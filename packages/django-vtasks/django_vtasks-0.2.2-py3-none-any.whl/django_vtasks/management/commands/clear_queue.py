import asyncio

from django.core.management.base import BaseCommand, CommandError
from django.tasks import task_backends


class Command(BaseCommand):
    help = "Clear tasks from a queue"

    def execute(self, *args, **options):
        if self.requires_system_checks:
            self.check()
        return asyncio.run(self.handle(*args, **options))

    def add_arguments(self, parser):
        parser.add_argument(
            "--backend-alias",
            type=str,
            default="default",
            help="Backend alias to use (default: default)",
        )
        parser.add_argument(
            "--queue",
            type=str,
            default="default",
            help="Queue name to clear (default: default)",
        )
        parser.add_argument(
            "--all-queues",
            action="store_true",
            help="Clear all queues for the backend",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompt",
        )
        parser.add_argument(
            "--failed",
            action="store_true",
            help="Clear failed tasks (DLQ) instead of regular queue",
        )

    async def handle(self, *args, **options):
        backend_alias = options["backend_alias"]
        queue_name = options["queue"]
        all_queues = options["all_queues"]
        force = options["force"]
        clear_failed = options["failed"]

        try:
            backend_instance = task_backends[backend_alias]
        except KeyError:
            raise CommandError(f"Backend '{backend_alias}' not found in TASKS configuration")

        backend_class_name = backend_instance.__class__.__name__

        if all_queues and not clear_failed:
            if not force:
                self.stdout.write(
                    self.style.WARNING(
                        (f"This will clear ALL queues for backend '{backend_alias}' ({backend_class_name})")
                    )
                )
                confirm = input("Are you sure? Type 'yes' to continue: ")
                if confirm.lower() != "yes":
                    self.stdout.write("Operation cancelled.")
                    return

            await self._clear_all_queues(backend_instance, backend_alias)
        elif clear_failed:
            if not force:
                self.stdout.write(
                    self.style.WARNING(
                        (
                            "This will clear failed tasks (DLQ) for "
                            f"backend '{backend_alias}' ({backend_class_name})"
                        )
                    )
                )
                confirm = input("Are you sure? Type 'yes' to continue: ")
                if confirm.lower() != "yes":
                    self.stdout.write("Operation cancelled.")
                    return

            await self._clear_failed_queue(backend_instance, backend_alias)
        else:
            # Clear specific queue
            if not force:
                depth = await backend_instance.get_queue_depth(queue_name)
                if depth == 0:
                    self.stdout.write(f"Queue '{queue_name}' is already empty.")
                    return

                self.stdout.write(
                    self.style.WARNING(
                        f"This will clear {depth} tasks from queue '{queue_name}' "
                        f"on backend '{backend_alias}' ({backend_class_name})"
                    )
                )
                confirm = input("Are you sure? Type 'yes' to continue: ")
                if confirm.lower() != "yes":
                    self.stdout.write("Operation cancelled.")
                    return

            await self._clear_single_queue(backend_instance, queue_name, backend_alias)

    async def _clear_single_queue(self, backend_instance, queue_name, backend_alias):
        """Clear a single queue."""
        depth_before = await backend_instance.get_queue_depth(queue_name)

        if depth_before == 0:
            self.stdout.write(f"Queue '{queue_name}' is already empty.")
            return

        # Clear the queue using backend-specific method
        if hasattr(backend_instance, "_clear_queue"):
            await backend_instance._clear_queue(queue_name)
        else:
            # Fallback: Use backend-specific clearing logic
            if backend_instance.__class__.__name__ == "DatabaseTaskBackend":
                await self._clear_postgres_queue(backend_instance, queue_name)
            elif backend_instance.__class__.__name__ == "ValkeyTaskBackend":
                await self._clear_valkey_queue(backend_instance, queue_name)
            else:
                raise CommandError(
                    f"Queue clearing not implemented for {backend_instance.__class__.__name__}"
                )

        depth_after = await backend_instance.get_queue_depth(queue_name)
        cleared_count = depth_before - depth_after

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Cleared {cleared_count} tasks from queue '{queue_name}' on backend '{backend_alias}'"
            )
        )

    async def _clear_postgres_queue(self, backend_instance, queue_name):
        """Clear a Postgres queue by deleting all queued tasks."""
        from asgiref.sync import sync_to_async

        from django_vtasks.db.models import QueuedTask, TaskStatus

        @sync_to_async
        def delete_tasks():
            return QueuedTask.objects.filter(queue=queue_name, status=TaskStatus.QUEUED).delete()

        await delete_tasks()

    async def _clear_valkey_queue(self, backend_instance, queue_name):
        """Clear a Valkey queue by deleting the queue key."""
        await backend_instance.client.delete(f"q:{queue_name}")

    async def _clear_all_queues(self, backend_instance, backend_alias):
        """Clear all queues for a backend."""
        if backend_instance.__class__.__name__ == "DatabaseTaskBackend":
            await self._clear_all_postgres_queues(backend_instance)
        elif backend_instance.__class__.__name__ == "ValkeyTaskBackend":
            await self._clear_all_valkey_queues(backend_instance)
        else:
            raise CommandError(f"Clear all queues not implemented for {backend_instance.__class__.__name__}")

        self.stdout.write(self.style.SUCCESS(f"✅ Cleared all queues for backend '{backend_alias}'"))

    async def _clear_all_postgres_queues(self, backend_instance):
        """Clear all Postgres queues."""
        from asgiref.sync import sync_to_async

        from django_vtasks.db.models import QueuedTask, TaskStatus

        @sync_to_async
        def delete_all_tasks():
            return QueuedTask.objects.filter(status=TaskStatus.QUEUED).delete()

        await delete_all_tasks()

    async def _clear_all_valkey_queues(self, backend_instance):
        """Clear all Valkey queues by finding and deleting queue keys."""
        # Find all queue keys (q:*)
        keys = await backend_instance.client.keys("q:*")
        if keys:
            await backend_instance.client.delete(*keys)

    async def _clear_failed_queue(self, backend_instance, backend_alias):
        """Clear the failed tasks queue (DLQ)."""
        if backend_instance.__class__.__name__ == "DatabaseTaskBackend":
            await self._clear_postgres_failed_queue(backend_instance)
        elif backend_instance.__class__.__name__ == "ValkeyTaskBackend":
            await self._clear_valkey_failed_queue(backend_instance)
        else:
            raise CommandError(
                f"Clear failed queue not implemented for {backend_instance.__class__.__name__}"
            )

        self.stdout.write(self.style.SUCCESS(f"✅ Cleared failed tasks for backend '{backend_alias}'"))

    async def _clear_postgres_failed_queue(self, backend_instance):
        """Clear failed tasks in Postgres."""
        from asgiref.sync import sync_to_async

        from django_vtasks.db.models import QueuedTask, TaskStatus

        @sync_to_async
        def delete_failed_tasks():
            return QueuedTask.objects.filter(status=TaskStatus.FAILED).delete()

        await delete_failed_tasks()

    async def _clear_valkey_failed_queue(self, backend_instance):
        """Clear failed tasks in Valkey."""
        await backend_instance.client.delete("q:failed")
