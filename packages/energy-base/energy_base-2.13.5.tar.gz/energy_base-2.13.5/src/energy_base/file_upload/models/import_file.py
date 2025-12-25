import uuid

from django.conf import settings
from django.db import models


class FileStatus(models.TextChoices):
    DRAFT = 'DRAFT'
    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'
    PROCESS = 'PROCESS'


class ImportFile(models.Model):
    Status = FileStatus

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    real_name = models.CharField(max_length=500)
    store_name = models.CharField(max_length=500)
    size = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=FileStatus.choices)
    active = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.UUIDField()
    updated_by = models.UUIDField(blank=True, null=True)
    deleted_by = models.UUIDField(blank=True, null=True)

    class Meta:
        app_label = settings.FILE_UPLOAD_APP_LABEL or 'file_upload'
        db_table = 'import_files'
        ordering = ('-created_at',)
