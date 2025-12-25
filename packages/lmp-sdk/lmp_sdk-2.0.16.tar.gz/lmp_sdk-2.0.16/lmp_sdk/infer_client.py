import time
from typing import List
import logging
from lmp_sdk.client import Client
from lmp_sdk.models import (
    PostAsyncInferRequest,
    PostAsyncInferResponse,
    GetAsyncInferRequest,
    TaskResponse,
)
from lmp_sdk.constants import (
    DEFAULT_API_ENDPOINT,
)

logger = logging.getLogger(__name__)

class InferClient:
    def __init__(
            self,
            apikey: str,
            endpoint: str = DEFAULT_API_ENDPOINT,
            worker_num: int = 100,
            timeout: int = 3600,
    ):

        self.start_time = time.time()
        self.client = Client(
            apikey=apikey,
            worker_num=worker_num,
            timeout=timeout,
            endpoint=endpoint,
        )
    def get_async_infer_res(self, request: GetAsyncInferRequest) -> TaskResponse:
        if not request.task_id:
            return TaskResponse(
                msg="task_id is required parameter",
                errno=-1,
                data=None,
            )

        return self.client.get_task_status(request.task_id)

    def post_async_infer(self, request: PostAsyncInferRequest) -> PostAsyncInferResponse:
        return self.client.post_async_infer(request)

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