
from ...services import MinioService

from django.conf import settings

minio_service = MinioService(
    endpoint=settings.MINIO.get("ENDPOINT"),
    access_key=settings.MINIO.get("ACCESS_KEY"),
    secret_key=settings.MINIO.get("SECRET_KEY"),
)
