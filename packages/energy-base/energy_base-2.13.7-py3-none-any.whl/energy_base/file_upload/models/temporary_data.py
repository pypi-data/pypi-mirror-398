import uuid

from django.conf import settings
from django.db import models

from ..models import ImportFile


class TemporaryData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(ImportFile, on_delete=models.CASCADE)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.UUIDField()
    updated_by = models.UUIDField(blank=True, null=True)
    deleted_by = models.UUIDField(blank=True, null=True)

    class Meta:
        app_label = settings.FILE_UPLOAD_APP_LABEL or 'file_upload'
        db_table = 'temporary_data'
        ordering = ('-created_at',)
