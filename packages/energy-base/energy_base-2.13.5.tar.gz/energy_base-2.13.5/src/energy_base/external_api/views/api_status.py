from urllib.parse import urlparse

from drf_spectacular.utils import extend_schema
from rest_framework import views, status
from rest_framework.response import Response

from energy_base.external_api.serializers import ApiStatusSerializer
from energy_base.services.telnet import Telnet


@extend_schema(tags=['admin/external-api'])
class BaseApiStatusView(views.APIView):
    serializer_class = ApiStatusSerializer
    api_base_url = None

    def get(self, request):
        parsed_url = urlparse(self.api_base_url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        telnet = Telnet(host=host, port=port)
        serializer = self.serializer_class(data={
            'url': self.api_base_url,
            'host': host,
            'port': port,
            'status': telnet.status,
            'error_message': telnet.error_message
        })
        serializer.is_valid(raise_exception=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
