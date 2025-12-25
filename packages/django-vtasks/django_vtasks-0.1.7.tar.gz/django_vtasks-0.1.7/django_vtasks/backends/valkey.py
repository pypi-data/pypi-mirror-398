import logging
import time
import traceback
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from django.core.cache import caches
from django.core.cache.backends.base import InvalidCacheBackendError
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.tasks.base import Task, TaskResult, TaskResultStatus
from django.utils.crypto import get_random_string
from valkey.asyncio import Valkey

from ..conf import settings
from ..serialization import deserialize, serialize
from .base import TaskPayload, VTasksBaseBackend

if TYPE_CHECKING:
    from valkey import ConnectionPool as SyncConnectionPool
    from valkey import Valkey as SyncValkey

logger = logging.getLogger(__name__)


class ValkeyTaskBackend(VTasksBaseBackend):
    supports_unique = True
    supports_throttle = True

    def __init__(self, alias: str, params: dict[str, Any] | None) -> None:
        super().__init__(alias, params)
        if "OPTIONS" in self.options:
            self.options = self.options["OPTIONS"]
        self._client: "Valkey" | None = None
        self._sync_client: "SyncValkey" | None = None
        self._sync_pool: "SyncConnectionPool" | None = None

        cache_alias = self.options.get("cache_alias")
        if cache_alias:
            try:
                cache = caches[cache_alias]
            except InvalidCacheBackendError:
                raise ImproperlyConfigured(f"Cache '{cache_alias}' not found in CACHES")

            if not hasattr(cache, "get_raw_client"):
                raise ImproperlyConfigured(
                    f"The cache '{cache_alias}' does not support 'get_raw_client'. "
                    "Please use a django-vcache backend."
                )

            # django-vcache returns the raw client, which is what we want.
            self._sync_client = cache.get_raw_client(async_client=False)
            self._client = cache.get_raw_client(async_client=True)
            self.pool = None  # Using cache's pool management
        else:
            if "CONNECTION_POOL" in self.options:
                self.pool = self.options["CONNECTION_POOL"]
            else:
                self.pool = None

    def _get_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    @property
    def prefix(self):
        return settings.VTASKS_VALKEY_PREFIX

    @property
    def client(self) -> "Valkey":
        if self._client is None:
            if self.pool:
                self._client = Valkey(connection_pool=self.pool)
            else:
                url = self.options.get("BROKER_URL")
                if not url:
                    raise ImproperlyConfigured(
                        "BROKER_URL is not configured for Valkey backend"
                    )
                self._client = Valkey.from_url(url)
        return self._client

    @property
    def sync_client(self) -> "SyncValkey":
        if self._sync_client is None:
            url = self.options.get("BROKER_URL")
            if not url:
                raise ImproperlyConfigured(
                    "BROKER_URL is required for synchronous enqueue, "
                    "even when using CONNECTION_POOL"
                )
            # Lazy load when needed
            from valkey import ConnectionPool as SyncConnectionPool
            from valkey import Valkey as SyncValkey

            self._sync_pool = SyncConnectionPool.from_url(url)
            self._sync_client = SyncValkey(connection_pool=self._sync_pool)
        return self._sync_client

    def _prepare_bulk_payloads(
        self,
        tasks: list[TaskPayload],
    ) -> tuple[dict[str, list[bytes]], list[TaskResult]]:
        grouped_payloads = defaultdict(list)
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
            data["id"] = get_random_string(32)
            payload = serialize(data)
            grouped_payloads[data["queue"]].append(payload)

            safe_args, safe_kwargs = self._sanitize_args_kwargs(args, kwargs)

            results.append(
                TaskResult(
                    task=task,
                    id=data["id"],
                    status=TaskResultStatus.READY,
                    args=safe_args,
                    kwargs=safe_kwargs,
                    enqueued_at=None,
                    started_at=None,
                    finished_at=None,
                    last_attempted_at=None,
                    backend=self.alias,
                    errors=[],
                    worker_ids=[],
                )
            )
        return grouped_payloads, results

    async def aenqueue_many(self, tasks: list[TaskPayload]) -> list["TaskResult"]:
        grouped_payloads, results = self._prepare_bulk_payloads(tasks)

        for queue_name, payloads in grouped_payloads.items():
            await self.client.lpush(self._get_key(f"q:{queue_name}"), *payloads)

        return results

    def enqueue_many(self, tasks: list[TaskPayload]) -> list["TaskResult"]:
        grouped_payloads, results = self._prepare_bulk_payloads(tasks)

        def _push():
            for queue_name, payloads in grouped_payloads.items():
                self.sync_client.lpush(self._get_key(f"q:{queue_name}"), *payloads)

        transaction.on_commit(_push)

        return results

    async def _fetch_task(self, queues: list[str]) -> dict | None:
        queue = queues[0]
        source = self._get_key(f"q:{queue}")
        dest = self._get_key(f"processing:{self.worker_id}")
        logger.debug("Fetching task from %s to %s", source, dest)
        data = await self.client.blmove(
            source,
            dest,
            2,  # Timeout
            src="RIGHT",
            dest="LEFT",
        )
        if data:
            unpacked = deserialize(data)
            unpacked["_raw"] = data
            return unpacked
        return None

    async def _ack_batch(self, tasks: list[dict]) -> None:
        """For Valkey, tasks are popped from the queue, so they are already acked."""
        pass

    async def _ack_task(self, task_data: dict) -> None:
        await self.client.lrem(
            self._get_key(f"processing:{self.worker_id}"), 1, task_data["_raw"]
        )
        if task_data.get("unique") and task_data.get("remove_unique_on_complete"):
            await self.client.delete(self._get_key(f"unique:{task_data['unique_key']}"))

    async def _fail_task(self, task_data: dict, exception: Exception) -> None:
        task_id = task_data.get("id", "unknown")
        logger.warning("Task %s failed. Moving to DLQ.", task_id, exc_info=True)

        failed_data = task_data.copy()
        failed_data.pop("_raw", None)
        failed_data["error_msg"] = str(exception)
        failed_data["error_traceback"] = traceback.format_exc()
        failed_data["failed_at"] = time.time()
        new_payload = serialize(failed_data)

        async with self.client.pipeline(transaction=True) as pipe:
            pipe.lpush(self._get_key("q:failed"), new_payload)
            pipe.ltrim(self._get_key("q:failed"), 0, self.dlq_cap - 1)
            pipe.lrem(
                self._get_key(f"processing:{self.worker_id}"), 1, task_data["_raw"]
            )
            await pipe.execute()

        if task_data.get("unique") and task_data.get("remove_unique_on_complete"):
            await self.client.delete(self._get_key(f"unique:{task_data['unique_key']}"))

    async def _rescue_tasks(self) -> None:
        while True:
            raw = await self.client.rpop(self._get_key(f"processing:{self.worker_id}"))
            if raw is None:
                break
            unpacked = deserialize(raw)
            queue = unpacked.get("queue", "default")
            await self.client.lpush(self._get_key(f"q:{queue}"), raw)
            logger.warning("Rescued task %s", unpacked["id"])

    async def aenqueue(
        self,
        task: "Task",
        args: tuple,
        kwargs: dict,
    ) -> "TaskResult | None":
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
        data["id"] = get_random_string(32)

        if data["unique"] and data["unique_key"]:
            unique_valkey_key = self._get_key(f"unique:{data['unique_key']}")
            # Set a default TTL for mutex mode to prevent race conditions
            # If ttl is None and remove_unique_on_complete is True (mutex mode),
            # set a short TTL (5 seconds) to prevent the lock from persisting
            # if the task completes before all enqueue attempts finish
            ttl = data["ttl"]
            if ttl is None and data["remove_unique_on_complete"]:
                ttl = 5  # Default 5 second TTL for mutex mode

            # Try to acquire the unique lock. If it already exists, the task is skipped.
            set_result = await self.client.set(unique_valkey_key, "1", nx=True, ex=ttl)
            if not set_result:
                logger.info("Skipped unique task: %s", data["func"])
                return None

        payload = serialize(data)

        await self.client.lpush(self._get_key(f"q:{data['queue']}"), payload)

        safe_args, safe_kwargs = self._sanitize_args_kwargs(args, kwargs)

        return TaskResult(
            task=task,
            id=data["id"],
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
        on_commit = getattr(task, "on_commit", True)
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
        data["id"] = get_random_string(32)

        if data["unique"] and data["unique_key"]:
            unique_valkey_key = self._get_key(f"unique:{data['unique_key']}")
            # Set a default TTL for mutex mode to prevent race conditions
            ttl = data["ttl"]
            if ttl is None and data["remove_unique_on_complete"]:
                ttl = 5  # Default 5 second TTL for mutex mode

            # Try to acquire the unique lock. If it already exists, the task is skipped.
            if not self.sync_client.set(unique_valkey_key, "1", nx=True, ex=ttl):
                logger.info("Skipped unique task: %s", data["func"])
                return None

        payload = serialize(data)

        def _push():
            self.sync_client.lpush(self._get_key(f"q:{data['queue']}"), payload)

        if on_commit:
            transaction.on_commit(_push)
        else:
            _push()

        safe_args, safe_kwargs = self._sanitize_args_kwargs(args, kwargs)

        return TaskResult(
            task=task,
            id=data["id"],
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

    async def acquire_lock(self, key: str, ttl: int) -> bool:
        """
        Acquire a distributed lock with the given key and TTL.
        Returns True if the lock was acquired, False otherwise.
        """
        lock_key = self._get_key(f"scheduler:{key}")

        # Try to acquire the lock with SET NX
        result = await self.client.set(lock_key, self.worker_id, nx=True, ex=ttl)
        if result:
            return True

        # If SET NX failed, check if we already own the lock
        current_owner = await self.client.get(lock_key)
        if current_owner and current_owner.decode("utf-8") == self.worker_id:
            # We already own the lock, refresh it
            await self.client.set(lock_key, self.worker_id, ex=ttl)
            return True

        return False

    async def get_metadata(self, key: str) -> Any:
        """
        Get metadata value for the given key.
        Returns None if the key doesn't exist.
        """
        meta_key = self._get_key(f"scheduler:{key}")
        value = await self.client.get(meta_key)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    async def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value for the given key.
        """
        meta_key = self._get_key(f"scheduler:{key}")
        await self.client.set(meta_key, str(value))

    async def fetch_batch(self, queue: str, count: int, timeout: float) -> list[dict]:
        """
        Fetches a batch of tasks from the specified queue.
        This is an "unsafe" batch operation as it does not move the tasks
        to a processing queue. If the worker crashes, the tasks are lost.
        """
        key_name = self._get_key(f"q:{queue}")
        logger.debug("Fetching batch of %d tasks from %s", count, key_name)
        result = await self.client.blmpop(
            timeout, 1, key_name, direction="RIGHT", count=count
        )
        if not result:
            return []
        _, items = result  # Unpack the result (key, items)

        tasks = []
        for item in items:
            task_data = deserialize(item)
            task_data["_raw"] = item
            tasks.append(task_data)
        return tasks
