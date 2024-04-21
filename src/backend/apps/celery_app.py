from celery import Celery

from .celery_config import *

app = Celery("worker")
app.config_from_object("apps.celery_config")
