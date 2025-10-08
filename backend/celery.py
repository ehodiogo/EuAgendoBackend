import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'backup-banco-daily': {
        'task': 'api.tasks.backup_postgres_to_drive',
        'schedule': crontab(hour=2, minute=0),  # todo dia às 2h da manhã
    },
}