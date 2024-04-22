# Broker settings.
broker_url = "redis://redis:6379/0"

# List of modules to import when the Celery worker starts.
imports = ("apps.tasks",)

# Using the database to store task state and results.
result_backend = "redis://redis:6379/0"

task_annotations = {"*": {"rate_limit": "10/s"}}

task_queues = {
    "ml-queue": {
        "exchange": "ml-queue",
    }
}
task_routes = {"worker.celery_worker.long_task": "ml-queue"}
task_track_started = True

worker_concurrency = 1
worker_prefetch_multiplier = 1
