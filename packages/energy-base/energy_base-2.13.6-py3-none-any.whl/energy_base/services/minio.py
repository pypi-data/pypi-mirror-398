import mimetypes
from typing import BinaryIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from minio import Minio


class MinioService:
    def __init__(self, endpoint, access_key, secret_key):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )

    def fput_object(self, bucket_name, object_name, file_path):
        content_type, *_ = mimetypes.guess_type(file_path)
        return self.client.fput_object(bucket_name, object_name, file_path, content_type=content_type)

    def put_object(self, bucket_name, object_name, file: BinaryIO | InMemoryUploadedFile):
        content_type = "application/octet-stream"
        length = -1
        if hasattr(file, 'content_type'):
            content_type = file.content_type
        if hasattr(file, '__len__'):
            length = len(file)
        return self.client.put_object(bucket_name, object_name, file,
                                      length=length,
                                      content_type=content_type,
                                      part_size=10 * 1024 * 1024)

    def get_object(self, bucket_name, object_name):
        try:
            response = self.client.get_object(bucket_name, object_name)
            object_bytes = response.read()
            response.close()
            response.release_conn()
        except Exception as e:
            return None
        return object_bytes
