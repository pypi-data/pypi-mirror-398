import os
import concurrent.futures
import threading
import queue
import weakref
from typing import Any, Callable, Dict, Optional, Tuple

__all__ = ["VXThreadPoolExecutor", "DynamicThreadPoolExecutor"]


class VXThreadPoolExecutor(concurrent.futures._base.Executor):
    """
    - 一种改进的 ThreadPoolExecutor，可自动清理空闲线程。
    - 该类在标准 ThreadPoolExecutor 的基础上扩展，加入机制，在指定时间后自动终止空闲线程。
    - 标准的 ThreadPoolExecutor 会在执行器关闭之前一直保持线程存活，可能浪费资源。本实现增加机制，自动清理在指定时间内处于空闲状态的线程。

    参数
    - max_workers ：使用的最大线程数。
    - thread_name_prefix ：该线程池中线程名称的前缀。
    - idle_timeout ：空闲线程在多少秒后将被终止。设为 None 可禁用自动清理（与 ThreadPoolExecutor 的默认行为一致）。"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        thread_name_prefix: str = "",
        initializer: Optional[Callable[..., None]] = None,
        initargs: Tuple[Any, ...] = (),
        *,
        idle_timeout: Optional[float] = 500.0,
        check_interval: float = 1.0,
        min_workers: int = 1,
    ):
        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) + 4)
        if max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")

        if initializer is not None and not callable(initializer):
            raise TypeError("initializer must be a callable")

        self._max_workers = max_workers
        self._work_queue = queue.Queue()
        self._threads = set[threading.Thread]()
        self._stop_event = threading.Event()
        self._thread_name_prefix = thread_name_prefix or (
            "VXWorkerThread%d" % self._counter()
        )
        self._initializer = initializer
        self._initargs = initargs

        self._idle_timeout = idle_timeout
        self._check_interval = float(check_interval)
        self._min_workers = max(1, int(min_workers))
        self._lock = threading.RLock()

        # 预启动最小保留线程数
        with self._lock:
            for _ in range(self._min_workers):
                self._start_worker()

    def _dynamic_worker(self) -> None:
        """
        Worker thread used by VXThreadPoolExecutor.
        """
        if self._initializer is not None:
            try:
                self._initializer(*self._initargs)
            except BaseException:
                concurrent.futures._base.LOGGER.critical(
                    "Exception in initializer:", exc_info=True
                )
                self._initializer_failed()
                return

        try:
            current = threading.current_thread()
            while not self._stop_event.is_set():
                try:
                    work_item = self._work_queue.get(timeout=self._idle_timeout)
                except queue.Empty:
                    with self._lock:
                        if len(self._threads) <= self._min_workers:
                            continue
                        else:
                            break
                if work_item is None:
                    break
                work_item.run()
                del work_item

        except BaseException:
            concurrent.futures._base.LOGGER.critical(
                "Exception in worker", exc_info=True
            )
        finally:
            with self._lock:
                self._threads.discard(current)

    def _adjust_thread_count(self) -> None:
        """
        Adjust the number of threads in the pool based on the number of pending tasks.

        This method is called internally by the executor to adjust the number of threads
        in the pool based on the number of pending tasks. If the number of pending tasks
        exceeds the number of threads, new threads will be created. If the number of pending
        tasks is less than the number of threads, idle threads will be terminated.
        """

        # When the executor gets lost, the weakref callback will wake up
        # the worker threads.
        def weakref_cb(_, q=self._work_queue):
            q.put(None)

        pending = self._work_queue.qsize()
        with self._lock:
            num_threads = len(self._threads)
            if (pending > num_threads) and (num_threads < self._max_workers):
                self._start_worker()

        weakref.ref(self, weakref_cb)

    def _start_worker(self) -> None:
        num_threads = len(self._threads)
        thread_name = "%s_%d" % (self._thread_name_prefix or self, num_threads)
        t = threading.Thread(
            name=thread_name,
            target=self._dynamic_worker,
            daemon=True,
        )
        t.start()
        self._threads.add(t)

    def submit(
        self, fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> concurrent.futures.Future:
        if self._stop_event.is_set():
            raise RuntimeError("cannot schedule new futures after shutdown")
        f: concurrent.futures.Future = concurrent.futures.Future()

        class _WorkItem:
            def __init__(
                self,
                future: concurrent.futures.Future,
                fn: Callable[..., Any],
                args: Tuple[Any, ...],
                kwargs: Dict[str, Any],
            ):
                self.future = future
                self.fn = fn
                self.args = args
                self.kwargs = kwargs

            def run(self) -> None:
                if not self.future.set_running_or_notify_cancel():
                    return
                try:
                    result = self.fn(*self.args, **self.kwargs)
                    self.future.set_result(result)
                except BaseException as exc:
                    self.future.set_exception(exc)

        wi = _WorkItem(f, fn, args, kwargs)
        self._work_queue.put(wi)
        self._adjust_thread_count()
        return f

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        self._stop_event.set()
        if cancel_futures:
            try:
                while True:
                    item = self._work_queue.get_nowait()
                    if hasattr(item, "future"):
                        item.future.cancel()
            except queue.Empty:
                pass

        with self._lock:
            threads = list(self._threads)

        for _ in threads:
            self._work_queue.put(None)
        if wait:
            for t in threads:
                t.join()
        with self._lock:
            self._threads.clear()

    @classmethod
    def _counter(cls) -> int:
        if not hasattr(cls, "__counter_lock__"):
            cls.__counter_lock__ = threading.Lock()
            cls.__counter__ = 0
        with cls.__counter_lock__:
            v = cls.__counter__
            cls.__counter__ += 1
            return v

# 兼容别名
DynamicThreadPoolExecutor = VXThreadPoolExecutor
