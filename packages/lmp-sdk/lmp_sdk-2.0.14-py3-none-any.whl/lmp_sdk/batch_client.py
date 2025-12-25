import logging
import requests
from typing import Optional, List
from pathlib import Path

from .batch_models import (
    CreateBatchAsyncInferRequest,
    CreateBatchAsyncInferResponse,
    ListBatchAsyncInferRequest,
    ListBatchAsyncInferResponse,
    GetBatchAsyncInferDetailRequest,
    GetBatchAsyncInferDetailResponse,
    CancelBatchAsyncInferRequest,
    CancelBatchAsyncInferResponse,
    BatchStatus
)
from .asset_integration import AssetIntegration
from .exceptions import (
    APIError,
    BatchCreationError,
    BatchNotFoundError,
    DatasetPathError
)

logger = logging.getLogger(__name__)


class BatchClient:
    """
    批量推理客户端
    提供批量异步推理任务的创建、查询、取消和结果下载功能
    """
    
    def __init__(
        self,
        token: str,
        apikey: Optional[str] = None,
        base_url: Optional[str] = None,
        env: str = "prod",
        timeout: int = 60
    ):
        """
        初始化批量推理客户端
        
        Args:
            token: JWT认证token
            apikey: API密钥，用于批量推理任务（必需）
            base_url: API基础URL
            env: 环境标识，"prod"表示生产环境，"ontest"表示测试环境
            timeout: 请求超时时间（秒）
        """
        if apikey is None:
            raise ValueError("apikey is required for BatchClient")
        
        self.token = token
        self.apikey = apikey
        self.env = env
        self.timeout = timeout
        
        if base_url is None:
            if env == "ontest":
                self.base_url = "https://lpai-ontest.lixiang.com/lpai/api/lpai-service-lmp"
            else:  
                self.base_url = "https://lpai.lixiang.com/lpai/api/lpai-service-lmp"
        else:
            self.base_url = base_url.rstrip('/')
        
        # 初始化HTTP会话
        self.session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"LpaiJwt {token}"
        }
        
        # ontest环境需要添加额外的namespace请求头
        if env == "ontest":
            headers["x-lpai-namespace"] = "test-resource"
        
        self.session.headers.update(headers)
        
        # 初始化Asset集成模块
        try:
            self.asset = AssetIntegration(jwt_token=token, env=env)
            logger.info("Asset integration initialized successfully")
        except ImportError as e:
            logger.warning(f"Asset SDK not available: {e}")
            self.asset = None
        
        logger.info(f"BatchClient initialized with base_url: {base_url}")
    
    def create_batch(
        self,
        request: CreateBatchAsyncInferRequest,
        auto_upload: bool = False
    ) -> CreateBatchAsyncInferResponse:
        """
        创建批量异步推理任务
        
        Args:
            request: 创建请求对象
            auto_upload: 是否自动上传本地文件到数据集（默认False）
                        - False: 使用数据集路径，如 "test-readme/0.1.1/test.jsonl"
                        - True: 使用本地文件路径，SDK会自动上传，如 "./local/file.jsonl"
            
        Returns:
            CreateBatchAsyncInferResponse: 创建响应，包含batch_id
            
        Raises:
            BatchCreationError: 任务创建失败
            DatasetPathError: 数据集路径错误
        """
        try:
            if request.apikey is None:
                request.apikey = self.apikey
            
            logger.info(f"Original output_dataset: {request.output_dataset}")
            request.output_dataset = f"{request.output_dataset}/llm-batch"
            logger.info(f"Modified output_dataset: {request.output_dataset}")
                
            if auto_upload and self.asset:
                logger.info(f"Uploading local file: {request.dataset}")
                uploaded_path = self.asset.upload_local_file_to_request_dataset(request.dataset)
                request.dataset = uploaded_path
                logger.info(f"File uploaded to: {uploaded_path}")
            
            # 发送创建请求
            url = f"{self.base_url}/batch_async_infer"
            request_data = request.to_dict()
            logger.info(f"Creating batch task: {request.name}")
            logger.info(f"Request URL: {url}")
            logger.info(f"Request data: {request_data}")
            
            response = self.session.post(
                url,
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise APIError(response.status_code, response.text)
            
            result = CreateBatchAsyncInferResponse.from_dict(response.json())
            
            if result.errno != 0:
                raise BatchCreationError(f"Failed to create batch: {result.msg}")
            
            logger.info(f"Batch task created successfully, batch_id: {result.data}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(0, str(e))
        except Exception as e:
            logger.error(f"Failed to create batch: {e}")
            raise BatchCreationError(str(e))
    
    def list_batches(
        self,
        request: Optional[ListBatchAsyncInferRequest] = None
    ) -> ListBatchAsyncInferResponse:
        """
        获取批量推理任务列表
        
        Args:
            request: 列表查询请求（可选，默认查询第1页，每页10条）
            
        Returns:
            ListBatchAsyncInferResponse: 任务列表响应
        """
        if request is None:
            request = ListBatchAsyncInferRequest()
        
        try:
            url = f"{self.base_url}/batch_async_infer"
            params = request.to_params()
            
            logger.info(f"Fetching batch list with params: {params}")
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise APIError(response.status_code, response.text)
            
            result = ListBatchAsyncInferResponse.from_dict(response.json())
            logger.info(f"Fetched {len(result.data.items)} batch tasks")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(0, str(e))
    
    def get_batch_detail(
        self,
        batch_id: str
    ) -> GetBatchAsyncInferDetailResponse:
        """
        获取批量推理任务详情
        
        Args:
            batch_id: 批量任务ID
            
        Returns:
            GetBatchAsyncInferDetailResponse: 任务详情响应
            
        Raises:
            BatchNotFoundError: 任务不存在
        """
        try:
            url = f"{self.base_url}/batch_async_infer/{batch_id}"
            
            logger.info(f"Fetching batch detail: {batch_id}")
            
            response = self.session.get(
                url,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                raise BatchNotFoundError(f"Batch task not found: {batch_id}")
            
            if response.status_code != 200:
                raise APIError(response.status_code, response.text)
            
            result = GetBatchAsyncInferDetailResponse.from_dict(response.json())
            
            if result.errno != 0:
                if "not found" in result.msg.lower():
                    raise BatchNotFoundError(result.msg)
                raise APIError(result.errno, result.msg)
            
            logger.info(f"Batch detail fetched: {batch_id}, status: {result.data.status}")
            return result
            
        except BatchNotFoundError:
            raise
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(0, str(e))
    
    def cancel_batch(
        self,
        batch_id: str
    ) -> CancelBatchAsyncInferResponse:
        """
        取消批量推理任务
        
        Args:
            batch_id: 批量任务ID
            
        Returns:
            CancelBatchAsyncInferResponse: 取消响应
            
        Raises:
            BatchNotFoundError: 任务不存在
        """
        try:
            url = f"{self.base_url}/batch_async_infer/{batch_id}/cancel"
            
            logger.info(f"Cancelling batch task: {batch_id}")
            
            response = self.session.put(
                url,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                raise BatchNotFoundError(f"Batch task not found: {batch_id}")
            
            if response.status_code != 200:
                raise APIError(response.status_code, response.text)
            
            result = CancelBatchAsyncInferResponse.from_dict(response.json())
            
            if result.errno != 0:
                raise APIError(result.errno, result.msg)
            
            logger.info(f"Batch task cancelled: {batch_id}, status: {result.data.status}")
            return result
            
        except BatchNotFoundError:
            raise
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(0, str(e))
    
    def download_results(
        self,
        batch_id: str,
        local_dir: str,
        prefix: Optional[str] = None,
        parallelism: int = 10,
        full_path: bool = True,
        ignore_errors: bool = False
    ) -> None:
        """
        下载批量推理任务的结果文件
        
        Args:
            batch_id: 批量任务ID
            local_dir: 本地下载目录
            prefix: 文件前缀过滤（可选，用于下载特定子目录或文件）
            parallelism: 并发下载数（默认10）
            full_path: 是否保留完整路径结构（默认True）
            ignore_errors: 是否忽略错误继续下载（默认False）
            
        Raises:
            BatchNotFoundError: 任务不存在
            Exception: 下载失败或Asset SDK不可用
        """
        if self.asset is None:
            raise Exception(
                "Asset SDK not available. Cannot download results. "
                "Please install lpai_asset SDK."
            )
        
        # 获取任务详情
        detail_response = self.get_batch_detail(batch_id)
        detail = detail_response.data
        
        # 检查任务状态
        if detail.status not in [
            BatchStatus.COMPLETED.value,
            BatchStatus.EXPIRED.value,
            BatchStatus.CANCELLED.value
        ]:
            logger.warning(
                f"Batch task {batch_id} is not in final state (status: {detail.status}). "
                "Results may not be available yet."
            )
        
        # 获取输出文件夹路径
        output_folder_path = detail.output_file_path
        if not output_folder_path:
            raise ValueError(f"Batch task {batch_id} has no output_file_path")
        
        parts = output_folder_path.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid output_file_path format: {output_folder_path}")
        
        dataset_name = parts[0]  
        version = parts[1]  
        folder_prefix = "/".join(parts[2:]) if len(parts) > 2 else None  
        
        # 构建Asset SDK数据集路径
        dataset_path = f"datasets/{dataset_name}/versions/{version}"
        
        # 如果用户指定了prefix，与文件夹路径合并
        download_prefix = folder_prefix
        if prefix:
            download_prefix = f"{folder_prefix}/{prefix}" if folder_prefix else prefix
        
        logger.info(f"Downloading results from {dataset_path}")
        logger.info(f"Output folder: {output_folder_path}")
        if download_prefix:
            logger.info(f"Using prefix filter: {download_prefix}")
        
        # 下载文件
        try:
            self.asset.download_from_dataset(
                dataset_path=dataset_path,
                local_dir=local_dir,
                prefix=download_prefix,
                parallelism=parallelism,
                full_path=full_path,
                ignore_errors=ignore_errors
            )
            logger.info(f"Files downloaded successfully to {local_dir}")
                
        except Exception as e:
            logger.error(f"Failed to download results: {e}")
            raise
    
    def wait_for_completion(
        self,
        batch_id: str,
        poll_interval: int = 30,
        max_wait_time: int = 86400
    ) -> GetBatchAsyncInferDetailResponse:
        """
        等待批量任务完成
        
        Args:
            batch_id: 批量任务ID
            poll_interval: 轮询间隔（秒），默认30秒
            max_wait_time: 最大等待时间（秒），默认24小时
            
        Returns:
            GetBatchAsyncInferDetailResponse: 最终任务详情
            
        Raises:
            TimeoutError: 超过最大等待时间
        """
        import time
        
        start_time = time.time()
        deadline = start_time + max_wait_time
        
        logger.info(f"Waiting for batch {batch_id} to complete...")
        
        while True:
            if time.time() > deadline:
                raise TimeoutError(
                    f"Batch task {batch_id} did not complete within {max_wait_time} seconds"
                )
            
            detail_response = self.get_batch_detail(batch_id)
            detail = detail_response.data
            
            logger.info(
                f"Batch {batch_id}: status={detail.status}, "
                f"progress={detail.progress:.1%}, "
                f"finished={detail.finished_request_num}/{detail.request_num}"
            )
            
            # 检查是否到达最终状态
            if detail.status in [
                BatchStatus.COMPLETED.value,
                BatchStatus.FAILED.value,
                BatchStatus.EXPIRED.value,
                BatchStatus.CANCELLED.value
            ]:
                logger.info(f"Batch {batch_id} reached final state: {detail.status}")
                return detail_response
            
            time.sleep(poll_interval)
    
    def close(self):
        """关闭客户端"""
        self.session.close()
        logger.info("BatchClient closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()