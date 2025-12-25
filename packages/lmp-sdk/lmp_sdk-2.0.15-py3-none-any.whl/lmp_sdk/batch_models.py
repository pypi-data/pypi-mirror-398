from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class BatchStatus(Enum):
    """批量任务状态枚举"""
    VALIDATING = "validating"      # 校验中
    FAILED = "failed"              # 失败
    IN_PROGRESS = "in_progress"    # 处理中
    FINALIZING = "finalizing"      # 完成中
    COMPLETED = "completed"        # 已完成
    EXPIRED = "expired"            # 过期
    CANCELLING = "cancelling"      # 取消中
    CANCELLED = "cancelled"        # 已取消


@dataclass
class CreateBatchAsyncInferRequest:
    """创建批量异步推理任务请求"""
    model_service: str              # 模型服务名称
    dataset: str                    # 输入数据集路径
    output_dataset: str             # 输出数据集路径
    name: str                       # 任务名称
    apikey: Optional[str] = None    # API密钥（可选，如果不提供则使用BatchClient的apikey）
    max_waiting_days: int = 1       # 最大等待天数（1-7天，对应1-168小时）
    description: str = ""           # 任务描述

    def to_dict(self) -> Dict[str, Any]:
        """转换为API请求字典，将天数转换为小时"""
        result = {
            "model_service": self.model_service,
            "dataset": self.dataset,
            "output_dataset": self.output_dataset,
            "name": self.name,
            "max_waiting_hour": self.max_waiting_days * 24,  # 天数转换为小时
            "description": self.description
        }
        # 只有当apikey不为None时才添加到字典中
        if self.apikey is not None:
            result["apikey"] = self.apikey
        return result


@dataclass
class CreateBatchAsyncInferResponse:
    """创建批量异步推理任务响应"""
    errno: int
    msg: str
    data: str  # batch_id

    @classmethod
    def from_dict(cls, data: Dict) -> 'CreateBatchAsyncInferResponse':
        return cls(
            errno=data.get("errno", 0),
            msg=data.get("msg", ""),
            data=data.get("data", "")
        )


@dataclass
class ListBatchAsyncInferRequest:
    """获取批量推理列表请求"""
    page_num: int = 1               # 页码（最小1）
    page_size: int = 10             # 每页大小（1-200）
    status: Optional[str] = None    # 按状态过滤
    model_service: Optional[str] = None  # 按模型服务过滤
    user_email: Optional[str] = None     # 按用户邮箱过滤
    order_by_created_at: int = 0    # 排序：1=升序，-1=降序，0=默认降序
    name: Optional[str] = None      # 按名称过滤

    def to_params(self) -> Dict[str, Any]:
        """转换为URL参数"""
        params = {
            "page_num": self.page_num,
            "page_size": self.page_size,
        }
        if self.status:
            params["status"] = self.status
        if self.model_service:
            params["model_service"] = self.model_service
        if self.user_email:
            params["user_email"] = self.user_email
        if self.order_by_created_at != 0:
            params["order_by_created_at"] = self.order_by_created_at
        if self.name:
            params["name"] = self.name
        return params


