import os
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "pyamqp://guest@rabbitmq//")
# backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://redis/0")

celery_app = Celery("actverse", broker=broker_url)
celery_app.autodiscover_tasks(["app.celery.tasks"])
celery_app.conf.task_default_queue = "actverse"
