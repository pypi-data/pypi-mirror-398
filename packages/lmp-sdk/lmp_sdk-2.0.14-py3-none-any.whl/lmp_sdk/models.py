from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
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
    """异步推理参数"""
    model: str
    messages: List[Message]
    temperature: float = 0.000001
    frequency_penalty: float = 1.05
    stream: bool = False
    lpai_max_request_retries: int = 5
    lpai_callback: Optional[str] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "frequency_penalty": self.frequency_penalty,
            "stream": self.stream,
            "lpai_max_request_retries": self.lpai_max_request_retries,
            "lpai_callback": self.lpai_callback,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "presence_penalty":self.presence_penalty,
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
    """异步推理请求"""
    contents: List[Content]
    model: str = ""
    temperature: float = 0.000001
    frequency_penalty: float = 1.05
    stream: bool = False
    lpai_callback: Optional[str] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    lpai_max_request_retries: int = 5
    role: str = "user"

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