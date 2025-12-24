"""Redis 기반 공유 캐시.

원격 MCP 서버에서 여러 클라이언트 간 캐시를 공유하기 위한 Redis 클라이언트.
"""

import json
import logging
from typing import Optional

try:
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None  # type: ignore

logger = logging.getLogger(__name__)


class RemoteCache:
    """Redis 공유 캐시.

    환경변수:
        REDIS_URL: Redis 연결 URL (기본: redis://localhost:6379)
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Args:
            redis_url: Redis 연결 URL (None이면 환경변수 사용)
        """
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis not installed. Remote cache disabled.")
            self.redis = None
            return

        import os
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[Redis] = None

    async def connect(self) -> bool:
        """Redis 연결.

        Returns:
            연결 성공 여부
        """
        if not REDIS_AVAILABLE:
            return False

        try:
            self.redis = Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True,
                health_check_interval=30
            )
            await self.redis.ping()
            logger.info(f"✅ Redis connected: {self.redis_url}")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis = None
            return False

    async def get(self, key: str) -> Optional[dict]:
        """캐시 조회.

        Args:
            key: 캐시 키

        Returns:
            캐시된 데이터 (없으면 None)
        """
        if not self.redis:
            return None

        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Redis get error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: dict, ttl: int = 300) -> bool:
        """캐시 저장.

        Args:
            key: 캐시 키
            value: 저장할 데이터
            ttl: TTL (초, 기본: 5분)

        Returns:
            저장 성공 여부
        """
        if not self.redis:
            return False

        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await self.redis.setex(key, ttl, serialized)
            return True

        except Exception as e:
            logger.error(f"Redis set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """캐시 삭제.

        Args:
            key: 캐시 키

        Returns:
            삭제 성공 여부
        """
        if not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True

        except Exception as e:
            logger.error(f"Redis delete error for key '{key}': {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 여러 키 삭제.

        Args:
            pattern: Redis key 패턴 (예: "search:*")

        Returns:
            삭제된 키 개수
        """
        if not self.redis:
            return 0

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} keys matching '{pattern}'")
                return len(keys)
            return 0

        except Exception as e:
            logger.error(f"Redis clear_pattern error: {e}")
            return 0

    async def get_stats(self) -> dict:
        """Redis 통계 조회.

        Returns:
            통계 정보
        """
        if not self.redis:
            return {
                "status": "disconnected",
                "available": False
            }

        try:
            info = await self.redis.info("stats")
            keyspace = await self.redis.info("keyspace")

            db0 = keyspace.get("db0", {})
            keys_count = db0.get("keys", 0) if isinstance(db0, dict) else 0

            return {
                "status": "connected",
                "available": True,
                "url": self.redis_url,
                "total_keys": keys_count,
                "total_commands": info.get("total_commands_processed", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }

        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {
                "status": "error",
                "available": False,
                "error": str(e)
            }

    def _calculate_hit_rate(self, info: dict) -> Optional[float]:
        """캐시 히트율 계산.

        Args:
            info: Redis INFO 통계

        Returns:
            히트율 (0.0-1.0)
        """
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)

        total = hits + misses
        if total == 0:
            return None

        return hits / total

    async def close(self):
        """Redis 연결 종료."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
