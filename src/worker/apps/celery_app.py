from pathlib import Path

from celery import Celery

app = Celery("worker")
app.config_from_object("apps.celery_config")

Path("./downloads").mkdir(parents=True, exist_ok=True)
