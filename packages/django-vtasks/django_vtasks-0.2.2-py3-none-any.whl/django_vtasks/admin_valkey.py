import logging
from datetime import datetime

from django.conf import settings
from django.contrib import admin
from django.core.paginator import Paginator
from django.db import models
from django.tasks import task_backends

from .serialization import deserialize

logger = logging.getLogger(__name__)


class ValkeyTask(models.Model):
    """A fake model to represent a task in Valkey for the Django admin."""

    id = models.CharField(primary_key=True, max_length=255)
    status = models.CharField(max_length=100)
    queue = models.CharField(max_length=255)
    payload = models.JSONField()
    enqueued_at = models.DateTimeField()
    error = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.id

    class Meta:
        managed = False
        verbose_name = "Valkey Task"
        verbose_name_plural = "Valkey Tasks"
        ordering = ("-enqueued_at",)


@admin.register(ValkeyTask)
class ValkeyTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "queue", "enqueued_at", "func_str")
    list_per_page = 100
    change_list_template = "admin/django_vtasks/valkeytask/valkey_change_list.html"

    # This admin is read-only
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Must return a queryset, but an empty one as we fetch directly
        return super().get_queryset(request).none()

    @admin.display(description="Function")
    def func_str(self, obj):
        if obj.payload:
            return obj.payload.get("func")
        return None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        page_number = request.GET.get("p", 1)

        task_instances = []

        # Find the first configured Valkey backend from settings
        valkey_backend_alias = None
        for alias, config in getattr(settings, "TASKS", {}).items():
            if "valkey" in config.get("BACKEND", "").lower():
                valkey_backend_alias = alias
                break

        if not valkey_backend_alias:
            self.message_user(
                request,
                "No Valkey backend configured in settings.TASKS.",
                level="warning",
            )
            return super().changelist_view(request, extra_context=extra_context)

        try:
            backend = task_backends[valkey_backend_alias]
            client = backend.sync_client
            prefix = backend.prefix

            # Get processing tasks
            processing_keys = list(client.scan_iter(f"{prefix}processing:*"))
            for key in processing_keys:
                worker_id = key.decode().split(":")[-1]
                for task_data_raw in client.lrange(key, 0, -1):
                    try:
                        task_info = deserialize(task_data_raw)
                        task_instances.append(
                            ValkeyTask(
                                id=task_info.get("id"),
                                status=f"processing:{worker_id}",
                                queue=task_info.get("queue", "unknown"),
                                payload=task_info,
                                enqueued_at=datetime.fromtimestamp(task_info.get("ts", 0)),
                            )
                        )
                    except Exception:
                        logger.warning("Failed to deserialize processing task", exc_info=True)

            # Get failed tasks
            failed_key = f"{prefix}q:failed"
            for task_data_raw in client.lrange(failed_key, 0, -1):
                try:
                    task_info = deserialize(task_data_raw)
                    task_instances.append(
                        ValkeyTask(
                            id=task_info.get("id"),
                            status="failed",
                            queue=task_info.get("queue", "unknown"),
                            payload=task_info,
                            enqueued_at=datetime.fromtimestamp(
                                task_info.get("failed_at", task_info.get("ts", 0))
                            ),
                            error=task_info.get("error_traceback"),
                        )
                    )
                except Exception:
                    logger.warning("Failed to deserialize failed task", exc_info=True)

        except Exception:
            logger.exception("Failed to fetch tasks from Valkey backend '%s'", valkey_backend_alias)
            self.message_user(
                request,
                f"Failed to fetch tasks from Valkey backend '{valkey_backend_alias}'.",
                level="error",
            )
            pass

        # Simple sorting
        sort_key = request.GET.get("o")
        if sort_key:
            reverse = sort_key.startswith("-")
            sort_field = sort_key.lstrip("-")
            if hasattr(ValkeyTask, sort_field):
                task_instances.sort(key=lambda x: getattr(x, sort_field) or "", reverse=reverse)

        # Paginate the full list of objects
        paginator = Paginator(task_instances, self.list_per_page)
        page_obj = paginator.page(page_number)

        cl = self.get_changelist_instance(request)
        cl.result_count = paginator.count
        cl.queryset = page_obj.object_list
        cl.paginator = paginator
        cl.page_num = page_obj.number
        cl.multi_page = paginator.num_pages > 1
        cl.can_show_all = False
        cl.formset = None

        extra_context["cl"] = cl
        return super().changelist_view(request, extra_context=extra_context)
