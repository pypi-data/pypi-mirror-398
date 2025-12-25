import socket
import time
import uuid
from typing import TYPE_CHECKING, Any

from django.tasks.backends.base import BaseTaskBackend

from ..conf import settings
from ..serialization import deserialize, serialize

if TYPE_CHECKING:
    from django.tasks.base import Task, TaskResult

    from ..tasks import VTask


TaskPayload = tuple["Task", tuple, dict]


class VTasksBaseBackend(BaseTaskBackend):
    supports_async_task = True
    supports_unique: bool = False
    supports_throttle: bool = False

    def __init__(self, alias: str, params: dict[str, Any] | None) -> None:
        super().__init__(alias, params)
        self.options = params or {}
        self.worker_id = f"{socket.gethostname()}-{uuid.uuid4().hex[:6]}"
        self.compress_threshold = self.options.get(
            "COMPRESS_THRESHOLD", settings.VTASKS_COMPRESS_THRESHOLD
        )
        self.dlq_cap = self.options.get("DLQ_CAP", settings.VTASKS_DLQ_CAP)

    def _sanitize_args_kwargs(self, args: tuple, kwargs: dict) -> tuple[list, dict]:
        """
        Sanitize args and kwargs to be JSON-compliant (e.g., datetime -> str).
        This is required because django.tasks.TaskResult runs normalize_json().
        """
        safe_args = deserialize(serialize(args))
        safe_kwargs = deserialize(serialize(kwargs))
        return safe_args, safe_kwargs

    def _build_task_data(
        self,
        task: "Task | VTask",
        args: tuple,
        kwargs: dict,
        *,
        unique: bool = False,
        unique_key: str | None = None,
        ttl: int | None = None,
        remove_unique_on_complete: bool = True,
    ) -> dict:
        """
        Create a dictionary with the task's data, excluding the ID.
        Uses getattr to safely access VTask-specific attributes,
        handling plain django.tasks.Task objects gracefully.
        """
        queue_name: str = getattr(task, "queue_name", "default")

        if unique and not unique_key:
            unique_key = self._generate_unique_key(
                f"{task.func.__module__}.{task.func.__name__}", args, kwargs
            )

        return {
            "func": f"{task.func.__module__}.{task.func.__name__}",
            "args": args,
            "kwargs": kwargs,
            "queue": queue_name,
            "ts": time.time(),
            "retries": 0,
            "unique": unique,
            "unique_key": unique_key,
            "ttl": ttl,
            "remove_unique_on_complete": remove_unique_on_complete,
        }

    def _generate_unique_key(self, name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate a unique key from the task's name, args, and kwargs.
        """
        # This is a simple implementation, but it should be effective.
        # For a more robust solution, consider using a faster hash algorithm
        # and serializing the args and kwargs in a more canonical way.
        return f"vtasks:unique:{name}:{hash((args, frozenset(kwargs.items())))}"

    async def _fetch_task(self, queues: list[str]) -> dict | None:
        raise NotImplementedError

    async def _ack_task(self, task_data: dict) -> None:
        raise NotImplementedError

    async def _fail_task(self, task_data: dict, exception: Exception) -> None:
        raise NotImplementedError

    async def acquire_lock(self, key: str, ttl: int) -> bool:
        raise NotImplementedError

    async def get_metadata(self, key: str) -> Any:
        raise NotImplementedError

    async def set_metadata(self, key: str, value: Any) -> None:
        raise NotImplementedError

    async def get_queue_depth(self, queue: str) -> int:
        raise NotImplementedError

    async def fetch_batch(self, queue: str, count: int, timeout: float) -> list[dict]:
        raise NotImplementedError

    async def _ack_batch(self, tasks: list[dict]) -> None:
        raise NotImplementedError

    def enqueue_many(self, tasks: list[TaskPayload], **options) -> list["TaskResult"]:
        """Enqueue multiple tasks at once."""
        raise NotImplementedError

    async def aenqueue_many(
        self, tasks: list[TaskPayload], **options
    ) -> list["TaskResult"]:
        """Asynchronously enqueue multiple tasks at once."""
        raise NotImplementedError


__all__ = ["VTasksBaseBackend"]
