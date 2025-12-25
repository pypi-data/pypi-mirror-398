from django.contrib import admin

from .models import QueuedTask, VTaskMetadata


@admin.register(QueuedTask)
class QueuedTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "queue", "status", "created_at")
    list_filter = ("status", "queue")
    search_fields = ("id", "queue")

    def has_add_permission(self, request):
        return False


@admin.register(VTaskMetadata)
class VTaskMetadataAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "expires_at")
    list_filter = ("expires_at",)
    search_fields = ("key",)
