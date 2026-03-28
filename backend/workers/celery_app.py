from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "reportchecker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Oslo",
    enable_utc=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["workers"])
