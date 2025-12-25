from django_q.models import Schedule
from rest_framework import serializers

from energy_base.q_api.serializers import TaskSerializer


class ScheduleSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = '__all__'
        read_only_fields = ['name', 'func', 'hook', 'args', 'kwargs', 'cluster']
