from django.urls import path

from energy_base.api.routers import OptionalSlashRouter

from energy_base.q_api.views import TaskViewSet, ScheduleViewSet, ScheduleRunNowView

router = OptionalSlashRouter()
router.register('tasks', TaskViewSet, basename='tasks')
router.register('schedules', ScheduleViewSet, basename='schedules')

urlpatterns = [
    path('schedules/<pk>/run-now/', ScheduleRunNowView.as_view(), name='schedules-run-now'),
]

urlpatterns += router.urls
