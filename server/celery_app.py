import os

import django
from celery import Celery
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

app = Celery('server')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.broker_url = settings.CELERY_BROKER_URL

app.autodiscover_tasks()


django.setup()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


