import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from .models import (
    PostAsyncInferRequest,
    PostAsyncInferResponse,
    PostAsyncInferParams,
    Message,
    TaskResponse,
    CallbackConfig
)
from .constants import (
    DEFAULT_API_ENDPOINT,
    DEFAULT_MODEL,
    BASE_GET_URL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_RETRIES,
)
from .exceptions import APIError, TaskTimeoutError, TaskFailedError

logger = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        apikey: str,
    #    task_queue: TaskQueue,
        endpoint: str = DEFAULT_API_ENDPOINT,
        worker_num: int = 100,
        timeout: int = 3600,
        use_processer: bool = True
    ):
        self.endpoint = endpoint
        self.apikey = apikey



        # 创建 Session
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=worker_num,  # 每个主机的连接池连接数
            pool_maxsize=worker_num,
            max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]),
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "content-type": "application/json",
            "accept": "application/json",
            "Authorization": f"Bearer {apikey}"
        })
        self.timeout = timeout

        logger.info(f"Client initialized with endpoint: {endpoint}")

    def post_async_infer(self, request: PostAsyncInferRequest) -> PostAsyncInferResponse:
        # 设置默认值
        if not request.model:
            request.model = DEFAULT_MODEL
        if request.temperature == 0:
            request.temperature = DEFAULT_TEMPERATURE
        if request.lpai_max_request_retries == 0:
            request.lpai_max_request_retries = DEFAULT_MAX_RETRIES

        if request.messages:
            # 新格式：直接使用提供的messages（支持Message对象或字典格式）
            messages = request.messages
        elif request.contents:
            # 旧格式：使用contents和role构建单个message
            messages = [Message(role=request.role, content=request.contents)]
        else:
            raise ValueError("Either messages or contents must be provided")

        # 构建参数
        params = PostAsyncInferParams(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            frequency_penalty=request.frequency_penalty,
            stream=request.stream,
            lpai_max_request_retries=request.lpai_max_request_retries,
        )
        
        # 处理lpai_callback（支持字符串和CallbackConfig对象）
        if request.lpai_callback is not None:
            if isinstance(request.lpai_callback, str):
                if (request.lpai_callback.strip() and
                    (request.lpai_callback.startswith('https://') or
                     request.lpai_callback.startswith('kafka://') or
                     request.lpai_callback.startswith('id:'))):
                    params.lpai_callback = request.lpai_callback
            elif isinstance(request.lpai_callback, CallbackConfig):   
                params.lpai_callback = request.lpai_callback.to_dict()
        
        # 处理lpai_priority（只支持字符串：normal或high）
        if request.lpai_priority is not None:
            if request.lpai_priority in ["normal", "high"]:
                params.lpai_priority = request.lpai_priority
            else:
                raise ValueError(f"Invalid priority: {request.lpai_priority}. Must be 'normal' or 'high'")
        
        if request.max_tokens:
            params.max_tokens = request.max_tokens
        if request.top_p:
            params.top_p = request.top_p
        if request.presence_penalty:
            params.presence_penalty = request.presence_penalty

        return self.async_infer_send(params)

    def async_infer_send(self, params: PostAsyncInferParams) -> PostAsyncInferResponse:

        try:
            response = self.session.post(
                self.endpoint,
                json=params.to_dict(),
                timeout=self.timeout
            )

            if response.status_code != 200:
                raise APIError(response.status_code, response.text)

            result = PostAsyncInferResponse.from_dict(response.json())

            return result

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(0, str(e))

    def get_task_status(self, task_id: str) -> TaskResponse:

        url = f"{BASE_GET_URL}/async_infer/{task_id}"

        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                raise APIError(response.status_code, response.text)

            return TaskResponse.from_dict(response.json())

        except requests.RequestException as e:
            logger.error(f"Get task status failed: {e}")
            raise APIError(0, str(e))

    def close(self):
        """关闭客户端"""
        self.session.close()
        logger.info("Client closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()