from django_q.models import Task
from rest_framework import serializers


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

    def to_representation(self, instance):
        if isinstance(instance, str):
            instance = Task.objects.filter(pk=instance).first()

        if not instance:
            return None
        data = super(TaskSerializer, self).to_representation(instance)
        data['args'] = instance.args
        data['kwargs'] = instance.kwargs
        data['result'] = instance.result

        return data
