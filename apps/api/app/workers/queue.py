from redis import Redis
from rq import Queue

from app.core.config import settings


def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url)


def get_comp_queue() -> Queue:
    return Queue("comp_ingest", connection=get_redis())
