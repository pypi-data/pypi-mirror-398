import hashlib
import logging
from datetime import timedelta
from typing import Any
from warnings import warn

from asgiref.sync import sync_to_async
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.tasks.base import Task, TaskResult, TaskResultStatus
from django.utils import timezone

from ..db.models import QueuedTask, TaskStatus, VTaskMetadata
from ..serialization import deserialize, serialize
from .base import TaskPayload, VTasksBaseBackend

logger = logging.getLogger(__name__)


_sqlite_warning_issued = False


class DatabaseTaskBackend(VTasksBaseBackend):
    supports_throttle = False

    def __init__(self, alias: str, params: dict[str, Any] | None) -> None:
        super().__init__(alias, params)

    @property
    def supports_unique(self) -> bool:
        # The unique constraint implementation relies on features not available in MySQL.  # noqa: E501
        return connection.vendor != "mysql"

    def _get_lock_params(self) -> dict[str, Any]:
        global _sqlite_warning_issued
        if connection.vendor in ("postgresql", "mysql"):
            return {"skip_locked": True}

        if connection.vendor == "sqlite" and not _sqlite_warning_issued:
            warn(
                "Using SQLite backend, which does not support 'skip_locked'. "
                "Concurrency will be limited, and tasks may block. "
                "Consider using PostgreSQL or MySQL for production environments.",
                UserWarning,
                stacklevel=2,
            )
            _sqlite_warning_issued = True

        return {"skip_locked": False}

    def _prepare_bulk_models(
        self,
        tasks: list[TaskPayload],
    ) -> tuple[list[QueuedTask], list[TaskResult]]:
        instances = []
        results = []

        for task, args, kwargs in tasks:
            unique = getattr(task, "unique", False)
            unique_key = getattr(task, "unique_key", None)
            ttl = getattr(task, "ttl", None)
            remove_unique_on_complete = getattr(task, "remove_unique_on_complete", True)
            data = self._build_task_data(
                task,
                args,
                kwargs,
                unique=unique,
                unique_key=unique_key,
                ttl=ttl,
                remove_unique_on_complete=remove_unique_on_complete,
            )
            payload = serialize(data)
            instance = QueuedTask(
                queue=data["queue"],
                data=payload,
                status=TaskStatus.QUEUED,
                unique_key=data["unique_key"],
            )
            instances.append(instance)

            safe_args, safe_kwargs = self._sanitize_args_kwargs(args, kwargs)

            results.append(
                TaskResult(
                    task=task,
                    id=str(instance.id),
                    status=TaskResultStatus.READY,
                    args=safe_args,
                    kwargs=safe_kwargs,
                    enqueued_at=instance.created_at,
                    started_at=None,
                    finished_at=None,
                    last_attempted_at=None,
                    backend=self.alias,
                    errors=[],
                    worker_ids=[],
                )
            )
        return instances, results

    async def aenqueue_many(self, tasks: list[TaskPayload]) -> list["TaskResult"]:
        instances, results = self._prepare_bulk_models(tasks)
        await QueuedTask.objects.abulk_create(instances)
        return results

    def enqueue_many(self, tasks: list[TaskPayload]) -> list["TaskResult"]:
        instances, results = self._prepare_bulk_models(tasks)
        QueuedTask.objects.bulk_create(instances)
        return results

    async def aenqueue(
        self,
        task: "Task",
        args: tuple,
        kwargs: dict,
    ) -> "TaskResult | None":
        # Support unique options from both kwargs dict (when called via task.aenqueue())
        # and as keyword arguments (for direct backend calls)
        unique = getattr(task, "unique", False)
        unique_key = getattr(task, "unique_key", None)
        ttl = getattr(task, "ttl", None)
        remove_unique_on_complete = getattr(task, "remove_unique_on_complete", True)

        data = self._build_task_data(
            task,
            args,
            kwargs,
            unique=unique,
            unique_key=unique_key,
            ttl=ttl,
            remove_unique_on_complete=remove_unique_on_complete,
        )
        payload = serialize(data)

        try:
            queued_task = await QueuedTask.objects.acreate(
                queue=data["queue"],
                data=payload,
                status=TaskStatus.QUEUED,
                unique_key=data["unique_key"],
            )
        except IntegrityError:
            logger.info("Debounced task: %s", data["func"])
            return None

        safe_args, safe_kwargs = self._sanitize_args_kwargs(args, kwargs)

        return TaskResult(
            task=task,
            id=str(queued_task.id),
            status=TaskResultStatus.READY,
            enqueued_at=None,
            started_at=None,
            last_attempted_at=None,
            finished_at=None,
            args=safe_args,
            kwargs=safe_kwargs,
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )

    def enqueue(
        self,
        task: "Task",
        args: tuple,
        kwargs: dict,
    ) -> "TaskResult | None":
        # Support unique options from both kwargs dict (when called via task.enqueue())
        # and as keyword arguments (for direct backend calls)
        unique = getattr(task, "unique", False)
        unique_key = getattr(task, "unique_key", None)
        ttl = getattr(task, "ttl", None)
        remove_unique_on_complete = getattr(task, "remove_unique_on_complete", True)

        data = self._build_task_data(
            task,
            args,
            kwargs,
            unique=unique,
            unique_key=unique_key,
            ttl=ttl,
            remove_unique_on_complete=remove_unique_on_complete,
        )
        payload = serialize(data)

        try:
            queued_task = QueuedTask.objects.create(
                queue=data["queue"],
                data=payload,
                status=TaskStatus.QUEUED,
                unique_key=data["unique_key"],
            )
        except IntegrityError:
            logger.info("Debounced task: %s", data["func"])
            return None

        safe_args, safe_kwargs = self._sanitize_args_kwargs(args, kwargs)

        return TaskResult(
            task=task,
            id=str(queued_task.id),
            status=TaskResultStatus.READY,
            enqueued_at=queued_task.created_at,
            started_at=None,
            last_attempted_at=None,
            finished_at=None,
            args=safe_args,
            kwargs=safe_kwargs,
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )

    @sync_to_async
    @transaction.atomic
    def acquire_lock(self, key: str, ttl: int) -> bool:
        if connection.vendor == "postgresql":
            # Use a stable hash to convert the string key into two 32-bit integers.
            # PostgreSQL advisory locks are identified by integers.
            h = hashlib.sha1(key.encode("utf-8"))
            # Split the 160-bit hash into two 32-bit integers for the lock ID.
            # This is more robust than using a single 64-bit integer.
            lock_id1 = int.from_bytes(h.digest()[:4], "big", signed=True)
            lock_id2 = int.from_bytes(h.digest()[4:8], "big", signed=True)

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_try_advisory_xact_lock(%s, %s)", [lock_id1, lock_id2]
                )
                lock_acquired = cursor.fetchone()[0]
                return lock_acquired

        # Fallback for other database backends (MySQL, etc.)
        now = timezone.now()
        try:
            lock = VTaskMetadata.objects.select_for_update(
                **self._get_lock_params()
            ).get(key=key)
            if lock.expires_at < now or lock.value == self.worker_id:
                lock.expires_at = now + timedelta(seconds=ttl)
                lock.value = self.worker_id
                lock.save()
                return True
            return False
        except VTaskMetadata.DoesNotExist:
            VTaskMetadata.objects.create(
                key=key, value=self.worker_id, expires_at=now + timedelta(seconds=ttl)
            )
            return True
        except DatabaseError:
            # This can happen if another process created the lock row concurrently.
            return False

    @sync_to_async
    def get_metadata(self, key: str) -> Any:
        try:
            metadata = VTaskMetadata.objects.get(key=key)
            return metadata.value
        except VTaskMetadata.DoesNotExist:
            return None

    @sync_to_async
    def set_metadata(self, key: str, value: Any) -> None:
        VTaskMetadata.objects.update_or_create(key=key, defaults={"value": str(value)})

    @sync_to_async
    @transaction.atomic
    def fetch_batch_sync(self, queue: str, count: int, timeout: float) -> list[dict]:
        logger.debug("Fetching batch of %d tasks from queue %s", count, queue)
        tasks_to_process = list(
            QueuedTask.objects.select_for_update(**self._get_lock_params())
            .filter(queue=queue, status=TaskStatus.QUEUED)
            .order_by("created_at")[:count]
        )
        if not tasks_to_process:
            return []

        task_ids = [task.id for task in tasks_to_process]
        QueuedTask.objects.filter(id__in=task_ids).update(
            status=TaskStatus.PROCESSING, worker_id=self.worker_id
        )

        tasks = []
        for task in tasks_to_process:
            task_data = deserialize(task.data)
            task_data["_raw"] = task.data
            task_data["id"] = str(task.id)
            task_data["queue"] = task.queue
            tasks.append(task_data)
        return tasks

    async def fetch_batch(self, queue: str, count: int, timeout: float) -> list[dict]:
        # The timeout is not used in the Postgres backend, as it does not block.
        return await self.fetch_batch_sync(queue, count, timeout)

    @sync_to_async
    @transaction.atomic
    def _fetch_task_sync(self, queues: list[str]) -> dict | None:
        logger.debug("Fetching task from queues %s", queues)
        queued_task = (
            QueuedTask.objects.select_for_update(**self._get_lock_params())
            .filter(queue__in=queues, status=TaskStatus.QUEUED)
            .order_by("created_at")
            .first()
        )

        if queued_task:
            queued_task.status = TaskStatus.PROCESSING
            queued_task.worker_id = self.worker_id
            queued_task.save()
            task_data = deserialize(queued_task.data)
            task_data["_raw"] = queued_task.data
            task_data["id"] = str(queued_task.id)
            task_data["queue"] = queued_task.queue
            return task_data
        return None

    async def _fetch_task(self, queues: list[str]) -> dict | None:
        return await self._fetch_task_sync(queues)

    @sync_to_async
    def _ack_task_sync(self, task_id: str) -> None:
        QueuedTask.objects.filter(id=task_id).delete()

    async def _ack_task(self, task_data: dict) -> None:
        await self._ack_task_sync(task_data["id"])

    @sync_to_async
    @transaction.atomic
    def _fail_task_sync(self, task_data: dict, exception: Exception) -> None:
        import time
        import traceback

        task_id = task_data.get("id", "unknown")
        logger.warning("Task %s failed. Marking as FAILED.", task_id, exc_info=True)

        failed_data = task_data.copy()
        failed_data.pop("_raw", None)
        failed_data["error_msg"] = str(exception)
        failed_data["error_traceback"] = traceback.format_exc()
        failed_data["failed_at"] = time.time()
        new_payload = serialize(failed_data)

        # Update the task to FAILED status
        task = QueuedTask.objects.filter(id=task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.data = new_payload
            task.save()

        # Trim failed tasks to DLQ cap
        failed_count = QueuedTask.objects.filter(status=TaskStatus.FAILED).count()
        if failed_count > self.dlq_cap:
            # Get the IDs of the oldest failed tasks that exceed the cap
            tasks_to_delete = QueuedTask.objects.filter(
                status=TaskStatus.FAILED
            ).order_by("created_at")[: failed_count - self.dlq_cap]
            task_ids_to_delete = list(tasks_to_delete.values_list("id", flat=True))
            QueuedTask.objects.filter(id__in=task_ids_to_delete).delete()

    async def _fail_task(self, task_data: dict, exception: Exception) -> None:
        await self._fail_task_sync(task_data, exception)

    async def _rescue_tasks(self) -> None:
        # For Postgres, rescue tasks that were marked as PROCESSING by this worker
        # but were never completed (e.g., worker crashed)
        @sync_to_async
        @transaction.atomic
        def _rescue():
            rescued = QueuedTask.objects.filter(
                worker_id=self.worker_id, status=TaskStatus.PROCESSING
            )
            count = rescued.count()
            if count > 0:
                rescued.update(status=TaskStatus.QUEUED, worker_id=None)
                logger.warning("Rescued %d tasks", count)

        await _rescue()
