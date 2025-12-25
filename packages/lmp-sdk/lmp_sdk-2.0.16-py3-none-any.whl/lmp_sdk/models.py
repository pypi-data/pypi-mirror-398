from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "PENDING"      # 排队中
    RUNNING = "RUNNING"      # 运行中
    FAILED = "FAILED"        # 失败
    SUCCEEDED = "SUCCEEDED"  # 成功
    UNKNOWN = "UNKNOWN"      # 未知异常


class ContentType(Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"
    VIDEO_URL = "video_url"


@dataclass
class CallbackConfig:
    """
    Args:
        url: 回调URL，支持以下格式：
            - https://your-server.com/callback  (HTTP回调)
            - kafka://bootstrap_servers/topic   (Kafka回调)
            - id:your-internal-id               (内部ID标识)
        include_input: 是否在回调中包含请求的input（默认False）
                      当设置为True时，回调payload中会包含原始请求内容
    """
    url: str
    include_input: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "include_input": self.include_input
        }


@dataclass
class Content:
    """内容数据类"""
    type: ContentType
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None
    video_url: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {"type": self.type.value}
        if self.type == ContentType.TEXT and self.text is not None:
            data["text"] = self.text
        if self.type == ContentType.IMAGE_URL and self.image_url is not None:
            data["image_url"] = self.image_url # type: ignore
        if self.type == ContentType.VIDEO_URL and self.video_url is not None:
            data["video_url"] = self.video_url # type: ignore
        return data


@dataclass
class Message:
    """消息数据类"""
    role: str
    content: List[Content]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": [c.to_dict() for c in self.content]
        }


@dataclass
class PostAsyncInferParams:
    """异步推理参数（内部使用）"""
    model: str
    messages: Union[List[Message], List[Dict[str, Any]]]  # 支持Message对象或字典
    temperature: float = 0.000001
    frequency_penalty: float = 1.05
    stream: bool = False
    lpai_max_request_retries: int = 5
    lpai_callback: Optional[Union[str, Dict[str, Any]]] = None
    lpai_priority: Optional[str] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为API请求字典"""
        # 处理messages：支持Message对象或字典格式
        if self.messages and isinstance(self.messages[0], dict):
            # 字典格式：直接使用
            messages_data = self.messages
        else:
            # Message对象：调用to_dict()转换
            messages_data = [m.to_dict() for m in self.messages]
        
        return {
            "model": self.model,
            "messages": messages_data,
            "temperature": self.temperature,
            "frequency_penalty": self.frequency_penalty,
            "stream": self.stream,
            "lpai_max_request_retries": self.lpai_max_request_retries,
            "lpai_callback": self.lpai_callback,
            "lpai_priority": self.lpai_priority,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
        }


@dataclass
class AsyncInferData:
    """异步推理响应数据"""
    task_id: str
    queue_length: int = 0
    processing_speed: int = 0
    estimated_scheduled_time: int = 0

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> Optional['AsyncInferData']:
        if not data:
            return None
        return cls(
            task_id=data.get("task_id", ""),
            queue_length=data.get("queue_length", 0),
            processing_speed=data.get("processing_speed", 0),
            estimated_scheduled_time=data.get("estimated_scheduled_time", 0)
        )


@dataclass
class PostAsyncInferResponse:
    """异步推理响应"""
    msg: Optional[str] = None
    data: Optional[AsyncInferData] = None
    errno: int = 0

    @classmethod
    def from_dict(cls, data: Dict) -> 'PostAsyncInferResponse':
        return cls(
            msg=data.get("msg"),
            data=AsyncInferData.from_dict(data.get("data")),
            errno=data.get("errno", 0)
        )


@dataclass
class TaskData:
    """任务数据"""
    task_id: str
    user_email: str = ""
    url: str = ""
    task_input: str = ""
    task_output: str = ""
    statistics: str = ""
    status: str = ""
    failed_reason: str = ""
    created_at: str = ""
    scheduled_at: str = ""
    finished_at: str = ""
    e2e_latency: int = 0
    processing_speed: float = 0.0
    estimated_scheduled_time: int = 0

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> Optional['TaskData']:
        if not data:
            return None
        return cls(**{k: data.get(k, v) for k, v in cls.__annotations__.items()})


@dataclass
class TaskResponse:
    """任务响应"""
    errno: int
    msg: str
    data: Optional[TaskData]

    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskResponse':
        return cls(
            errno=data.get("errno", 0),
            msg=data.get("msg", ""),
            data=TaskData.from_dict(data.get("data"))
        )


@dataclass
class PostAsyncInferRequest:
    """异步推理请求
    
    支持三种使用方式：
    1. 使用messages字段（Message对象列表）：完整格式，支持多轮多模态对话
    2. 使用contents+role字段：简单模式，只支持单个message
       例如：contents=[Content(...)], role="user"
    
    注意：如果同时提供messages和contents，优先使用messages
    """
    # 支持Message对象列表或字典列表（兼容OpenAI格式）
    messages: Optional[Union[List[Message], List[Dict[str, Any]]]] = None
    contents: Optional[List[Content]] = None
    role: str = "user"
    
    # 模型参数
    model: str = ""
    temperature: float = 0.000001
    frequency_penalty: float = 1.05
    stream: bool = False
    lpai_callback: Optional[Union[str, CallbackConfig]] = None
    lpai_priority: Optional[str] = None  # 优先级："normal"或"high"
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    lpai_max_request_retries: int = 5

@dataclass
class GetAsyncInferRequest:
    task_id: str = ""

@dataclass
class Task:
    """任务"""
    id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        return cls(**data)