import time
import logging
import threading
from typing import Optional, Callable, List
from lmp_sdk.task_queue import TaskQueue
from lmp_sdk.client import Client

from lmp_sdk.exceptions import APIError, TaskTimeoutError, TaskFailedError

logger = logging.getLogger(__name__)

from .models import (
    PostAsyncInferRequest,
    PostAsyncInferResponse,
    TaskResponse
)
from .constants import (
    DEFAULT_API_ENDPOINT,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_MAX_WAIT_TIME,
    DEFAULT_MAX_QUEUE_SIZE
)

class InferService:
    def __init__(
        self,
        apikey: str,
        endpoint: str = DEFAULT_API_ENDPOINT,
        worker_num: int = 100,
        polling_interval: int = DEFAULT_POLLING_INTERVAL,
        max_wait_time: int = DEFAULT_MAX_WAIT_TIME,
        max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
        timeout: int = 3600,
    ):
        self.polling_interval = polling_interval
        self.max_wait_time = max_wait_time

        self.task_queue = TaskQueue(
            max_queue_size=max_queue_size
        )

        self.client = Client(
            apikey=apikey,
            worker_num=worker_num,
            timeout=timeout,
            endpoint=endpoint,
        )

    def get_task_queue(self):
        return self.task_queue

    def post_async_infer(self, request: PostAsyncInferRequest) -> PostAsyncInferResponse:
        ret = self.client.post_async_infer(request)
        # 添加到任务队列
        if self.task_queue and ret.data:
            self.task_queue.add_task(ret.data.task_id)
            logger.info(f"Task {ret.data.task_id} added to queue")

        return ret


    def post_async_infer_batch(
                self,
                requests: List[PostAsyncInferRequest],
                max_workers: int = 10
        ) -> List[PostAsyncInferResponse]:

        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = [None] * len(requests)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.post_async_infer, req): i
                for i, req in enumerate(requests)
            }

            for future in as_completed(futures):
                id = futures[future]
                try:
                    result = future.result()
                    results[id] = result
                except Exception as e:
                    logger.error(f"Batch request failed: {e}")
                    results[id] = None

        return results

    def wait_for_task_completion(
            self,
            task_id: str,
            callback: Optional[Callable[[TaskResponse], None]] = None
    ) -> Optional[TaskResponse]:
        start_time = time.time()
        deadline = start_time + self.max_wait_time

        logger.info(f"Start polling task: {task_id}")
        logger.info(f"Polling interval: {self.polling_interval}s, Max wait: {self.max_wait_time}s")

        request_count = 0

        while True:
            # 检查超时
            if time.time() > deadline:
                raise TaskTimeoutError(f"Task timeout after {time.time() - start_time:.1f}s")

            request_count += 1
            current_time = time.strftime("%H:%M:%S")
            logger.info(f"[{current_time}] Request #{request_count}")

            try:
                result = self.client.get_task_status(task_id)

                # 检查错误码
                if result.errno != 0:
                    logger.info(f"Task processing: {result.msg}")
                    if result.data and result.data.estimated_scheduled_time > 0:
                        logger.info(f"Estimated wait: {result.data.estimated_scheduled_time}s")
                    time.sleep(self.polling_interval)
                    continue

                # 检查任务状态
                if result.data:
                    status = result.data.status
                    print(f'get_task_status, task_id is: {task_id}, resp status is: {status}')
                    if status == "RUNNING":
                        logger.info("Task running...")
                    elif status == "SUCCEEDED":
                        logger.info("Task succeeded!")
                        self._update_task_status(task_id, callback, result)
                        return result
                    elif status in ["FAILED", "UNKNOWN"]:
                        logger.error(f"Task failed: {result.data.failed_reason}")
                        self._update_task_status(task_id, callback, result)
                        raise TaskFailedError(f"Task failed: {result.data.failed_reason}")
                    elif status == "PENDING":
                        logger.info("Task pending...")
                    else:
                        logger.warning(f"Unknown status: {status}")

            except (APIError, TaskFailedError):
                raise
            except Exception as e:
                logger.error(f"Request failed: {e}")

            time.sleep(self.polling_interval)

    def _update_task_status(
            self,
            task_id: str,
            callback: Optional[Callable[[TaskResponse], None]],
            response: TaskResponse
    ):
        """更新任务状态"""
        # 从队列删除
        if self.task_queue:
            self.task_queue.remove_task(task_id)

        # 执行回调
        if callback:
            threading.Thread(target=callback, args=(response,), daemon=True).start()