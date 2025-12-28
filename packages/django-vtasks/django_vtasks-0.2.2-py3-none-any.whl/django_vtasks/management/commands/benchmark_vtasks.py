import asyncio
import subprocess
import sys
import time

from django.core.management.base import BaseCommand
from django.tasks import task_backends

from django_vtasks.worker import Worker


class Command(BaseCommand):
    help = "Benchmark vtasks backend"

    def execute(self, *args, **options):
        if self.requires_system_checks:
            self.check()
        return asyncio.run(self.handle(*args, **options))

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=1000,
            help="Number of tasks to enqueue",
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=50,
            help="Number of concurrent workers",
        )
        parser.add_argument(
            "--backend-alias",
            type=str,
            default="default",
            help="Backend alias to use",
        )
        parser.add_argument(
            "--queue",
            type=str,
            default="default",
            help="Queue to use",
        )
        parser.add_argument(
            "--task-type",
            type=str,
            choices=["noop", "sleep"],
            default="noop",
            help="Task type to benchmark",
        )
        parser.add_argument(
            "--payload-size",
            type=int,
            default=0,
            help="Size of dummy payload in bytes (if > 0)",
        )

    async def handle(self, *args, **options):
        count = options["count"]
        concurrency = options["concurrency"]
        backend_alias = options["backend_alias"]
        queue_name = options["queue"]
        task_type = options["task_type"]
        payload_size = options["payload_size"]

        backend_instance = task_backends[backend_alias]

        # Clear the queue first to ensure clean benchmark
        self.stdout.write("Clearing queue before benchmark...")
        clear_cmd = [
            sys.executable,
            "manage.py",
            "clear_queue",
            f"--backend-alias={backend_alias}",
            f"--queue={queue_name}",
            "--force",
        ]

        try:
            result = subprocess.run(clear_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.stdout.write(self.style.WARNING(f"Failed to clear queue: {result.stderr}"))
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.WARNING("Queue clear command timed out"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to clear queue: {e}"))

        # Import the benchmark tasks
        from benchmarks.tasks import noop, sleep_io

        # Select the task based on task type
        if task_type == "noop":
            benchmark_task = noop
        else:  # sleep
            benchmark_task = sleep_io

        # Generate dummy payload if requested
        dummy_payload = ""
        if payload_size > 0:
            dummy_payload = "x" * payload_size

        self.stdout.write(self.style.SUCCESS("--- vtasks benchmark ---"))
        self.stdout.write(f"Backend: {backend_instance.__class__.__name__}")
        self.stdout.write(f"Backend Alias: {backend_alias}")
        self.stdout.write(f"Count: {count}")
        self.stdout.write(f"Concurrency: {concurrency}")
        self.stdout.write(f"Queue: {queue_name}")
        self.stdout.write(f"Task Type: {task_type}")
        if payload_size > 0:
            self.stdout.write(f"Payload Size: {payload_size} bytes")
        self.stdout.write(self.style.SUCCESS("-" * 30))

        # Double-check that the queue is empty before starting
        queue_depth = await backend_instance.get_queue_depth(queue_name)
        if queue_depth > 0:
            self.stdout.write(
                self.style.WARNING(
                    (
                        f"Queue '{queue_name}' still has {queue_depth} "
                        "tasks after clearing. Continuing anyway..."
                    )
                )
            )

        # Phase 1: Enqueue
        self.stdout.write("Phase 1: Enqueueing tasks...")
        start_time = time.monotonic()

        for i in range(count):
            if task_type == "noop":
                if payload_size > 0:
                    await benchmark_task.aenqueue(dummy_payload, queue_name=queue_name)
                else:
                    await benchmark_task.aenqueue(queue_name=queue_name)
            else:  # sleep
                if payload_size > 0:
                    await benchmark_task.aenqueue(0.1, dummy_payload, queue_name=queue_name)
                else:
                    await benchmark_task.aenqueue(0.1, queue_name=queue_name)

        end_time = time.monotonic()
        enqueue_duration = end_time - start_time
        enqueue_rate = count / enqueue_duration
        self.stdout.write(f"Enqueued {count} tasks in {enqueue_duration:.2f}s ({enqueue_rate:.2f} ops/s)")
        self.stdout.write(self.style.SUCCESS("-" * 30))

        # Phase 2: Processing
        self.stdout.write("Phase 2: Processing tasks...")
        worker = Worker(backend_instance, [queue_name], concurrency)

        start_time = time.monotonic()

        worker_task = asyncio.create_task(worker.run(handle_signals=False))

        # Wait for all tasks to be processed
        while True:
            depth = await backend_instance.get_queue_depth(queue_name)
            if depth == 0:
                # Give a bit of time for the worker to pick up the last tasks
                await asyncio.sleep(0.5)
                depth = await backend_instance.get_queue_depth(queue_name)
                if depth == 0:
                    break
            await asyncio.sleep(0.1)

        # All tasks are fetched, now wait for the worker to finish processing
        await worker.stop()
        await worker_task

        end_time = time.monotonic()
        process_duration = end_time - start_time
        process_rate = count / process_duration

        self.stdout.write(f"Processed {count} tasks in {process_duration:.2f}s ({process_rate:.2f} ops/s)")

        self.stdout.write(self.style.SUCCESS("-" * 30))
        self.stdout.write("FINAL RESULTS:")
        self.stdout.write(f"Backend: {backend_alias}")
        self.stdout.write(f"Concurrency: {concurrency}")
        self.stdout.write(f"Task Type: {task_type}")
        self.stdout.write(f"Enqueue Rate: {enqueue_rate:.2f} ops/s")
        self.stdout.write(f"Process Rate: {process_rate:.2f} ops/s")
