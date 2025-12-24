"""인메모리 TTL 캐시.

PRD AC10 캐시 TTL 설정:
- 검색 결과: 5분 (300초)
- 기사 상세: 30분 (1800초)
- 트렌드/연관어: 10분 (600초)
- 언론사/카테고리 목록: 24시간 (86400초)
"""

import hashlib
import json
from typing import Any

from cachetools import TTLCache

# PRD AC10 캐시 TTL 상수
SEARCH_CACHE_TTL = 300  # 5분
ARTICLE_CACHE_TTL = 1800  # 30분
COUNT_CACHE_TTL = 300  # 5분 (검색과 동일)
TREND_CACHE_TTL = 600  # 10분
METADATA_CACHE_TTL = 86400  # 24시간


class MCPCache:
    """MCP 서버용 인메모리 캐시."""

    def __init__(
        self,
        maxsize: int = 1000,
        search_ttl: int = SEARCH_CACHE_TTL,
        article_ttl: int = ARTICLE_CACHE_TTL,
        count_ttl: int = COUNT_CACHE_TTL,
    ):
        self._search_cache: TTLCache = TTLCache(maxsize=maxsize, ttl=search_ttl)
        self._article_cache: TTLCache = TTLCache(maxsize=maxsize, ttl=article_ttl)
        self._count_cache: TTLCache = TTLCache(maxsize=maxsize, ttl=count_ttl)
        self._generic_cache: TTLCache = TTLCache(maxsize=maxsize, ttl=TREND_CACHE_TTL)
        # news_id -> url 매핑 캐시 (기사 상세 조회용)
        self._url_cache: TTLCache = TTLCache(maxsize=maxsize * 10, ttl=article_ttl)

    def _make_key(self, prefix: str, **kwargs) -> str:
        """캐시 키 생성."""
        # None 값 필터링 후 정렬된 JSON으로 해시
        filtered = {k: v for k, v in kwargs.items() if v is not None}
        data = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
        hash_val = hashlib.md5(data.encode()).hexdigest()[:12]
        return f"{prefix}:{hash_val}"

    # Search 캐시
    def get_search(self, **kwargs) -> Any | None:
        """검색 결과 캐시 조회."""
        key = self._make_key("search", **kwargs)
        return self._search_cache.get(key)

    def set_search(self, value: Any, **kwargs) -> None:
        """검색 결과 캐시 저장."""
        key = self._make_key("search", **kwargs)
        self._search_cache[key] = value

    # Article 캐시
    def get_article(self, news_id: str) -> Any | None:
        """기사 캐시 조회."""
        return self._article_cache.get(f"article:{news_id}")

    def set_article(self, news_id: str, value: Any) -> None:
        """기사 캐시 저장."""
        self._article_cache[f"article:{news_id}"] = value

    # Count 캐시
    def get_count(self, **kwargs) -> Any | None:
        """기사 수 캐시 조회."""
        key = self._make_key("count", **kwargs)
        return self._count_cache.get(key)

    def set_count(self, value: Any, **kwargs) -> None:
        """기사 수 캐시 저장."""
        key = self._make_key("count", **kwargs)
        self._count_cache[key] = value

    # URL 캐시 (news_id -> url 매핑)
    def get_url(self, news_id: str) -> str | None:
        """news_id로 URL 조회."""
        return self._url_cache.get(f"url:{news_id}")

    def set_url(self, news_id: str, url: str) -> None:
        """news_id -> URL 매핑 저장."""
        if news_id and url:
            self._url_cache[f"url:{news_id}"] = url

    def set_urls_batch(self, articles: list[dict]) -> None:
        """여러 기사의 news_id -> URL 매핑을 일괄 저장."""
        for article in articles:
            news_id = article.get("news_id")
            url = article.get("url")
            if news_id and url:
                self._url_cache[f"url:{news_id}"] = url

    # Generic 캐시 (visualization 등)
    def get(self, key: str) -> Any | None:
        """제네릭 캐시 조회."""
        return self._generic_cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """제네릭 캐시 저장."""
        if ttl is not None:
            # TTL 지정 시 새 캐시 생성
            cache = TTLCache(maxsize=1, ttl=ttl)
            cache[key] = value
            self._generic_cache.update(cache)
        else:
            self._generic_cache[key] = value

    # 캐시 통계
    def stats(self) -> dict:
        """캐시 통계 반환."""
        return {
            "search": {
                "size": len(self._search_cache),
                "maxsize": self._search_cache.maxsize,
            },
            "article": {
                "size": len(self._article_cache),
                "maxsize": self._article_cache.maxsize,
            },
            "count": {
                "size": len(self._count_cache),
                "maxsize": self._count_cache.maxsize,
            },
            "generic": {
                "size": len(self._generic_cache),
                "maxsize": self._generic_cache.maxsize,
            },
        }

    def clear(self) -> None:
        """모든 캐시 클리어."""
        self._search_cache.clear()
        self._article_cache.clear()
        self._count_cache.clear()
        self._generic_cache.clear()
        self._url_cache.clear()
