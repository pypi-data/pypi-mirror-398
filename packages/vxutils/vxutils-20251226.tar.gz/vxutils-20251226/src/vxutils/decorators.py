import logging
import functools
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from threading import Lock
from typing import Callable, Type, Tuple, Union, Any, Deque

__all__ = [
    "retry",
    "timer",
    "log_exception",
    "singleton",
    "timeout",
    "rate_limit",
]


def retry(
    max_retries: int = 3,
    delay: Union[int, float] = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Any], Any]:
    """
    错误重试装饰器
    :param max_retries: 最大重试次数（包含首次调用）
    :param delay: 重试间隔时间（秒）
    :param exceptions: 需要捕获的异常类型
    """

    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2**attempt))
            raise last_exception

        return wrapper

    return decorator


class timer:
    """计时器"""

    def __init__(self, descriptions: str = "", *, verbose: bool = False) -> None:
        self._descriptions = descriptions
        self._start_time = 0.0
        self._end_time = 0.0
        self._verbose = verbose

    @property
    def cost(self) -> float:
        return (
            (time.perf_counter() if self._end_time == 0 else self._end_time)
            - self._start_time
        ) * 1000

    def __enter__(self) -> "timer":
        if self._verbose:
            logging.info(f"{self._descriptions} start...")
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self._end_time = time.perf_counter()

        if self._verbose:
            logging.warning(f"{self._descriptions} used : {self.cost:.2f}ms")

    def __call__(self, func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper


###################################
# log_exception 实现
# @log_exception
###################################


def log_exception(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """
    异常捕获装饰器
    :param logger: 日志对象
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(
                f"Exception in {func.__name__}: {e}", exc_info=True, stack_info=True
            )
            raise e

    return wrapper


###################################
# Singleton 实现
# @singleton
###################################


class singleton(object):
    """
    单例
    example::

        @singleton
        class YourClass(object):
            def __init__(self, *args, **kwargs):
                pass
    """

    def __init__(self, cls: Type[Any]) -> None:
        self._instance = None
        self._cls = cls
        self._lock = Lock()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = self._cls(*args, **kwargs)
        return self._instance


###################################
# 限制超时时间
# @timeout(seconds, error_message='Function call timed out')
###################################


class timeout:
    def __init__(
        self, seconds: float = 1, *, timeout_msg: str = "Function %s call time out."
    ) -> None:
        self._timeout = seconds
        self._timeout_msg = timeout_msg

    def __call__(self, func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            executor = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix=f"timeout-{func.__name__}"
            )
            future = executor.submit(func, *args, **kwargs)
            try:
                result = future.result(timeout=self._timeout)
                executor.shutdown(wait=True, cancel_futures=True)
                return result
            except FutureTimeoutError:
                executor.shutdown(wait=False, cancel_futures=True)
                raise TimeoutError(
                    f"{self._timeout_msg} after {self._timeout * 1000}ms"
                )

        return wrapper


################################################
################################################
#  @rate_limit(times:int, period:float)
#  用于限制某个应用调用次数的修饰器
################################################


def rate_limit(times: int, period: float) -> Any:
    lock = Lock()
    calls: Deque[float] = deque([0] * times, maxlen=times)

    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            while True:
                now = time.monotonic()
                with lock:
                    if calls[0] + period <= now:
                        calls.append(now)
                        break
                    sleep_for = period - (now - calls[0])
                time.sleep(sleep_for)
            return func(*args, **kwargs)

        return wrapper

    return decorator
