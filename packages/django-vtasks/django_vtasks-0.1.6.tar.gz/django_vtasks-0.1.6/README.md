# django-vtasks

**Valkey Tasks. Very Fast Tasks.**

From the team at [GlitchTip](https://glitchtip.com), `django-vtasks` is a lightweight, async-first task queue for Django 6.0+, designed to bridge the gap between simplicity (database-backed) and raw performance (Valkey-backed).

**Status**: Feature complete. Alpha quality. Breaking changes may be introduced at any time. Once we hit 1.0, we'll switch to semantic versioning and release a change log.

## When to use django-vtasks

Adopting `django-vtasks` is a good choice when:

*   You are using Django 6.0+ and want to leverage modern `asyncio`.
*   You want a "Hybrid" strategy: Start with Postgres (Less-Infra) and switch to Valkey/Redis (High-Throughput) without rewriting task code.
*   You care about efficiency: You want to handle thousands of concurrent I/O-bound tasks in a single process/container.

It might **not** be the ideal option if:

*   You need complex workflow primitives (Chains, Chords, Groups) -> Use [Celery](https://docs.celeryq.dev/en/stable/).
*   You need to store Task Results (this library is strictly Fire-and-Forget). Consider [django-tasks](https://github.com/RealOrangeOne/django-tasks)
*   You rely on brokers other than Valkey or Postgres (e.g., SQS, RabbitMQ).

## Features

*   **Async First:** Native `asyncio` worker for high-performance I/O. Sync fallback for synchronous tasks (via asyncio.to_thread). Worker can run standalone or be embedded into existing asyncio loop.
*   **Dual Backends:**
    *   **Database:** Simple, zero-infrastructure setup. Best with Postgres.
    *   **Valkey:** High-throughput, low-latency using atomic `BLMOVE`. Compatible with Redis.
*   **Batch Processing:** Optional, explicit batching for high-throughput queues.
*   **Scheduled Tasks:** Schedule tasks to run at a specific time or interval, using cron syntax.
*   **Unique tasks** Ensure tasks runs just once using `unique` kwarg. Allows for Mutex/Debounce patterns. 
*   **Compression:** Automatic [Zstandard](https://github.com/indygreg/python-zstandard) compression for large payloads (>1KB).
*   **Serialization:** Uses `orjson`. `datetime` and `UUID` are supported (converted to strings). Tuples become lists.
*   **Reliability:** Fail-fast DLQ with capped history for failed tasks.
*   **Lightweight:** Minimal dependencies and a simple, modern codebase.
*   **Admin** View in-progress and failed tasks via Django admin interface, even for valkey backend.

![Admin Interface](/docs/admin.png)

### Backend Features

| Feature | `DatabaseTaskBackend` (PostgreSQL) | `DatabaseTaskBackend` (SQLite) | `DatabaseTaskBackend` (MySQL) | `ValkeyTaskBackend` |
| :--- | :---: | :---: | :---: | :---: |
| **Concurrent Workers** | ✅ | ⚠️ (1 at a time) | ✅ | ✅ |
| **Unique (Mutex)** | ✅ | ✅ | ❌ | ✅ |
| **Throttling** | ❌ | ❌ | ❌ | ✅ |

> **Note on Concurrency:** The `DatabaseTaskBackend` relies on `SELECT ... FOR UPDATE SKIP LOCKED` for efficient parallel processing. SQLite and older versions of MySQL do not support this feature, which means that only one worker can process tasks from the queue at a time.

## Requirements

*   Python 3.12+
*   Django 6.0+
*   Valkey backend requires Valkey 7+ (or Redis 7+)

## Installation

Install the core `django-vtasks` library:

```bash
pip install "django-vtasks"
```

or with uv

```bash
uv add "django-vtasks"
```

Optional dependencies:

```bash
uv add "django-vtasks[valkey]"
```

## Configuration

-   `VTASKS_VALKEY_PREFIX`: A string prefix for all Valkey keys, to provide namespace isolation. Defaults to `"vt"`.

### Database Backend

```python
INSTALLED_APPS = [
    # ...
    "django_vtasks",
    "django_vtasks.db", # Required for the Database backend
]

TASKS = {
    "default": {
        "BACKEND": "django_vtasks.backends.db.DatabaseTaskBackend",
    }
}
```

### Valkey Backend

This is the simplest way to configure the Valkey backend.

```python
INSTALLED_APPS = [
    # ...
    "django_vtasks",
]

TASKS = {
    "default": {
        "BACKEND": "django_vtasks.backends.valkey.ValkeyTaskBackend",
        "OPTIONS": {
            "BROKER_URL": "valkey://localhost:6379/0",
        }
    }
}
```

**Alternative: Shared Cache Connection**

For applications that already use a compatible cache backend like `django-vcache`,
you can share the existing connections to minimize resource usage.
Compatibility requires the cache to implement

`get_raw_client(async_client: bool)`

`django-vtasks` will borrow the raw Valkey clients from the cache, avoiding the
need to create new connections.

```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django_vcache.backend.ValkeyCache",
        "LOCATION": "valkey://localhost:6379/1",
    },
}

TASKS = {
    "default": {
        "BACKEND": "django_vtasks.backends.valkey.ValkeyTaskBackend",
        "OPTIONS": {
            "cache_alias": "default",
        }
    }
}
```

**Alternative: Shared `valkey-py` Connection Pool**

For applications that already use `valkey-py`, you can share an existing `valkey.asyncio.ConnectionPool` to minimize TCP connections.

When using a shared pool, you **must still provide a `BROKER_URL`**. This is required for synchronous operations like `task.enqueue()` which cannot use an asynchronous connection pool.

```python
import valkey.asyncio as valkey

MY_APP_VALKEY_POOL = valkey.ConnectionPool.from_url("valkey://localhost:6379/0")

INSTALLED_APPS = [
    # ...
    "django_vtasks",
]

TASKS = {
    "default": {
        "BACKEND": "django_vtasks.backends.valkey.ValkeyTaskBackend",
        "OPTIONS": {
            "CONNECTION_POOL": MY_APP_VALKEY_POOL,
            "BROKER_URL": "valkey://localhost:6379/0",
        }
    }
}
```

## Usage

### Defining Tasks
Create a `tasks.py` in your Django app.

```python
# my_app/tasks.py
from django_vtasks import task
from my_app.models import User

@task
def send_welcome_email(user_id):
    user = User.objects.get(id=user_id)
    # Your email logic here
    print(f"Sent welcome email to {user.email}")
```

You may also use `from django.tasks import task` however this will not allow for any unique django-vtasks features like unique.

### Enqueueing Tasks

Both sync and async contexts are supported.
async will perform better as it will take full advantage of the asyncio loop.

```python
from django.http import HttpResponse
from .tasks import send_welcome_email

def register_sync(request):
    user = User.objects.create(...)
    send_welcome_email.enqueue(user.id)
    return HttpResponse("User created.")

async def register_async(request):
    user = await User.objects.acreate(...)
    await send_welcome_email.aenqueue(user.id)
    return HttpResponse("User created.")
```

### Bulk Enqueueing

For high-performance scenarios where you need to dispatch a large number of tasks at once, `enqueue_many` and `aenqueue_many` provide an optimized way to send tasks in a single network request per queue.

This is significantly more performant than enqueueing tasks in a loop. The implementation uses Valkey's variadic `LPUSH` and Postgres's `bulk_create` for maximum efficiency.

The methods accept a list of tuples, where each tuple contains `(task_function, args, kwargs)`. The `queue_name` can be specified in the `kwargs` for each task.

```python
from .tasks import process_user, cleanup_job
from django.tasks import task_backends

async def dispatch_many_tasks(request):
    tasks_to_send = [
        # (task, args, kwargs)
        (process_user, (user1.id,), {}),
        (process_user, (user2.id,), {}),
        (cleanup_job, (), {"queue_name": "low_priority"}),
    ]
    
    # Use aenqueue_many in async contexts
    await task_backends["default"].aenqueue_many(tasks_to_send)

    # Use enqueue_many in sync contexts, usually within a transaction
    # from django.db import transaction
    # with transaction.atomic():
    #     task_backends["default"].enqueue_many(tasks_to_send)

    return HttpResponse("Dispatched many tasks.")
```
The tasks are automatically grouped by queue name (`default` and `low_priority` in this example) and sent in optimized batches.
Ensure your task function accepts a list of tasks.

```python
@task
def process_widgets_batch(tasks: list):
    # You could use "if isinstance(tasks, list):" for batch and non-batch compatibility.
    for task in tasks:
        process_widget(task)
```

### Unique Tasks

To prevent duplicate tasks from being enqueued, use the `.using()` method with the `unique` parameter. This is useful for tasks that should only be running once at a time.

```python
from .tasks import send_welcome_email

# This task will only be enqueued if no other task with the same
# function, args, and kwargs is currently in the queue or running.
await send_welcome_email.using(unique=True).aenqueue(user.id)
```

You can also provide a custom `unique_key` to control how uniqueness is determined.

```python
# This task will only be enqueued if no other task with the unique_key="user-welcome"
# is currently in the queue or running.
await send_welcome_email.using(
    unique=True,
    unique_key="user-welcome"
).aenqueue(user.id)
```

The `unique` parameter supports two modes: **Mutex** and **Throttling**.

-   **Mutex (default):** The lock is released as soon as the task is finished. This is the default behavior.
-   **Throttling:** The lock is held for a specified `ttl` (time-to-live) in seconds, even after the task is finished. This is useful for rate-limiting tasks.

```python
# This task will only be enqueued if no other task with the same
# unique_key has been enqueued in the last 60 seconds.
await send_welcome_email.using(
    unique=True,
    unique_key="user-welcome-throttle",
    ttl=60,
    remove_unique_on_complete=False,
).aenqueue(user.id)
```

**Handling Rejections:**

The `.using()` syntax returns `None` when a task is rejected due to uniqueness:

```python
result = await send_welcome_email.using(unique=True).aenqueue(user.id)
if result is None:
    # Task was rejected (duplicate found)
    print("Email already being sent")
else:
    # Task was enqueued successfully
    print(f"Email queued: {result.id}")
```

**Backend Support:**

-   **Database:** Supports **Mutex** only. `remove_unique_on_complete=False` is not supported.
-   **Valkey:** Supports both **Mutex** and **Throttling**.

> **Note:** The `unique` feature is not supported when using the `Database` backend with MySQL, as MySQL does not support conditional unique constraints.

### Periodic Tasks

`django-vtasks` supports periodic tasks using cron-style schedules.

```python
# settings.py
from django_vtasks.scheduler import crontab

VTASKS_SCHEDULE = {
    "daily_report": {
        "task": "myapp.tasks.report",
        "schedule": crontab(hour=5, minute=0),  # Runs at 5:00 AM
    },
    "cleanup": {
        "task": "myapp.tasks.cleanup",
        "schedule": 3600,  # Runs every hour
    },
}
```

To run the scheduler, use the `runworker` command with the `--scheduler` flag.

```bash
python manage.py runworker --scheduler
```

> **Note on Scheduler Reliability:** To prevent periodic tasks from being enqueued multiple times, the scheduler uses a locking mechanism that relies on features only available in certain backends. For PostgreSQL, this is implemented using a highly efficient, native transaction-scoped advisory lock (`pg_try_advisory_xact_lock`). For other supported database backends (MySQL), it is emulated by locking a row in a metadata table. For deployments running multiple scheduler instances (e.g., multiple `runworker --scheduler` processes), you **must** use one of the following backends to ensure safety:
> - `ValkeyTaskBackend`
> - `DatabaseTaskBackend` with **PostgreSQL** or **MySQL**
>
> Using the `DatabaseTaskBackend` with SQLite is **not safe** for running more than one scheduler instance and may result in duplicate task runs.


## Batch Processing

For high-throughput scenarios, consider batching. This allows the worker to fetch multiple tasks at once and process them in a single function call. Your task function must accept the tasks being passed as a list.

### 1. Configure a Batch Queue

In your `settings.py`, define a batch queue using `VTASKS_BATCH_QUEUES`. The `task` key is required and must point to the function that will process the collected batch.

```python
# settings.py

VTASKS_BATCH_QUEUES = {
    "batch_queue": {
        "task": "sample.tasks.process_widgets_batch",  # Task to process the batch
        "count": 100,  # Max number of tasks to fetch at once
        "timeout": 5.0,  # Max time to wait for tasks
    }
}
```

### 2. Create a Batch Processing Task

The task function specified in the `task` key of the configuration must accept a single argument: a list of task dictionaries.

```python
# sample/tasks.py
from django.tasks import task

@task
def process_widgets_batch(tasks: list):
    """Processes a batch of widgets."""
    print(f"Processing a batch of {len(tasks)} widgets.")
    widget_ids = [task["kwargs"]["widget_id"] for task in tasks]
    # Your batch processing logic here
    print(f"  - Processing widget IDs: {widget_ids}")

@task
def single_widget_task(widget_id: int):
    """A dummy task to be processed in a batch."""
    pass
```

### 3. Enqueue Tasks to the Batch Queue

Enqueue individual tasks to the batch queue as you normally would. The worker will automatically group them into batches.

```python
# Enqueueing multiple tasks to the batch_queue
for i in range(10):
    single_widget_task.using(queue_name="batch_queue").enqueue(widget_id=i)
```

The `batch_worker` will fetch up to `100` tasks from `batch_queue`, and then call `process_widgets_batch` with the list of these tasks.

## Deployment

### Standalone Worker

For traditional deployments, you can run one or more standalone worker processes. This is the most robust and scalable option.

The worker uses a bounded semaphore to handle concurrency safely.

```bash
# Run a worker with default settings
python manage.py runworker

# Run with specific concurrency and queues
python manage.py runworker --concurrency 100 --queue high_priority --queue default

# Run a worker for a batch queue
python manage.py runworker --queue=batch_queue
```

### Optimization

It's possible to reduce worker memory by removing unneeded INSTALLED_APPS from your worker. In settings.py:

```python
if os.environ.get("VTASKS_IS_WORKER") == "true":
    INSTALLED_APPS = prune_installed_apps(INSTALLED_APPS)
    ROOT_URLCONF = "django_vtasks.empty_urls"  # Omit if tasks require "reverse"
```

Ensure you set VTASKS_IS_WORKER to "true" in your environment variables.

**Scaling and Reliability:**

It is safe to run multiple standalone worker instances. Both the Postgres (`SKIP LOCKED`) and Valkey (`BLMOVE`) backends use atomic operations to prevent multiple workers from picking up the same task.

Each worker has a unique ID. If a worker process is terminated uncleanly, its in-process tasks will be abandoned. On startup, a worker will attempt to rescue any tasks that were previously abandoned *by a worker with the same ID*.

### Embedded Worker (All-in-One)

For simpler deployments or "light scaling" needs, you can run the worker inside your ASGI web server's event loop. This "All-in-One" setup is efficient and reduces the number of processes you need to manage.

This is achieved by wrapping your main Django ASGI application.

**1. Create an embedded ASGI entrypoint:**

```python
# sample/asgi_embedded.py
import os
from django.core.asgi import get_asgi_application
from django_vtasks.asgi import get_worker_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sample.settings")

# Get the standard Django ASGI application
django_asgi_app = get_asgi_application()

# Wrap it with the worker application
application = get_worker_application(django_asgi_app)
```

**2. Run with an ASGI Server (e.g., Granian):**

You can then run this application with any ASGI-compliant server that supports the `lifespan` protocol.

```bash
# Example with Granian
granian --interface asgi sample.asgi_embedded:application --host 0.0.0.0 --port 8000
```

**Scaling:**

You can run multiple instances of this "All-in-One" configuration. Each web server process will have its own embedded worker, and they will safely coordinate through the shared backend (Postgres or Valkey). This is a simple way to achieve horizontal scaling for both web and task processing.


## Testing Your Application

For unit and integration tests, it's often useful to execute tasks immediately without a running worker. `django-vtasks` provides a custom "immediate" backend that is fully compatible with `vtasks` features.

To use it in your tests, override the `TASKS` setting:

```python
# your_app/tests.py or your test settings file

from django.test import TestCase, override_settings

@override_settings(
    TASKS={
        "default": {
            "BACKEND": "django_vtasks.backends.immediate.ImmediateBackend",
        }
    }
)
class MyTaskTests(TestCase):
    def test_something(self):
        # Tasks enqueued here will run immediately and synchronously.
        my_task.enqueue()
        # ... your assertions
```

This backend ensures that even tasks using `vtasks`-specific features (like `unique=True`) can be tested seamlessly. The `unique` parameters will be accepted but ignored, as there is no queue in immediate mode.

### Testing Batch Tasks

The `ImmediateBackend` provides a simulation layer for testing batch processing without a running worker. When tasks are enqueued to a queue defined in `VTASKS_BATCH_QUEUES`, they are not executed immediately. Instead, they are stored in memory.

To process the stored tasks, you must manually call `flush_batch()` or `flush_batches()` on the backend instance.

```python
# your_app/tests.py
from django.test import TestCase, override_settings
from django.tasks import task_backends
from .tasks import single_widget_task, process_widgets_batch # Assuming these are defined

@override_settings(
    TASKS={
        "default": {
            "BACKEND": "django_vtasks.backends.immediate.ImmediateBackend",
        }
    },
    VTASKS_BATCH_QUEUES={
        "batch_queue": {"task": "your_app.tasks.process_widgets_batch"}
    }
)
class MyBatchingTest(TestCase):
    def test_batching_simulation(self):
        backend = task_backends["default"]

        # Enqueue tasks to the batch queue. They will be stored, not executed.
        for i in range(5):
            single_widget_task.using(queue_name="batch_queue").enqueue(widget_id=i)

        # Assert that the tasks are pending in the backend's memory
        self.assertEqual(len(backend.pending_batches["batch_queue"]), 5)

        # Manually trigger the batch processor
        backend.flush_batch("batch_queue")

        # Now, you can assert that your batching logic was executed correctly
        # (e.g., by checking a mock or a database state).

        # The pending list for the flushed queue will be empty
        self.assertEqual(len(backend.pending_batches["batch_queue"]), 0)
```


## Technical Details and FAQ

### Why not Celery?

Celery is powerful but heavy. At GlitchTip, we needed a simpler, `asyncio`-native task runner for our own Django backend, and `django-vtasks` is the result. It's opinionated: it only supports the two best options for modern Django (Valkey & Postgres) and strips away the rest to maximize `asyncio` throughput without the overhead of AMQP or legacy support.

A Celery web app typically requires 3 services (django, worker, beat) which can be a high burden for smaller/hobby level apps. VTasks can run embedded in one asyncio loop (web, worker, scheduler) or as separate services for high throughput.

Celery is awkward to use in async views, requiring an inefficient sync_to_async wrapper.

### Why not django-tasks?

The developers of django-tasks contributed Django's task system. Thank you! So we are using it, in a sense. However, django-tasks is not as lightweight or as efficient as django-vtasks. Specifically, we take an asyncio-first approach and have much better efficient concurrency. We could in theory contribute to django-tasks and perhaps will. vtasks and GlitchTip are made by a very small team and we're prioritizing our own projects needs. GlitchTip needs to support both Postgres and Valkey, but we don't care about much else.

If it feels weird that it's easier to create a new tool than contribute, that's because it's 100% true. Label us as having Not Invented Here syndrome. If you work on django-tasks and want to collaborate, please reach out to us.

To contribute to django-tasks, we would need to:

- Create two new backends (DB and Valkey) that compete with their own.
- Implement or extend the "task" decorator to support our custom kwargs
- Rewrite or have an alternative implementation of the task worker to use async

That's basically the entire project. But thanks to their Django task contribution, django-tasks tasks work AS IS with django-vtasks.

### Why not support more than Django?

Sure why not, send us a contribution. We would have to make a sqlachemy backend or something. The worker with valkey doesn't use many Django features.

### Why do you prefer valkey?

We have to pick one and our pick is valkey. Redis probably will work for the near future, but the projects could diverge in the future.

### Reliability (Valkey)

When using Valkey, `django-vtasks` implements the Reliable Queue Pattern:

1.  Worker waits for a task.
2.  Task is atomically moved from `q:default` to `processing:<worker_id>` via `BLMOVE`.
3.  Task is processed and then acknowledged (removed from the processing list).

If a worker crashes hard (e.g., OOM kill, power failure), the task remains in its `processing:` list. On the next startup, the same worker (or a new one with the same ID logic) can rescue the task and move it back to the main queue.

## Queue Management

### Clearing Queues

For debugging, maintenance, or emergency situations, you can clear tasks from queues using the `clear_queue` management command.

```bash
# Clear a specific queue (with confirmation prompt)
python manage.py clear_queue --backend-alias=default --queue=default

# Clear a specific queue without confirmation
python manage.py clear_queue --backend-alias=default --queue=default --force

# Clear all queues for a backend
python manage.py clear_queue --backend-alias=default --all-queues --force

# Clear failed tasks (DLQ)
python manage.py clear_queue --backend-alias=default --failed --force

# Examples with different backends
python manage.py clear_queue --backend-alias=benchmark_db --force
python manage.py clear_queue --backend-alias=benchmark_valkey --force
```

## Benchmarking

`django-vtasks` is designed to be lighter and faster than Celery for I/O-bound workloads.

Benchmarks run on identical hardware (1000 tasks, concurrency 50):

### Speed (Operations Per Second)

| Metric | Celery (Prefork) | django-vtasks (Async) | Improvement |
| :--- | :--- | :--- | :--- |
| **Enqueue Rate** (API Speed) | 637 ops/s | **1,695 ops/s** | **2.6x Faster** |
| **Process Rate** (Worker Speed) | 166 ops/s | **250 ops/s** | **1.5x Faster** |

* **Enqueue Rate:** Measures how quickly your web views return after scheduling a task.
* **Process Rate:** Measures raw machinery overhead processing no-op tasks.

### Efficiency (Resource Usage)

| Metric | Celery (Standard) | django-vtasks | Savings |
| :--- | :--- | :--- | :--- |
| **Memory per Worker** | 72 MB | **48 MB** | **33% Less RAM** |
| **Concurrency Model** | Threads/Processes | `asyncio` | High Concurrency "for free" |

* **Memory:** Measured with a standard Django installation including common apps.
* **Scalability:** VTasks maintains stable throughput even at 500+ concurrent tasks per worker, whereas thread-based workers often degrade due to context switching.

### Running Performance Tests

django-vtasks includes comprehensive benchmarking tools to measure performance across different backends and task types.

```bash
# Basic benchmark
python manage.py benchmark_vtasks --count=1000 --concurrency=50

# Test specific backend and task type
python manage.py benchmark_vtasks \
    --backend-alias=benchmark_valkey \
    --task-type=sleep \
    --count=1000 \
    --concurrency=50

# Test with large payloads
python manage.py benchmark_vtasks \
    --task-type=noop \
    --payload-size=1024 \
    --count=500
```

### Benchmark Suite

Run the complete benchmark suite to compare Database vs Valkey performance:

```bash
python benchmarks/run_suite.py
```

This will run a matrix of tests covering:
- **NoOp tasks**: Measure raw serialization/transport overhead
- **Sleep tasks**: Measure I/O concurrency handling
- **Both backends**: Direct performance comparison

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up a development environment and run tests.
