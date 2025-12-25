from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from ..models import ImportFile


class ImportFileSerializer(serializers.ModelSerializer):
    created_by = serializers.DictField()

    class Meta:
        model = ImportFile
        fields = '__all__'


class FileDownloadSerializer(serializers.Serializer):
    file = serializers.FileField()


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(validators=[FileExtensionValidator(allowed_extensions=['xls', 'xlsx'])])
    date = serializers.DateField()


class FileConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportFile
        fields = []
