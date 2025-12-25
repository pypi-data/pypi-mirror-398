import importlib
import mimetypes
import os
import uuid

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse, Http404
from django_filters.rest_framework.backends import DjangoFilterBackend
from energy_base.translation import translate as _
from rest_framework import viewsets, filters, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from ..data_processors import XlsProcessor, BaseSheetProcessor
from ..filters import FileFilterSet
from ..models import ImportFile, TemporaryData
from ..serializers.file import (
    FileDownloadSerializer,
    ImportFileSerializer,
    FileUploadSerializer,
    FileConfirmSerializer
)
from ..services import minio_service
from ...api import pagination
from ...api.base import BaseAPIView, BaseRequest
from ...services import UserService

BUCKET_NAME = settings.MINIO.get("BUCKET_NAME")


class DataProcessorMixin:
    data_processor_classes = []

    _data_processors = None

    def get_data_processors(self) -> list[BaseSheetProcessor]:
        if self._data_processors:
            return self._data_processors

        processors = []
        for processor_class in (self.data_processor_classes or getattr(settings, 'DATA_PROCESSORS_CLASSES', [])):
            if isinstance(processor_class, str):
                module_name, class_name = processor_class.rsplit('.', 1)
                module = importlib.import_module(module_name)
                processor_class = getattr(module, class_name)

            processors.append(processor_class())

        self._data_processors = processors
        return self._data_processors


class ImportFileViewSet(viewsets.GenericViewSet, viewsets.generics.ListAPIView):
    queryset = ImportFile.objects.all()
    serializer_class = ImportFileSerializer
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FileFilterSet
    pagination_class = pagination.SmallResultsSetPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.paginate_queryset(queryset)

        files = list(queryset)

        created_bys = []
        for file in files:
            created_bys.append(str(file.created_by))

        users = UserService.get_users(created_bys)
        users = {u['id']: u for u in users}

        for file in files:
            creator = users.get(str(file.created_by), {})

            file.created_by = {
                'id': creator.get('id'),
                'username': creator.get('username'),
                'firstName': creator.get('firstName'),
                'surName': creator.get('surName'),
                'midName': creator.get('midName'),
            }

        serializer = self.get_serializer(files, many=True)
        return self.get_paginated_response(serializer.data)


class FileDownloadViewSet(viewsets.generics.RetrieveAPIView):
    queryset = ImportFile.objects.all()
    serializer_class = FileDownloadSerializer

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        file_bytes = minio_service.get_object(BUCKET_NAME, obj.store_name)
        if file_bytes is None:
            raise Http404('File not found')
        content_type, _ = mimetypes.guess_type(obj.real_name, strict=False)
        response = HttpResponse(file_bytes, content_type=content_type or 'application/octet-stream')
        response['Content-Length'] = len(file_bytes)
        response['Content-Disposition'] = 'attachment; filename="%s"' % obj.real_name
        return response


class FileUploadViewSet(BaseAPIView, viewsets.generics.CreateAPIView, DataProcessorMixin):
    serializer_class = FileUploadSerializer
    parser_classes = (MultiPartParser,)

    def create(self, request: BaseRequest, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file: InMemoryUploadedFile = serializer.validated_data.get('file')
        try:
            xls_processor = XlsProcessor(file.read())
        except:
            return Response({
                'file_read': _('File could not be read')
            }, status=status.HTTP_400_BAD_REQUEST)
        errors = xls_processor.validate_many([data_processor for data_processor in self.get_data_processors()])

        if errors:
            return Response({
                'sheets': errors
            }, status=status.HTTP_400_BAD_REQUEST)

        file.seek(0)

        random_str = uuid.uuid4().hex
        date = serializer.validated_data.get('date').strftime('%Y-%m-%d')
        file_extension = os.path.splitext(file.name)[1]
        store_name = f'{date}--{random_str}{file_extension}'

        minio_service.put_object(BUCKET_NAME, store_name, file)

        import_file = ImportFile(
            date=serializer.validated_data.get('date'),
            real_name=file.name,
            store_name=store_name,
            size=file.size,
            status=ImportFile.Status.DRAFT,
            active=False,
            created_by=self.request.user.pk,
        )
        import_file.save()

        data = {}
        for data_processor in self.get_data_processors():
            data[data_processor.sheet_index] = xls_processor.get_data(data_processor)

        temporary_data = TemporaryData(
            file=import_file,
            data=data,
            created_by=self.request.user.pk
        )
        temporary_data.save()

        return Response(
            data={
                'success': True,
                'file_id': import_file.pk
            },
            status=status.HTTP_201_CREATED
        )


class FileConfirmViewSet(BaseAPIView, viewsets.generics.UpdateAPIView, DataProcessorMixin):
    serializer_class = FileConfirmSerializer
    http_method_names = ['patch']
    queryset = ImportFile.objects.filter(status=ImportFile.Status.DRAFT, active=False).all()

    def perform_update(self, serializer):
        model: ImportFile = self.get_object()
        temp = TemporaryData.objects.filter(file=model).get()
        data = temp.data
        for data_processor in self.get_data_processors():
            data_processor.write_db(
                data.get(str(data_processor.sheet_index)),
                model,
                self.request.user.pk,
            )
        temp.delete()
        ImportFile.objects.filter(active=True, date=model.date).update(active=False)
        serializer.save(status=ImportFile.Status.SUCCESS, active=True)
