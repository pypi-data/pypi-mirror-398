import time

from lmp_sdk.async_infer import AsyncInfer

class QueueMonitor:
    def __init__(self, infer: AsyncInfer, max_duration: int = 3600, check_interval: int = 30):
        self.infer_svc = infer.infer_service
        self.processor = infer.processor
        self.max_duration = max_duration
        self.check_interval = check_interval
        self.start_time = infer.start_time

    def monitor(self) -> str:
        try:
            while True:
                # 检查是否超时
                if time.time() - self.start_time >= self.max_duration:
                    print(f"已运行满{self.max_duration}秒，退出...")
                    return "timeout"

                queue_size = len(self.infer_svc.get_task_queue().tasks)
                if queue_size == 0:
                    print("队列为空，等待10分确认...")
                    time.sleep(600)
                    # 再次检查
                    if len(self.infer_svc.get_task_queue().queue) == 0:
                        print("队列确认为空，退出...")
                        return "empty"
                else:
                    elapsed = time.time() - self.start_time
                    remaining = self.max_duration - elapsed
                    print(f"队列还有 {queue_size} 个任务，已运行 {elapsed:.0f}秒，剩余 {remaining:.0f}秒...")
                    time.sleep(self.check_interval)
        finally:
            print(f"总运行时间: {time.time() - self.start_time:.1f}秒")

    def get_elapsed_time(self) -> float:
        """获取已运行时间（秒）"""
        if self.start_time:
            return time.time() - self.start_time
        return 0

    def get_queue_size(self) -> int:
        """获取当前队列大小"""
        return len(self.infer_svc.task_queue.queue)