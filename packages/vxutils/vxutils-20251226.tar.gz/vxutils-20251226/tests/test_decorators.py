import unittest
import time
import threading
from typing import List
from vxutils.decorators import retry, timer, log_exception, singleton, timeout, rate_limit


class TestRetry(unittest.TestCase):
    def test_retry_exponential_backoff(self):
        attempts = {
            "count": 0
        }

        @retry(max_retries=3, delay=0.01)
        def fn():
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise ValueError("fail")
            return "ok"

        self.assertEqual(fn(), "ok")
        self.assertEqual(attempts["count"], 3)


class TestTimeout(unittest.TestCase):
    def test_timeout_raises(self):
        @timeout(seconds=0.05)
        def slow():
            time.sleep(0.2)

        with self.assertRaises(TimeoutError):
            slow()


class TestSingleton(unittest.TestCase):
    def test_singleton_thread_safe(self):
        @singleton
        class Obj:
            def __init__(self):
                time.sleep(0.01)

        results: List[int] = []

        def worker():
            o = Obj()
            results.append(id(o))

        threads = [threading.Thread(target=worker) for _ in range(10)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(len(set(results)), 1)


class TestTimer(unittest.TestCase):
    def test_timer_context(self):
        with timer("work", verbose=False) as tm:
            time.sleep(0.02)
        self.assertGreaterEqual(tm.cost, 20)


class TestLogException(unittest.TestCase):
    def test_log_exception_reraises(self):
        @log_exception
        def boom():
            raise RuntimeError("x")

        with self.assertRaises(RuntimeError):
            boom()


class TestRateLimit(unittest.TestCase):
    def test_rate_limit_throttles(self):
        calls = {"count": 0}

        @rate_limit(times=2, period=0.2)
        def fn():
            calls["count"] += 1
            return calls["count"]

        start = time.monotonic()
        [fn() for _ in range(5)]
        elapsed = time.monotonic() - start
        self.assertGreaterEqual(elapsed, 0.35)
        self.assertEqual(calls["count"], 5)


if __name__ == "__main__":
    unittest.main()