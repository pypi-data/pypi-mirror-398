import threading
import time
import signal
import sys
import atexit
import logging

from lmp_sdk.infer_service import InferService
from lmp_sdk.models import  TaskResponse
from typing import Optional, Callable
from lmp_sdk.constants import DEFAULT_WORKER_NUM

logger = logging.getLogger(__name__)


class TaskProcessor:
    """任务处理器"""

    def __init__(
        self,
        infer_service: InferService,
        worker_num: int = DEFAULT_WORKER_NUM,
        callback: Optional[Callable[[TaskResponse], None]] = None,
    ):
        self.queue = infer_service.get_task_queue()
        self.service = infer_service
        self.worker_num = worker_num
        self.callback = callback
        self.stop_event = threading.Event()
        self.workers = []

        logger.info(f"TaskProcessor initialized with {worker_num} workers")

    def start(self):
        """启动处理器"""
        logger.info(f"Starting {self.worker_num} workers...")

        for i in range(self.worker_num):
            worker = threading.Thread(
                target=self._worker,
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info("All workers started")

        # 注册退出处理
        self._register_shutdown_handlers()

    def _worker(self, worker_id: int):
        """工作线程"""
        logger.info(f"Worker-{worker_id} started")

        while not self.stop_event.is_set():
            task = self.queue.get_next_task()

            if task is None:
                time.sleep(1)
                continue

            logger.info(f"Worker-{worker_id} processing task: {task.id}")

            try:
                self.service.wait_for_task_completion(
                    task.id,
                    self.callback
                )
            except Exception as e:
                logger.error(f"Worker-{worker_id} failed to process task {task.id}: {e}")

        logger.info(f"Worker-{worker_id} stopped")

    def _register_shutdown_handlers(self):
        self._shutdown_called = False
        """注册关闭处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            if not self._shutdown_called:
                self._shutdown_called = True
                self.shutdown_all()
            sys.exit(0)

        # 注册信号
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, signal_handler)

        # 注册退出处理
        def atexit_handler():
            if not self._shutdown_called:
                self._shutdown_called = True
                self.shutdown_all()
        atexit.register(atexit_handler)

    def shutdown_all(self,timeout: float = 30):
        """关闭队列"""
        logger.info("Shutting down Processor")

        try:
            self.processor_stop(timeout=timeout)
            self.service.client.close()
            self.queue.shutdown()
            logger.info("Task queue saved successfully")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")


    def processor_stop(self, timeout: float = 30):
        """停止处理器"""
        logger.info("Stopping TaskProcessor...")
        self.stop_event.set()

        for worker in self.workers:
            worker.join(timeout=timeout/len(self.workers))

        logger.info("TaskProcessor stopped")