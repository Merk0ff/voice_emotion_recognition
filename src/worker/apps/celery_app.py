from pathlib import Path

from celery import Celery

app = Celery("worker")

Path("./downloads").mkdir(parents=True, exist_ok=True)
