import logging
from pathlib import Path
from typing import Optional, List, Set
import os

logger = logging.getLogger(__name__)

try:
    import asset
    ASSET_SDK_AVAILABLE = True
except ImportError:
    ASSET_SDK_AVAILABLE = False
    logger.warning("lpai_asset SDK not installed. Asset operations will not be available.")


class AssetIntegration:
    """
    Asset SDK集成模块
    用于处理文件上传到LPAI数据集和从数据集下载文件
    """
    
    # 固定的数据集配置
    BATCH_REQUEST_DATASET = "datasets/lmp-request/versions/0.1.1"
    
    def __init__(self, jwt_token: str, env: str = "prod", user_name: Optional[str] = None):
        """
        初始化Asset集成模块
        
        Args:
            jwt_token: JWT认证token
            env: 运行环境，"prod"(生产)或"ontest"(测试)
            user_name: 用户名，用于构建上传路径（可选，默认从token解析或使用timestamp）
        """
        if not ASSET_SDK_AVAILABLE:
            raise ImportError(
                "lpai_asset SDK is required for batch inference. "
                "Please install it using: pip install lpai_asset"
            )
        
        self.jwt_token = jwt_token
        self.env = env
        self.user_name = user_name or self._extract_user_from_token(jwt_token)
        self.config = asset.config(env=env, jwt_token=jwt_token)
        logger.info(f"AssetIntegration initialized with env: {env}, user: {self.user_name}")
    
    def _extract_user_from_token(self, token: str) -> str:
        """
        从JWT token中提取用户名，并添加时间戳
        格式: {username}_{timestamp} 或 user_{timestamp}（解析失败时）
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            import base64
            import json
            
            # JWT token格式: header.payload.signature
            parts = token.split('.')
            if len(parts) >= 2:
                # 解码payload（可能需要补齐padding）
                payload = parts[1]
                # 添加必要的padding
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                
                decoded = base64.urlsafe_b64decode(payload)
                payload_data = json.loads(decoded)
                
                # 尝试获取用户标识（常见字段：sub, email, username, user_id）
                user = (payload_data.get('sub') or
                       payload_data.get('email') or
                       payload_data.get('username') or
                       payload_data.get('user_id'))
                
                if user:
                    # 在用户名后添加时间戳
                    return f"{user}_{timestamp}"
                
        except Exception as e:
            logger.warning(f"Failed to extract user from token: {e}")
        
        # 如果解析失败，使用默认用户名加时间戳
        return f"user_{timestamp}"
    
    def upload_local_file_to_request_dataset(
        self,
        local_file_path: str,
        target_filename: Optional[str] = None,
        overwrite: bool = False
    ) -> str:
        """
        上传本地文件到 lmp-request 数据集 0.1.1 版本
        文件会上传到用户名和时间戳命名的子目录下
        
        Args:
            local_file_path: 本地文件路径
            target_filename: 目标文件名（可选，默认使用原文件名）
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            str: 上传后的数据集路径
                格式: lmp-request/0.1.1/{username}_{timestamp}/{filename}
                示例: lmp-request/0.1.1/john_1702188000/data.jsonl
            
        Raises:
            FileNotFoundError: 本地文件不存在
            Exception: 上传失败
        """
        # 检查本地文件是否存在
        local_path = Path(local_file_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_file_path}")
        
        if not local_path.is_file():
            raise ValueError(f"Path is not a file: {local_file_path}")
        
        # 确定目标文件名
        if target_filename is None:
            target_filename = local_path.name
        
        # 构建目标路径：datasets/lmp-request/versions/0.1.1/{user_name_timestamp}/{filename}
        target_subdir = self.user_name  # 已经包含用户名和时间戳
        target_path_in_dataset = f"{target_subdir}/{target_filename}"
        
        logger.info(f"Uploading {local_file_path} to {self.BATCH_REQUEST_DATASET}/{target_path_in_dataset}")
        
        try:
            # 获取资源对象
            resource = asset.resource(self.BATCH_REQUEST_DATASET, config=self.config)
            
            resource.upload(
                paths={str(local_path.absolute())},
                prefix=target_subdir  
            )
        
            # 返回完整的数据集路径
            result_path = f"lmp-request/0.1.1/{target_path_in_dataset}"
            logger.info(f"File uploaded successfully to: {result_path}")
            return result_path
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise Exception(f"Asset upload failed: {str(e)}")
    
    def download_from_dataset(
        self,
        dataset_path: str,
        local_dir: str,
        prefix: Optional[str] = None,
        parallelism: int = 10,
        full_path: bool = True,
        ignore_errors: bool = False
    ) -> None:
        """
        从数据集下载文件到本地目录
        
        Args:
            dataset_path: 数据集路径，如 "datasets/output-data/versions/v1"
            local_dir: 本地目标目录
            prefix: 文件前缀过滤（可选，用于下载特定子目录或文件）
            parallelism: 并发下载数（默认10）
            full_path: 是否保留完整路径结构（默认True）
            ignore_errors: 是否忽略错误继续下载（默认False）
            
        Raises:
            Exception: 下载失败
        """
        logger.info(f"Downloading from {dataset_path} to {local_dir}")
        if prefix:
            logger.info(f"Using prefix filter: {prefix}")
        
        try:
            # 确保本地目录存在
            Path(local_dir).mkdir(parents=True, exist_ok=True)
            
            # 获取资源对象
            resource = asset.resource(dataset_path, config=self.config)
            
            # 下载文件 - 使用Asset SDK的正确参数
            resource.download(
                local_dir=local_dir,
                prefix=prefix,
                parallelism=parallelism,
                full_path=full_path,
                ignore_errors=ignore_errors
            )
            
            logger.info(f"Files downloaded successfully to: {local_dir}")
            
        except Exception as e:
            logger.error(f"Failed to download files: {e}")
            raise Exception(f"Asset download failed: {str(e)}")
    
    def list_files_in_dataset(
        self,
        dataset_path: str,
        prefix: Optional[str] = None,
        max_keys: int = 100
    ) -> List[str]:
        """
        列出数据集中的文件
        
        Args:
            dataset_path: 数据集路径
            prefix: 文件前缀过滤（可选）
            max_keys: 最大返回数量
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            resource = asset.resource(dataset_path, config=self.config)
            files = resource.list_file(prefix=prefix, max_keys=max_keys)
            return [f.get('key', '') for f in files]
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def check_dataset_exists(self, dataset_path: str) -> bool:
        """
        检查数据集是否存在
        
        Args:
            dataset_path: 数据集路径
            
        Returns:
            bool: 数据集是否存在
        """
        try:
            resource = asset.resource(dataset_path, config=self.config)
            details = resource.get(force_refresh=False)
            return details is not None
        except Exception as e:
            logger.warning(f"Dataset check failed: {e}")
            return False
    
    @staticmethod
    def parse_dataset_path(path: str) -> dict:
        """
        解析数据集路径类型
        
        Args:
            path: 路径字符串
            
        Returns:
            dict: 包含类型和路径信息的字典
        """
        if path.startswith('/'):
            return {'type': 'local', 'path': path}
        elif path.startswith('datasets/'):
            return {'type': 'dataset', 'path': path}
        else:
            # 默认认为是数据集路径
            return {'type': 'dataset', 'path': path}
    
    def prepare_batch_input(
        self,
        input_path: str,
        target_filename: Optional[str] = None
    ) -> str:
        """
        准备批量推理的输入文件
        - 如果是本地文件，上传到 lmp-request 数据集
        - 如果已经是数据集路径，直接返回
        
        Args:
            input_path: 输入文件路径（本地或数据集）
            target_filename: 上传后的目标文件名（仅对本地文件有效）
            
        Returns:
            str: 数据集路径
        """
        path_info = self.parse_dataset_path(input_path)
        
        if path_info['type'] == 'local':
            # 本地文件，需要上传
            logger.info(f"Local file detected, uploading to {self.BATCH_REQUEST_DATASET}")
            return self.upload_local_file_to_request_dataset(
                input_path,
                target_filename=target_filename
            )
        elif path_info['type'] == 'dataset':
            # 已经是数据集路径，需要转换格式
            # 从 "datasets/{name}/versions/{version}/path/to/file.jsonl"
            # 转换为 "{name}/{version}/path/to/file.jsonl"
            logger.info(f"Dataset path detected: {input_path}")
            
            # 移除 "datasets/" 和 "versions/" 前缀
            normalized_path = input_path
            if normalized_path.startswith('datasets/'):
                normalized_path = normalized_path[9:]  # 移除 "datasets/"
            
            # 将 "/versions/" 替换为 "/"
            normalized_path = normalized_path.replace('/versions/', '/')
            
            logger.info(f"Normalized dataset path: {normalized_path}")
            return normalized_path
        else:
            # 其他类型（PVC、Task等）暂不处理，直接返回
            logger.warning(f"Unsupported path type: {path_info['type']}, returning as-is")
            return input_path