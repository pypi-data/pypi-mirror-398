"""
An immediate backend for django-vtasks, designed for testing.

This backend extends Django's built-in ImmediateBackend to be compatible
with django-vtasks' VTask objects. It ensures that when a VTask is enqueued,
the underlying DjangoTask is what gets processed, preventing type
mismatches within Django's task system.

It also simulates batch processing by intercepting tasks sent to configured
batch queues and storing them in memory until explicitly flushed.
"""

from collections import defaultdict
from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.tasks.backends.immediate import (
    ImmediateBackend as DjangoImmediateBackend,
)
from django.utils.module_loading import import_string

from ..tasks import VTask


def _sanitize_for_result(args, kwargs):
    """
    Recursively sanitizes args and kwargs to convert complex types
    (datetime, UUID) to string representations for TaskResult.
    """

    def sanitize_value(value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, list):
            return [sanitize_value(v) for v in value]
        if isinstance(value, tuple):
            return tuple(sanitize_value(v) for v in value)
        if isinstance(value, dict):
            return {k: sanitize_value(v) for k, v in value.items()}
        return value

    sanitized_args = sanitize_value(list(args))
    sanitized_kwargs = sanitize_value(kwargs)
    return sanitized_args, sanitized_kwargs


class ImmediateBackend(DjangoImmediateBackend):
    """
    VTasks-compatible immediate execution backend with batching simulation.

    This backend runs tasks synchronously on enqueue. If a task is sent to
    a queue configured in `VTASKS_BATCH_QUEUES`, it is stored in memory
    instead of being executed. A manual call to `flush_batch()` or
    `flush_batches()` is then required to execute the batch processor task.

    It also correctly handles `VTask` objects by extracting the underlying
    `DjangoTask` before passing it to the parent implementation. This makes
    it suitable for unit testing environments.
    """

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.batch_config = getattr(settings, "VTASKS_BATCH_QUEUES", {})
        self.pending_batches = defaultdict(list)
        # Add configured batch queues to the list of valid queues
        for queue_name in self.batch_config:
            self.queues.add(queue_name)

    def enqueue(self, task, args, kwargs):
        """
        Enqueue a task. If it's for a batch queue, store it; otherwise,
        execute immediately.
        """
        queue_name = getattr(task, "queue_name", "default")

        intercept = False
        if queue_name in self.batch_config:
            intercept = True

            # Check if this task IS the batch handler itself.
            # If so, we must NOT intercept it, otherwise infinite recursion.
            if isinstance(task, VTask):
                task_path = task.name
            else:
                task_path = f"{task.func.__module__}.{task.func.__name__}"

            handler_path = self.batch_config[queue_name].get("task")
            if task_path == handler_path:
                intercept = False

        if intercept:
            if isinstance(task, VTask):
                task_path = task.name
            else:
                task_path = f"{task.func.__module__}.{task.func.__name__}"

            task_data = {"func": task_path, "args": list(args), "kwargs": kwargs}
            self.pending_batches[queue_name].append(task_data)
            return None

        # Fallback to default behavior for non-batch queues
        if isinstance(task, VTask):
            underlying_task = task.django_task
        else:
            underlying_task = task
        return super().enqueue(underlying_task, args, kwargs)

    async def aenqueue(self, task, args, kwargs):
        """
        Asynchronously enqueue a task. If it's for a batch queue, store it;
        otherwise, execute immediately.
        """
        queue_name = getattr(task, "queue_name", "default")

        intercept = False
        if queue_name in self.batch_config:
            intercept = True

            # Check if this task IS the batch handler itself.
            if isinstance(task, VTask):
                task_path = task.name
            else:
                task_path = f"{task.func.__module__}.{task.func.__name__}"

            handler_path = self.batch_config[queue_name].get("task")
            if task_path == handler_path:
                intercept = False

        if intercept:
            if isinstance(task, VTask):
                task_path = task.name
            else:
                task_path = f"{task.func.__module__}.{task.func.__name__}"

            task_data = {"func": task_path, "args": list(args), "kwargs": kwargs}
            self.pending_batches[queue_name].append(task_data)
            return None

        # Fallback to default behavior for non-batch queues
        if isinstance(task, VTask):
            underlying_task = task.django_task
        else:
            underlying_task = task
        return await super().aenqueue(underlying_task, args, kwargs)

    def flush_batch(self, queue_name: str):
        """
        Process all pending tasks for a given batch queue.
        """
        if queue_name not in self.batch_config:
            raise ValueError(f"'{queue_name}' is not a configured batch queue.")

        pending_tasks = self.pending_batches.pop(queue_name, [])
        if not pending_tasks:
            return None

        batch_task_path = self.batch_config[queue_name].get("task")
        if not batch_task_path:
            raise ValueError(f"No 'task' configured for batch queue '{queue_name}'.")

        batch_task_func = import_string(batch_task_path)
        return self.enqueue(batch_task_func, (pending_tasks,), {})

    def flush_batches(self):
        """Process all pending tasks for all configured batch queues."""
        for queue_name in list(self.pending_batches):
            self.flush_batch(queue_name)

    async def aflush_batch(self, queue_name: str):
        """
        Asynchronously process all pending tasks for a given batch queue.
        """
        if queue_name not in self.batch_config:
            raise ValueError(f"'{queue_name}' is not a configured batch queue.")

        pending_tasks = self.pending_batches.pop(queue_name, [])
        if not pending_tasks:
            return None

        batch_task_path = self.batch_config[queue_name].get("task")
        if not batch_task_path:
            raise ValueError(f"No 'task' configured for batch queue '{queue_name}'.")

        batch_task_func = import_string(batch_task_path)
        return await self.aenqueue(batch_task_func, (pending_tasks,), {})

    async def aflush_batches(self):
        """Asynchronously process all pending tasks for all batch queues."""
        for queue_name in list(self.pending_batches):
            await self.aflush_batch(queue_name)
