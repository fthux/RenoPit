"""
Celery 实例配置 — 使用 Redis 作为 Broker 和结果后端
"""

from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "renovation_analyzer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=True,
    include=["app.tasks.analysis"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=1200,  # 20 min hard limit (accommodates serial document analysis)
    task_soft_time_limit=1200,  # 20 min soft limit
)