# [Ngày 7] Khởi tạo Redis async client dùng chung kết nối từ settings.REDIS_URL

import logging
from typing import Optional
from redis.asyncio import Redis, from_url

from app.core.config import settings

logger = logging.getLogger("taskhub")

redis_client: Optional[Redis] = None


async def init_redis() -> Optional[Redis]:
    """Khởi tạo kết nối Redis async client."""
    global redis_client
    try:
        redis_client = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}")
    return redis_client


async def close_redis() -> None:
    """Đóng kết nối Redis async client."""
    global redis_client
    if redis_client is not None:
        try:
            await redis_client.aclose()
        except Exception:
            pass
        redis_client = None
        logger.info("Closed Redis connection.")


async def get_redis() -> Optional[Redis]:
    """Lấy Redis client instance."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")
            return None
    return redis_client


async def invalidate_project_tasks_cache(project_id: int) -> None:
    """[Ngày 7] Invalidate toàn bộ cache list_tasks của project_id theo pattern tasks:{project_id}:* (dùng scan_iter)."""
    redis = await get_redis()
    if not redis:
        return
    try:
        pattern = f"tasks:{project_id}:*"
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache key(s) for project_id={project_id}")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for project_id={project_id}: {e}")
