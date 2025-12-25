from django.utils import timezone
from django_q.models import Schedule
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, filters

from energy_base.api.permissions import IsSuperUser
from energy_base.q_api.serializers import ScheduleSerializer


@extend_schema(tags=['admin/schedules'])
class ScheduleViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'patch']
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsSuperUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@extend_schema(tags=['admin/schedules'], request={})
class ScheduleRunNowView(viewsets.generics.UpdateAPIView):
    serializer_class = ScheduleSerializer
    http_method_names = ['patch']
    queryset = Schedule.objects.all()

    def perform_update(self, serializer):
        serializer.save(next_run=timezone.now())
