import asyncio
import logging

from django.tasks import task_backends

from .conf import settings
from .scheduler import Scheduler
from .worker import Worker


def get_worker_application(django_app):
    worker_instance = None
    scheduler_instance = None

    async def asgi(scope, receive, send):
        nonlocal worker_instance, scheduler_instance

        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    try:
                        # Instantiate worker
                        backend = task_backends["default"]

                        worker_instance = Worker(
                            backend=backend,
                            concurrency=settings.VTASKS_CONCURRENCY,
                            queues=settings.VTASKS_QUEUES,
                            batch_config=settings.VTASKS_BATCH_QUEUES,
                        )

                        # Run worker in the background
                        asyncio.create_task(worker_instance.run(handle_signals=False))

                        # Instantiate and run scheduler if enabled
                        if settings.VTASKS_RUN_SCHEDULER:
                            if settings.VTASKS_SCHEDULE:
                                scheduler_instance = Scheduler(
                                    backend=backend, schedule=settings.VTASKS_SCHEDULE
                                )
                                asyncio.create_task(scheduler_instance.run())

                        await send({"type": "lifespan.startup.complete"})
                    except Exception as e:
                        logging.error(
                            "Worker/Scheduler startup failed: %s", e, exc_info=True
                        )
                        await send(
                            {"type": "lifespan.startup.failed", "message": str(e)}
                        )

                elif message["type"] == "lifespan.shutdown":
                    try:
                        if worker_instance:
                            await worker_instance.stop()
                        if scheduler_instance:
                            await scheduler_instance.stop()
                        await send({"type": "lifespan.shutdown.complete"})
                    except Exception as e:
                        logging.error(
                            "Worker/Scheduler shutdown failed: %s", e, exc_info=True
                        )
                        await send(
                            {"type": "lifespan.shutdown.failed", "message": str(e)}
                        )
                    return
        else:
            await django_app(scope, receive, send)

    return asgi
