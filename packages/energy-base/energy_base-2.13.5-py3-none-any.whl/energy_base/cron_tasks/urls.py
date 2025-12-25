from django.urls import path

from .views import CronTasksView, CronTaskRunView

urlpatterns = [
    path('cron-tasks', CronTasksView.as_view(), name='cron-tasks'),
    path('cron-tasks/<str:name>/run', CronTaskRunView.as_view(), name='cron-task-run'),
]
