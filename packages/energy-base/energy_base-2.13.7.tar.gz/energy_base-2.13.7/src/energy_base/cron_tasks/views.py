import importlib
import inspect

from django.conf import settings
from django_q.tasks import async_task
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import BaseCronTask


class CronTaskRunSerializer(serializers.Serializer):
    params = serializers.DictField()


class CronTasksView(APIView):
    def get(self, request):
        cron_tasks = []
        for cron_task_class_path in settings.CRON_TASK_CLASSES:
            module_name, class_name = cron_task_class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            cron_task_class: BaseCronTask = getattr(module, class_name)
            argspec = inspect.getfullargspec(cron_task_class.run)
            cron_tasks.append({
                'name': cron_task_class.name,
                'args': argspec.args,
            })

        return Response(cron_tasks)


class CronTaskRunView(APIView):
    @extend_schema(request=[CronTaskRunSerializer])
    def post(self, request, name):
        serializer = CronTaskRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for cron_task_class_path in settings.CRON_TASK_CLASSES:
            module_name, class_name = cron_task_class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            cron_task_class: BaseCronTask = getattr(module, class_name)
            if cron_task_class.name == name:
                run_func_name = cron_task_class_path + '.run'
                async_task(run_func_name, serializer.validated_data['params'])
                return Response()

        return Response(status=status.HTTP_404_NOT_FOUND)
