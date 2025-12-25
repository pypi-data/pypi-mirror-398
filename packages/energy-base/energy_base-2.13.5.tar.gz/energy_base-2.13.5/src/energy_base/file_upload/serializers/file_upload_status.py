from rest_framework import serializers

from ...utils import EDate


class FileUploadStatusSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    last_upload_date = serializers.DateTimeField()


class FileUploadStatusFilterSerializer(serializers.Serializer):
    date = serializers.DateField(required=False, default=EDate.today())
