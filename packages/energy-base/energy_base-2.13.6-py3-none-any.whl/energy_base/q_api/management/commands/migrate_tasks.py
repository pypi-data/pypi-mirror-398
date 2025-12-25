import importlib

from django.conf import settings
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Migrate tasks"

    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, help="An optional argument", required=True)

    def handle(self, *args, **options):
        try:
            tasks = importlib.import_module(f"apps.{options['app']}.tasks")
            tasks = tasks.tasks
            for task in tasks:
                scheduler = Schedule.objects.filter(name=task['name']).first()
                if not scheduler:
                    scheduler = Schedule()
                else:
                    task.pop('next_run')
                for k, v in task.items():
                    setattr(scheduler, k, v)
                scheduler.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully migrated tasks')
            )
        except ModuleNotFoundError:
            self.stdout.write(self.style.ERROR("Tasks module not found"))
