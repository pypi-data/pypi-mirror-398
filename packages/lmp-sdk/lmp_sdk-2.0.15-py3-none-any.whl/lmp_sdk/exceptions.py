class LMPException(Exception):
    """LMP SDK 基础异常"""
    pass

class TaskTimeoutError(LMPException):
    """任务超时异常"""
    pass

class QueueFullError(LMPException):
    """队列已满异常"""
    pass

class APIError(LMPException):
    """API 调用异常"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")

class TaskFailedError(LMPException):
    """任务执行失败异常"""
    pass

class BatchCreationError(LMPException):
    """批量任务创建失败异常"""
    pass

class BatchNotFoundError(LMPException):
    """批量任务不存在异常"""
    pass

class DatasetPathError(LMPException):
    """数据集路径错误异常"""
    pass

class AssetDownloadError(LMPException):
    """Asset结果下载失败异常"""
    pass

class AssetUploadError(LMPException):
    """Asset文件上传失败异常"""
    pass