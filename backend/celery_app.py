from celery import Celery
from celery.schedules import crontab
from core.config import settings

celery = Celery(
    "quesh",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    beat_schedule={
        # Dispatch pending contact attempts every 5 minutes
        "dispatch-contacts": {
            "task": "workers.tasks.dispatch_pending_contacts",
            "schedule": crontab(minute="*/5"),
        },
        # Sync payment statuses from Asaas every 30 minutes
        "sync-payments": {
            "task": "workers.tasks.sync_payment_statuses",
            "schedule": crontab(minute="*/30"),
        },
    },
)
