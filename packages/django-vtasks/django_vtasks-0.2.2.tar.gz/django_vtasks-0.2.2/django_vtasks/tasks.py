"""
VTask - Extended Task class with unique task support.

This module provides a wrapper around Django's Task that adds support for
unique task parameters (unique, unique_key, ttl, remove_unique_on_complete).

The VTask class is designed to be a superset of Django's Task, maintaining
full compatibility while adding our custom features.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

from django.tasks import task_backends
from django.tasks.base import Task as DjangoTask

if TYPE_CHECKING:
    from django.tasks.base import TaskResult


@dataclass(frozen=True, slots=True, kw_only=True)
class VTask:
    """
    Extended Task class with support for unique task parameters.

    This wraps a Django Task and adds our custom parameters:
    - unique: Whether to enforce uniqueness
    - unique_key: Custom key for uniqueness (auto-generated if not provided)
    - ttl: Time-to-live for the unique lock (seconds)
    - remove_unique_on_complete: If True (mutex), remove lock on completion.
                                 If False (throttle), let TTL expire naturally.

    Usage:
        @task
        def my_task(arg1, arg2):
            ...

        # Using with unique parameters
        result = (
            await my_task.using(unique=True, unique_key="key1")
            .aenqueue(arg1, arg2)
        )  # noqa: E501

        # Using with backend selection
        result = await my_task.using(backend="postgres").aenqueue(arg1, arg2)
    """

    # Django Task fields
    django_task: DjangoTask

    # VTask-specific fields for unique functionality
    unique: bool = False
    unique_key: str | None = None
    ttl: int | None = None
    remove_unique_on_complete: bool = True
    on_commit: bool = True

    @property
    def func(self) -> Callable:
        """The underlying task function."""
        return self.django_task.func

    @property
    def priority(self) -> int:
        """The task's priority."""
        return self.django_task.priority

    @property
    def queue_name(self) -> str:
        """The queue name."""
        return self.django_task.queue_name

    @property
    def backend(self) -> str:
        """The backend alias."""
        return self.django_task.backend

    @property
    def name(self) -> str:
        """The task name."""
        return self.django_task.name

    @property
    def takes_context(self) -> bool:
        """Whether the task takes context."""
        return self.django_task.takes_context

    @property
    def run_after(self) -> datetime | None:
        """The earliest time the task will run."""
        return self.django_task.run_after

    @property
    def module_path(self) -> str:
        """The module path of the task function."""
        return self.django_task.module_path

    def using(
        self,
        *,
        priority: int | None = None,
        queue_name: str | None = None,
        run_after: datetime | None = None,
        backend: str | None = None,
        unique: bool | None = None,
        unique_key: str | None = None,
        ttl: int | None = None,
        remove_unique_on_complete: bool | None = None,
        on_commit: bool | None = None,
    ) -> VTask:
        """
        Create a new VTask with modified parameters.

        This method supports both Django's standard Task parameters
        and our VTask-specific unique parameters.

        Args:
            priority: Task priority (-100 to 100)
            queue_name: Name of the queue to use
            run_after: Earliest time the task will run
            backend: Backend alias to use
            unique: Whether to enforce uniqueness
            unique_key: Custom unique key
            ttl: Time-to-live for unique lock (seconds)
            remove_unique_on_complete: If True, remove lock on completion (mutex mode).
                                      If False, let TTL expire (throttle mode).
            on_commit: If True, enqueue the task after the current transaction commits.

        Returns:
            A new VTask instance with the modified parameters.
        """
        # Build changes for Django Task
        django_changes = {}
        if priority is not None:
            django_changes["priority"] = priority
        if queue_name is not None:
            django_changes["queue_name"] = queue_name
        if run_after is not None:
            django_changes["run_after"] = run_after
        if backend is not None:
            django_changes["backend"] = backend

        # Create new Django task if needed
        new_django_task = self.django_task.using(**django_changes) if django_changes else self.django_task

        # Build changes for VTask
        vtask_changes = {"django_task": new_django_task}
        if unique is not None:
            vtask_changes["unique"] = unique
        if unique_key is not None:
            vtask_changes["unique_key"] = unique_key
        if ttl is not None:
            vtask_changes["ttl"] = ttl
        if remove_unique_on_complete is not None:
            vtask_changes["remove_unique_on_complete"] = remove_unique_on_complete
        if on_commit is not None:
            vtask_changes["on_commit"] = on_commit

        from dataclasses import replace

        return replace(self, **vtask_changes)

    def enqueue(self, *args: Any, **kwargs: Any) -> TaskResult:
        """
        Queue up the Task to be executed (synchronous).

        Args:
            *args: Positional arguments for the task function
            **kwargs: Keyword arguments for the task function

        Returns:
            TaskResult instance
        """
        return task_backends[self.backend].enqueue(self, args, kwargs)

    async def aenqueue(self, *args: Any, **kwargs: Any) -> TaskResult:
        """
        Queue up the Task to be executed (asynchronous).

        Args:
            *args: Positional arguments for the task function
            **kwargs: Keyword arguments for the task function

        Returns:
            TaskResult instance
        """
        return await task_backends[self.backend].aenqueue(self, args, kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the underlying task function directly."""
        return self.func(*args, **kwargs)

    def call(self, *args: Any, **kwargs: Any) -> Any:
        """Call the underlying task function."""
        return self.django_task.call(*args, **kwargs)

    async def acall(self, *args: Any, **kwargs: Any) -> Any:
        """Asynchronously call the underlying task function."""
        return await self.django_task.acall(*args, **kwargs)

    def get_backend(self):
        """Get the backend instance."""
        return self.django_task.get_backend()


def task(
    function: Callable | None = None,
    *,
    priority: int = 0,
    queue_name: str = "default",
    backend: str = "default",
    takes_context: bool = False,
    unique: bool = False,
    unique_key: str | None = None,
    ttl: int | None = None,
    remove_unique_on_complete: bool = True,
    on_commit: bool = True,
) -> VTask | Callable[[Callable], VTask]:
    """
    Decorator to create a VTask.

    This is a superset of Django's @task decorator, supporting all of Django's
    parameters plus our unique task parameters.

    Args:
        function: The function to decorate (when used as @task)
        priority: Task priority (-100 to 100)
        queue_name: Name of the queue
        backend: Backend alias
        takes_context: Whether the task receives TaskContext as first arg
        unique: Whether to enforce uniqueness
        unique_key: Custom unique key (auto-generated if not provided)
        ttl: Time-to-live for unique lock (seconds)
        remove_unique_on_complete: If True, remove lock on completion (mutex).
                                  If False, let TTL expire (throttle).
        on_commit: If True, enqueue the task only after the current transaction commits.

    Usage:
        @task
        def my_task(arg1, arg2):
            ...

        @task(unique=True, ttl=60, remove_unique_on_complete=False)
        def throttled_task(arg1):
            ...
    """
    from django.tasks import task as django_task

    def wrapper(func: Callable) -> VTask:
        # Create the underlying Django task
        django_task_instance = django_task(
            func,
            priority=priority,
            queue_name=queue_name,
            backend=backend,
            takes_context=takes_context,
        )

        # Wrap it in our VTask
        return VTask(
            django_task=django_task_instance,
            unique=unique,
            unique_key=unique_key,
            ttl=ttl,
            remove_unique_on_complete=remove_unique_on_complete,
            on_commit=on_commit,
        )

    if function is None:
        # Called with arguments: @task(...)
        return wrapper
    else:
        # Called without arguments: @task
        return wrapper(function)
