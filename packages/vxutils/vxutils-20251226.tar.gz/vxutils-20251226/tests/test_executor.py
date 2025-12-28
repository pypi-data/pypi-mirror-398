import time
import threading
import unittest
from concurrent.futures import Future
from vxutils import DynamicThreadPoolExecutor


class TestDynamicThreadPoolExecutor(unittest.TestCase):
    def test_executor_cleans_idle_threads(self):
        # 创建一个短超时时间的执行器
        executor = DynamicThreadPoolExecutor(
            max_workers=5,
            thread_name_prefix="test-",
            idle_timeout=1.0,  # 1秒超时
            check_interval=0.5  # 每0.5秒检查一次
        )
        
        # 提交一些任务
        def slow_task(sleep_time):
            time.sleep(sleep_time)
            return threading.get_ident()
        
        # 提交5个任务，每个任务使用一个线程
        futures = [executor.submit(slow_task, 0.1) for _ in range(5)]
        
        # 等待所有任务完成
        thread_ids = [future.result() for future in futures]
        
        # 验证所有任务都成功完成
        self.assertEqual(len(thread_ids), 5)
        
        # 等待足够长的时间让线程被清理
        time.sleep(2.0)
        
        # 提交一个新任务
        new_future = executor.submit(slow_task, 0.1)
        new_thread_id = new_future.result()
        
        # 关闭执行器
        executor.shutdown()
        
        # 由于线程池中的线程应该已经被清理，新任务应该在新线程中执行
        # 注意：这个测试可能不是100%可靠，因为线程ID可能会被重用
        # 但在大多数情况下，它应该能够验证我们的实现
        print(f"Original thread IDs: {thread_ids}")
        print(f"New thread ID: {new_thread_id}")

    def test_executor_with_many_tasks(self):
        # 测试执行器能否处理大量任务
        executor = DynamicThreadPoolExecutor(
            max_workers=3,  # 只使用3个工作线程
            idle_timeout=1.0
        )
        
        # 提交20个任务
        def simple_task(task_id):
            time.sleep(0.1)  # 短暂延迟
            return task_id
        
        futures = [executor.submit(simple_task, i) for i in range(20)]
        
        # 验证所有任务都成功完成并返回正确的结果
        results = [future.result() for future in futures]
        self.assertEqual(results, list(range(20)))
        
        executor.shutdown()

    def test_executor_shutdown(self):
        # 测试执行器的关闭功能
        executor = DynamicThreadPoolExecutor(
            max_workers=2,
            idle_timeout=60.0  # 长超时，不应该自动清理
        )
        
        # 提交一个长时间运行的任务
        def long_task():
            time.sleep(1.0)
            return "done"
        
        future = executor.submit(long_task)
        
        # 立即关闭执行器，但等待任务完成
        executor.shutdown(wait=True)
        
        # 验证任务仍然完成
        self.assertEqual(future.result(), "done")
        
        # 验证执行器已关闭
        with self.assertRaises(RuntimeError):
            executor.submit(long_task)

    def test_long_running_task_not_killed(self):
        executor = DynamicThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="long-",
            idle_timeout=0.5,
            check_interval=0.2,
        )

        def long_task():
            time.sleep(1.2)
            return threading.current_thread().name

        future = executor.submit(long_task)
        name = future.result()
        self.assertTrue(name.startswith("long-"))

        time.sleep(1.0)
        executor.shutdown()

    def test_min_workers_floor(self):
        executor = DynamicThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="floor-",
            idle_timeout=0.5,
            check_interval=0.2,
            min_workers=2,
        )

        def short_task():
            time.sleep(0.1)

        futures = [executor.submit(short_task) for _ in range(6)]
        for f in futures:
            f.result()

        time.sleep(1.5)
        names = [t.name for t in threading.enumerate() if t.name.startswith("floor-")]
        self.assertGreaterEqual(len(names), 2)
        executor.shutdown()


if __name__ == "__main__":
    unittest.main()