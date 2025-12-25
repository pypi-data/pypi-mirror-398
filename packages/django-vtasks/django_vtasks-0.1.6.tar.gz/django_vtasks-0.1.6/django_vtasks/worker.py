import asyncio
import logging
import signal
import time
import traceback as tb
from importlib import import_module

from django_vtasks.backends.base import BaseTaskBackend

from .conf import settings
from .signals import task_failure, task_finished, task_started

logger = logging.getLogger(__name__)


class Worker:
    def __init__(
        self,
        backend: "BaseTaskBackend",
        queues: list[str] | None = None,
        concurrency: int | None = None,
        batch_config: dict[str, dict] | None = None,
    ) -> None:
        self.backend = backend
        self.queues = queues or settings.VTASKS_QUEUES
        self.concurrency = concurrency or settings.VTASKS_CONCURRENCY
        self.batch_config = batch_config or settings.VTASKS_BATCH_QUEUES
        self.running = False
        self.sem: asyncio.Semaphore | None = None

    async def run(self, handle_signals: bool = True, run_once: bool = False) -> None:
        try:
            import uvloop

            uvloop.install()
            logger.info("uvloop installed.")
        except ImportError:
            logger.info("uvloop not found, using default asyncio event loop.")

        if self.running:
            return

        self.sem = asyncio.Semaphore(self.concurrency)
        self.running = True
        loop = asyncio.get_running_loop()

        logger.info(
            "Starting worker with concurrency=%d, queues=%s, backend=%s",
            self.concurrency,
            self.queues,
            self.backend.__class__.__name__,
        )

        if handle_signals:

            def _stop_signal_handler() -> None:
                asyncio.create_task(self.stop())

            loop.add_signal_handler(signal.SIGINT, _stop_signal_handler)
            loop.add_signal_handler(signal.SIGTERM, _stop_signal_handler)

        await self.backend._rescue_tasks()

        try:
            sleep_time = 0.1
            while self.running:
                for queue in self.queues:
                    await self.sem.acquire()
                    if not self.running:
                        self.sem.release()
                        break

                    batch_options = self.batch_config.get(queue)
                    if batch_options:
                        tasks = await self.backend.fetch_batch(
                            queue, batch_options["count"], batch_options["timeout"]
                        )
                        if tasks:
                            asyncio.create_task(self.process_batch(tasks, queue))
                            sleep_time = 0.1
                        else:
                            self.sem.release()
                            logger.debug("No tasks found in queue %s", queue)
                            await asyncio.sleep(sleep_time)
                            sleep_time = min(sleep_time * 2, 1)
                    else:
                        task = await self.backend._fetch_task([queue])
                        if task:
                            asyncio.create_task(self.process_task(task))
                            sleep_time = 0.1
                        else:
                            self.sem.release()
                            logger.debug("No tasks found in queue %s", queue)
                            await asyncio.sleep(sleep_time)
                            sleep_time = min(sleep_time * 2, 1)
                if not self.running:
                    break

                if run_once:
                    self.running = False
        finally:
            logger.info("Waiting for active tasks to finish...")
            if self.sem:
                for _ in range(self.concurrency):
                    await self.sem.acquire()
                for _ in range(self.concurrency):
                    self.sem.release()
            logger.info("Worker stopped.")

    async def stop(self) -> None:
        if not self.running:
            return

        logger.info("Shutting down worker...")
        self.running = False

    async def process_batch(self, tasks: list[dict], queue: str) -> None:
        start_time = time.monotonic()
        task_ids = [task.get("id", "unknown") for task in tasks]
        logger.info(
            "Processing batch of %d tasks from queue %s: %s",
            len(tasks),
            queue,
            task_ids,
        )
        try:
            batch_task_path = self.batch_config[queue]["task"]
            module_path, func_name = batch_task_path.rsplit(".", 1)
            module = import_module(module_path)
            func = getattr(module, func_name).func

            if asyncio.iscoroutinefunction(func):
                await func(tasks)
            else:
                await asyncio.to_thread(func, tasks)

            await self.backend._ack_batch(tasks)
            duration = time.monotonic() - start_time
            logger.info(
                "Finished processing batch of %d tasks in %.4fs", len(tasks), duration
            )
        except Exception as e:
            logger.error("Failed to process batch for queue %s", queue, exc_info=True)
            for task in tasks:
                await self.backend._fail_task(task, e)
        finally:
            if self.sem:
                self.sem.release()

    async def process_task(self, task_data: dict) -> None:
        start_time = time.monotonic()
        task_id = task_data.get("id", "unknown")
        func_path = task_data.get("func", "unknown")
        logger.info("Processing task %s: %s", task_id, func_path)
        try:
            try:
                task_started.send(
                    sender=self.__class__,
                    task_id=task_id,
                    name=func_path,
                    args=task_data.get("args"),
                    kwargs=task_data.get("kwargs"),
                )
            except Exception:
                logger.exception("Error sending task_started signal")

            module_path, func_name = task_data["func"].rsplit(".", 1)
            module = import_module(module_path)
            func = getattr(module, func_name).func

            # Filter out internal kwargs
            filtered_kwargs = {
                k: v
                for k, v in task_data["kwargs"].items()
                if k
                not in [
                    "queue_name",
                    "unique",
                    "unique_key",
                    "ttl",
                    "remove_unique_on_complete",
                ]
            }

            if asyncio.iscoroutinefunction(func):
                await func(*task_data["args"], **filtered_kwargs)
            else:
                await asyncio.to_thread(func, *task_data["args"], **filtered_kwargs)

            await self.backend._ack_task(task_data)
            duration = time.monotonic() - start_time
            logger.info("Task %s finished in %.4fs", task_id, duration)

            try:
                task_finished.send(
                    sender=self.__class__,
                    task_id=task_id,
                    name=func_path,
                    duration=duration,
                )
            except Exception:
                logger.exception("Error sending task_finished signal")
        except Exception as e:
            logger.error("Task %s failed", task_id, exc_info=True)
            await self.backend._fail_task(task_data, e)

            try:
                task_failure.send(
                    sender=self.__class__,
                    task_id=task_id,
                    name=func_path,
                    exception=e,
                    traceback=tb.format_exc(),
                )
            except Exception:
                logger.exception("Error sending task_failure signal")
        finally:
            if self.sem:
                self.sem.release()
