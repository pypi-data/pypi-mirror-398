from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import ImportFile
from ..serializers import FileUploadStatusSerializer, FileUploadStatusFilterSerializer
from ...utils.date import to_edate


class FileUploadStatusView(APIView):
    serializer_class = FileUploadStatusSerializer

    def get(self, request, *args, **kwargs):
        filter_serializer = FileUploadStatusFilterSerializer(data=request.GET)
        filter_serializer.is_valid(raise_exception=True)
        filter_date = to_edate(filter_serializer.validated_data['date'])

        status = ImportFile.objects.filter(
            date=filter_date.yesterday(),
            created_at__lte=filter_date.datetime().replace(hour=10, minute=30),
        ).exists()
        last_upload_import_file = ImportFile.objects.filter(
            created_at__date__lte=filter_date,
        ).order_by('-created_at').first()
        if last_upload_import_file:
            last_upload_datetime = str(last_upload_import_file.created_at)
        else:
            last_upload_datetime = None

        return Response({
            'status': status,
            'last_upload_datetime': last_upload_datetime,
        })
