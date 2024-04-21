from celery import Celery

from .celery_config import *

app = Celery("worker")
