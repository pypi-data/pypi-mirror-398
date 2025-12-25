# API 端点
DEFAULT_API_ENDPOINT = "https://lpai.lixiang.com/lpai/api/lpai-service-lmp/async_infer"
BASE_GET_URL = "https://lpai.lixiang.com/lpai/api/lpai-service-lmp"

# 批量推理API端点
BATCH_API_BASE_URL = "https://lpai.lixiang.com/lpai/api/lpai-service-lmp"
BATCH_API_ENDPOINT = "https://lpai.lixiang.com/lpai/api/lpai-service-lmp/batch_async_infer"

# 默认模型
DEFAULT_MODEL = "qwen__qwen2_5-vl-72b-instruct"

# 默认参数
DEFAULT_TEMPERATURE = 0.000001
DEFAULT_FREQUENCY_PENALTY = 1.05
DEFAULT_MAX_RETRIES = 5
DEFAULT_POLLING_INTERVAL = 10  # 秒
DEFAULT_MAX_WAIT_TIME = 86400  # 24小时（秒）
DEFAULT_MAX_QUEUE_SIZE = 100000
DEFAULT_WORKER_NUM = 5

# 批量推理默认参数
DEFAULT_BATCH_MAX_WAITING_DAYS = 1  # 默认最大等待天数
DEFAULT_BATCH_PAGE_SIZE = 10  # 默认每页大小
DEFAULT_BATCH_POLL_INTERVAL = 30  # 批量任务状态轮询间隔（秒）
BATCH_REQUEST_DATASET = "datasets/lmp-request/versions/0.1.1"  # 批量请求文件上传数据集

# Asset SDK 配置
DEFAULT_ASSET_ENV = "prod"  # Asset SDK 默认环境