@dataclass
class BatchAsyncInferItem:
    """批量推理任务列表项"""
    batch_id: str
    name: str
    status: str
    req_nums: int
    finished_req_nums: int
    created_at: str
    description: str = ""
    input_jsonl: str = ""
    output_jsonl: str = ""
    finished_at: str = ""
    err_msg: str = ""
    expire_at: str = ""

    @classmethod
    def from_dict(cls, data: Dict) -> 'BatchAsyncInferItem':
        return cls(
            batch_id=data.get("batch_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            input_jsonl=data.get("input_jsonl", ""),
            output_jsonl=data.get("output_jsonl", ""),
            status=data.get("status", ""),
            created_at=data.get("created_at", ""),
            finished_at=data.get("finished_at", ""),
            finished_req_nums=data.get("finished_req_nums", 0),
            req_nums=data.get("req_nums", 0),
            err_msg=data.get("err_msg", ""),
            expire_at=data.get("expire_at", "")
        )


@dataclass
class ListBatchAsyncInferPayload:
    """批量推理列表响应数据"""
    items: List[BatchAsyncInferItem]
    total: int
    page_num: int
    page_size: int

    @classmethod
    def from_dict(cls, data: Dict) -> 'ListBatchAsyncInferPayload':
        items = [BatchAsyncInferItem.from_dict(item) for item in data.get("items", [])]
        return cls(
            items=items,
            total=data.get("total", 0),
            page_num=data.get("page_num", 1),
            page_size=data.get("page_size", 10)
        )


@dataclass
class ListBatchAsyncInferResponse:
    """获取批量推理列表响应"""
    errno: int
    msg: str
    data: ListBatchAsyncInferPayload

    @classmethod
    def from_dict(cls, data: Dict) -> 'ListBatchAsyncInferResponse':
        return cls(
            errno=data.get("errno", 0),
            msg=data.get("msg", ""),
            data=ListBatchAsyncInferPayload.from_dict(data.get("data", {}))
        )


@dataclass
class GetBatchAsyncInferDetailRequest:
    """获取批量推理详情请求"""
    batch_id: str


@dataclass
class GetBatchAsyncInferDetailPayload:
    """
    批量推理详情响应数据
    
    字段说明（基于后端API实际返回，2025-12-19验证）：
    - batch_id: 任务ID
    - name: 任务名称
    - description: 任务描述
    - model_service: 模型服务名称
    - status: 任务状态
    - input_file_path: 输入文件名（如 "test_model.jsonl"）
    - output_file_path: 输出文件夹路径（如 "wd-batch-1203/llm-batch/d7313aad-..."）
    - request_num: 总请求数
    - finished_request_num: 已完成请求数
    - progress: 进度（0-1的浮点数）
    - user_email: 用户邮箱
    - created_at: 创建时间
    - scheduled_at: 调度时间
    - finished_at: 完成时间
    - expire_at: 过期时间
    - err_msg: 错误信息（仅错误情况下存在）
    """
    batch_id: str
    name: str
    model_service: str
    status: str
    request_num: int
    finished_request_num: int
    progress: float
    user_email: str
    created_at: str
    description: str = ""
    input_file_path: str = ""
    output_file_path: str = ""  # 输出文件夹路径
    scheduled_at: str = ""
    finished_at: str = ""
    expire_at: str = ""
    err_msg: str = ""  # 仅错误情况下存在

    @classmethod
    def from_dict(cls, data: Dict) -> 'GetBatchAsyncInferDetailPayload':
        return cls(
            batch_id=data.get("batch_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            model_service=data.get("model_service", ""),
            status=data.get("status", ""),
            input_file_path=data.get("input_file_path", ""),
            output_file_path=data.get("output_file_path", ""),
            request_num=data.get("request_num", 0),
            finished_request_num=data.get("finished_request_num", 0),
            progress=data.get("progress", 0.0),
            user_email=data.get("user_email", ""),
            created_at=data.get("created_at", ""),
            scheduled_at=data.get("scheduled_at", ""),
            finished_at=data.get("finished_at", ""),
            expire_at=data.get("expire_at", ""),
            err_msg=data.get("err_msg", "")
        )


@dataclass
class GetBatchAsyncInferDetailResponse:
    """获取批量推理详情响应"""
    errno: int
    msg: str
    data: GetBatchAsyncInferDetailPayload

    @classmethod
    def from_dict(cls, data: Dict) -> 'GetBatchAsyncInferDetailResponse':
        return cls(
            errno=data.get("errno", 0),
            msg=data.get("msg", ""),
            data=GetBatchAsyncInferDetailPayload.from_dict(data.get("data", {}))
        )


@dataclass
class CancelBatchAsyncInferRequest:
    """取消批量推理任务请求"""
    batch_id: str


@dataclass
class CancelBatchAsyncInferPayload:
    """取消批量推理任务响应数据"""
    batch_id: str
    status: str
    message: str

    @classmethod
    def from_dict(cls, data: Dict) -> 'CancelBatchAsyncInferPayload':
        return cls(
            batch_id=data.get("batch_id", ""),
            status=data.get("status", ""),
            message=data.get("message", "")
        )


@dataclass
class CancelBatchAsyncInferResponse:
    """取消批量推理任务响应"""
    errno: int
    msg: str
    data: CancelBatchAsyncInferPayload

    @classmethod
    def from_dict(cls, data: Dict) -> 'CancelBatchAsyncInferResponse':
        return cls(
            errno=data.get("errno", 0),
            msg=data.get("msg", ""),
            data=CancelBatchAsyncInferPayload.from_dict(data.get("data", {}))
        )