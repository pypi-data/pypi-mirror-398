import json
import signal
import sys
import threading
import atexit
from pathlib import Path
from typing import Optional, Dict, List, Callable
import logging

from lmp_sdk.models import Task, TaskResponse
from lmp_sdk.exceptions import QueueFullError
from lmp_sdk.constants import DEFAULT_MAX_QUEUE_SIZE

logger = logging.getLogger(__name__)

class TaskQueue:
    """任务队列"""
    def __init__(
            self,
            persist_file: Optional[str] = None,
            max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
            on_task_added: Optional[Callable[[Task], None]] = None
    ):
        if persist_file is None:
            home_dir = Path.home()
            persist_file = home_dir / ".lmp" / "task_queue.json"

        self.persist_file = Path(persist_file)
        self.max_queue_size = max_queue_size
        self.on_task_added = on_task_added


        self.tasks: Dict[str, Task] = {}
        self.queue: List[str] = []

        self.lock = threading.RLock()
        self.stop_event = threading.Event()

        self._initialize()
        logger.info(f"TaskQueue initialized with persist file: {self.persist_file}")

    def _initialize(self):
        # 确保目录存在
        self.persist_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载已有任务
        try:
            self.load_from_file()
        except FileNotFoundError:
            logger.info("No existing task file found")
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")

    def load_from_file(self):
        if not self.persist_file.exists():
            raise FileNotFoundError()

        with open(self.persist_file, 'r') as f:
            data = json.load(f)

        with self.lock:
            self.tasks = {
                tid: Task.from_dict(tdata)
                for tid, tdata in data.get("tasks", {}).items()
            }
            self.queue = data.get("queue", [])

        # 加载后删除文件
        self.persist_file.unlink()
        logger.info(f"Loaded {len(self.tasks)} tasks from file")

    def shutdown(self):
        """关闭队列"""
        logger.info("Shutting down TaskQueue")
        self.stop_event.set()

        try:
            self.save_to_file()
            logger.info("Task queue saved successfully")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

    def save_to_file(self):
        """保存任务到文件"""
        queue = [tid for tid,t in self.tasks.items()]

        with self.lock:
            data = {
                "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
                "queue": queue
            }
            print(f"[DEBUG] 保存时的状态:")
            print(f"  - queue 长度: {len(queue)}")
            print(f"  - queue 内容: {queue}")

        # 确保目录存在
        self.persist_file.parent.mkdir(parents=True, exist_ok=True)

        # 原子写入
        temp_file = self.persist_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        temp_file.replace(self.persist_file)

        logger.info(f"Saved task ids to {self.persist_file}")

    def add_task(self, task_id: str) -> None:
        """添加任务"""
        with self.lock:
            if len(self.queue) >= self.max_queue_size:
                raise QueueFullError(f"Queue is full (max size: {self.max_queue_size})")

            task = Task(id=task_id)
            self.tasks[task_id] = task
            self.queue.append(task_id)

            logger.info(f"Added task: {task_id}")

        # 触发回调
        if self.on_task_added:
            threading.Thread(
                target=self.on_task_added,
                args=(task,),
                daemon=True
            ).start()

    def get_next_task(self) -> Optional[Task]:
        """获取下一个任务（保持 queue 和 tasks 同步）"""
        with self.lock:
            if self.queue:
                #task_id = self.queue[0]  # 不要 pop，只是查看
                task_id = self.queue.pop(0)
                print(f'task_id is: {task_id}')
                if task_id in self.tasks:
                    return self.tasks[task_id]
                else:
                    # 如果任务不存在，才从队列中移除
                    self.queue.pop(0)
                    return self.get_next_task()  # 递归查找下一个
            return None

    def remove_task(self, task_id: str):
        """删除任务"""
        with self.lock:
            if task_id in self.queue:
                self.queue.remove(task_id)
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.debug(f"Removed task: {task_id}")