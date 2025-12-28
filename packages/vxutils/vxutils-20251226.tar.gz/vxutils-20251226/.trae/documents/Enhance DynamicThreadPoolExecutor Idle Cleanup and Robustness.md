## Objectives

* Make idle-thread cleanup safer, configurable, and observable without relying on private internals more than necessary.

* Avoid removing threads that are currently executing tasks; only reap truly idle workers.

* Provide consistent logging and configurability (e.g., minimum workers to keep).

## Implementation Changes

1. Idle Detection Accuracy

* Add `_thread_active: Dict[int, bool]` and flip per-task using a `try/finally` in `submit`'s wrapper (`e:\src\vxutils\src\vxutils\executor.py:165`).

* Only mark threads for removal when `not _thread_active[tid]` and `now - _thread_last_active[tid] > idle_timeout` (`e:\src\vxutils\src\vxutils\executor.py:93–99`).

1. Configurable Floor

* Add `min_workers: int = 1` to `__init__` and ensure `max_to_remove = max(0, active_threads - min_workers)` (`e:\src\vxutils\src\vxutils\executor.py:29–37`, `110–114`).

1. Atomic Queue Swap

* Reorder cleanup:

  * Acquire `_shutdown_lock`, snapshot `old_queue = self._work_queue` and `old_threads = self._threads.copy()`.

  * Set `self._work_queue = queue.SimpleQueue()` immediately.

  * Drain `old_queue` non-None items and put into new queue.

  * Remove selected threads from `self._threads` and send `None` to `old_queue`.

* This reduces races while draining and swapping (`e:\src\vxutils\src\vxutils\executor.py:120–157`).

1. Logging

* Replace `print` with project logger: `vxutils.logger.get_logger()` (existing format includes `%(threadName)s`).

* Log cleanup decisions at `DEBUG` (counts, ids) and summary at `INFO` (`e:\src\vxutils\src\vxutils\executor.py:118`).

1. Guardrails

* Validate `idle_timeout > 0` and `check_interval > 0`; if disabled (`None`), skip monitor thread (`e:\src\vxutils\src\vxutils\executor.py:46–49`).

* Ensure `shutdown` joins cleanup thread and clears maps safely (already present) (`e:\src\vxutils\src\vxutils\executor.py:195–212`).

## Tests

* Extend `tests/test_executor.py`:

  * `test_long_running_task_not_killed`: submit a long task, set `idle_timeout` < run time, assert thread exits only after completion.

  * `test_min_workers_floor`: with `min_workers=2`, ensure cleanup doesn’t reduce below 2 after idle period.

  * `test_queue_swap_preserves_work`: enqueue many tasks, force cleanup, verify all results returned.

  * `test_logging`: capture logs, assert cleanup messages emitted at expected levels.

* Keep existing tests; they currently pass for executor-specific suite.

## Usage Notes

* Instantiate with `min_workers` to maintain baseline capacity:

  * `DynamicThreadPoolExecutor(max_workers=4, idle_timeout=10, min_workers=1, thread_name_prefix="dyn-")`.

* Threads reaped are those idle past `idle_timeout`; busy threads finish work and then exit if marked.

## Validation & Rollout

* Run `pytest -q tests/test_executor.py` and new tests; verify behavior under load.

* Observe logs to confirm cleanup cadence and counts.

* Incrementally adopt in places using `ThreadPoolExecutor` where idle cleanup is beneficial.

