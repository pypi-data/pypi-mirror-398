import uuid

from django.db import models
from django.db.models import Q


class TaskStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    PROCESSING = "PROCESSING", "Processing"
    FAILED = "FAILED", "Failed"


class QueuedTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue = models.CharField(max_length=255, db_index=True)
    unique_key = models.CharField(max_length=255, null=True, blank=True)
    data = models.BinaryField()
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.QUEUED,
        db_index=True,
    )
    worker_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(default=0, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["queue", "status", "-priority", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["queue", "unique_key"],
                condition=Q(status__in=[TaskStatus.QUEUED, TaskStatus.PROCESSING]),
                name="unique_queued_or_processing_task",
            )
        ]


class VTaskMetadata(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField()
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name_plural = "VTask Metadata"
