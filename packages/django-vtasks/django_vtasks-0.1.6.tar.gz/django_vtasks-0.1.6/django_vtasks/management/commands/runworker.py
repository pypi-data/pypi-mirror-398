import asyncio
import logging
import re
import signal
from importlib import metadata

from django.core.management.base import BaseCommand
from django.tasks import task_backends

from django_vtasks.conf import settings
from django_vtasks.scheduler import Scheduler
from django_vtasks.worker import Worker

logger = logging.getLogger("django_vtasks.worker")


def _get_version():
    try:
        return metadata.version("django-vtasks")
    except metadata.PackageNotFoundError:
        # For development, try to read from pyproject.toml
        try:
            with open("pyproject.toml", "r") as f:
                content = f.read()
            version_match = re.search(r'version = "(.*?)"', content)
            if version_match:
                return version_match.group(1)
        except FileNotFoundError:
            return "unknown"
    return "unknown"


class Command(BaseCommand):
    requires_system_checks = []  # Save memory

    def add_arguments(self, parser):
        parser.add_argument(
            "--queue",
            action="append",
            default=None,
            help="Queue to process",
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=settings.VTASKS_CONCURRENCY,
            help="Number of concurrent workers",
        )
        parser.add_argument(
            "--backend",
            type=str,
            default="default",
            help="Backend to use",
        )
        parser.add_argument(
            "--scheduler",
            action="store_true",
            help="Run scheduler",
        )
        parser.add_argument(
            "--id",
            type=str,
            default=None,
            help="Worker ID to use",
        )

    def handle(self, *args, **options):
        backend = task_backends[options["backend"]]
        if options["id"]:
            backend.worker_id = options["id"]
        queues = options["queue"] or settings.VTASKS_QUEUES
        concurrency = options["concurrency"]

        version = _get_version()

        banner = f"\ndjango-vtasks v{version}\n"

        # Get broker URL and redact password
        broker_url = f"db+{backend.alias}"
        if "valkey" in backend.__class__.__name__.lower():
            raw_url = backend.options.get("BROKER_URL", "valkey://localhost:6379/0")
            broker_url = re.sub(r"://[^@]+@", "://:********@", raw_url)

        banner += f"\n- **Backend**: {backend.__class__.__name__}"
        banner += f"\n- **Broker**: {broker_url}"
        banner += f"\n- **Concurrency**: {concurrency}"
        banner += f"\n- **Queues**: {', '.join(queues)}"
        if options["scheduler"]:
            banner += "\n- **Scheduler**: Enabled"

        logger.info(banner)

        try:
            import uvloop

            uvloop.install()
        except ImportError:
            pass

        worker = Worker(
            backend,
            queues,
            concurrency,
            batch_config=settings.VTASKS_BATCH_QUEUES,
        )

        scheduler = None
        if options["scheduler"]:
            if settings.VTASKS_SCHEDULE:
                scheduler = Scheduler(
                    backend=backend, schedule=settings.VTASKS_SCHEDULE
                )

        async def main():
            loop = asyncio.get_running_loop()
            stop_event = asyncio.Event()

            def _signal_handler():
                print("Signal received, stopping...")
                stop_event.set()

            loop.add_signal_handler(signal.SIGINT, _signal_handler)
            loop.add_signal_handler(signal.SIGTERM, _signal_handler)

            worker_task = asyncio.create_task(worker.run(handle_signals=False))

            scheduler_task = None
            if scheduler:
                scheduler_task = asyncio.create_task(scheduler.run())

            await stop_event.wait()
            print("Stop event received.")

            print("Stopping scheduler...")
            if scheduler:
                await scheduler.stop()
            print("Scheduler stop called.")

            print("Stopping worker...")
            await worker.stop()
            print("Worker stop called.")

            print("Waiting for tasks to finish...")
            if scheduler_task:
                await scheduler_task

            await worker_task
            print("All tasks finished.")

        asyncio.run(main())
