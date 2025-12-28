import asyncio
import logging
from datetime import datetime
from importlib import import_module

from croniter import croniter
from django.utils import timezone

from .backends.base import VTasksBaseBackend


def crontab(
    minute: str = "*",
    hour: str = "*",
    day_of_week: str = "*",
    day_of_month: str = "*",
    month_of_year: str = "*",
) -> str:
    """
    A celery-like crontab schedule generator
    """
    cron_format = f"{minute} {hour} {day_of_month} {month_of_year} {day_of_week}"
    if not croniter.is_valid(cron_format):
        raise ValueError("Invalid cron format")
    return cron_format


logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, backend: "VTasksBaseBackend", schedule: dict) -> None:
        self.backend = backend
        self.schedule = schedule
        self.running = False

    async def run(self, run_once: bool = False) -> None:
        if self.running:
            return

        self.running = True
        logger.debug("Scheduler starting with schedule: %s", self.schedule)
        logger.info("Scheduler started.")

        while self.running:
            logger.debug("Acquiring scheduler lock...")
            if not await self.backend.acquire_lock("vtasks_scheduler_lock", ttl=15):
                await asyncio.sleep(5)  # Wait before trying to acquire the lock again
                if run_once:
                    self.running = False
                continue

            logger.debug("Scheduler lock acquired.")
            now = timezone.now()

            for task_name, task_config in self.schedule.items():
                last_run_key = f"vtasks_last_run:{task_name}"
                last_run_str = await self.backend.get_metadata(last_run_key)
                last_run = (
                    datetime.fromtimestamp(float(last_run_str), tz=timezone.UTC) if last_run_str else None
                )
                schedule = task_config["schedule"]
                logger.debug(
                    "Checking task '%s'",
                    task_name,
                )

                should_run = False
                if isinstance(schedule, str):  # Cron schedule
                    if last_run:
                        itr = croniter(schedule, last_run)
                        next_run = itr.get_next(datetime)
                    else:
                        itr = croniter(schedule, now)
                        next_run = itr.get_prev(datetime)

                    if next_run <= now:
                        should_run = True
                elif isinstance(schedule, int):  # Interval schedule
                    last_run_ts = last_run.timestamp() if last_run else 0
                    if (now.timestamp() - last_run_ts) >= schedule:
                        should_run = True

                if should_run:
                    logger.debug("Task '%s' is due to run.", task_name)
                    logger.info("Enqueuing due task: %s", task_name)
                    try:
                        module_path, func_name = task_config["task"].rsplit(".", 1)
                        module = import_module(module_path)
                        task_func = getattr(module, func_name)

                        # Enqueue the task
                        await self.backend.aenqueue(task_func, (), {})
                        await self.backend.set_metadata(last_run_key, str(now.timestamp()))
                    except Exception:
                        logger.error("Error scheduling task %s", task_name, exc_info=True)

            if run_once:
                self.running = False

            await asyncio.sleep(1)  # Check schedule every 1 second

        logger.info("Scheduler stopped.")

    async def stop(self) -> None:
        if not self.running:
            return
        logger.info("Shutting down scheduler...")
        self.running = False
