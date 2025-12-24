"""MCP Tools 테스트."""

import pytest

from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.async_scraper import AsyncArticleScraper
from bigkinds_mcp.core.cache import MCPCache
from bigkinds_mcp.tools import article, search


@pytest.fixture
def setup_tools():
    """Tools 초기화 fixture."""
    client = AsyncBigKindsClient()
    scraper = AsyncArticleScraper()
    cache = MCPCache()

    search.init_search_tools(client, cache)
    article.init_article_tools(client, scraper, cache)

    yield {"client": client, "scraper": scraper, "cache": cache}

    # Sync cleanup - run async close in event loop
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(client.close())
        else:
            loop.run_until_complete(client.close())
    except RuntimeError:
        asyncio.run(client.close())

    # Scraper close is synchronous
    scraper.close()


class TestSearchNews:
    """search_news 도구 테스트."""

    @pytest.mark.asyncio
    async def test_search_basic(self, setup_tools):
        """기본 검색 테스트."""
        result = await search.search_news(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-05",
            page=1,
            page_size=10,
            sort_by="date",
        )

        assert result["total_count"] > 0
        assert len(result["articles"]) <= 10
        assert result["page"] == 1
        assert result["keyword"] == "AI"

    @pytest.mark.asyncio
    async def test_search_sort_by_both(self, setup_tools):
        """sort_by=both 병합 테스트."""
        result = await search.search_news(
            keyword="반도체",
            start_date="2024-12-01",
            end_date="2024-12-03",
            page=1,
            page_size=10,
            sort_by="both",
        )

        assert result["sort_by"] == "both"
        assert len(result["articles"]) > 0
        # 병합 후 중복 제거 확인
        news_ids = [a["news_id"] for a in result["articles"]]
        assert len(news_ids) == len(set(news_ids))

    @pytest.mark.asyncio
    async def test_search_pagination(self, setup_tools):
        """페이지네이션 테스트."""
        result = await search.search_news(
            keyword="경제",
            start_date="2024-12-01",
            end_date="2024-12-10",
            page=1,
            page_size=5,
            sort_by="date",
        )

        assert result["page_size"] == 5
        assert result["total_pages"] > 1
        assert result["has_next"] is True
        assert result["has_prev"] is False


class TestGetArticleCount:
    """get_article_count 도구 테스트."""

    @pytest.mark.asyncio
    async def test_count_basic(self, setup_tools):
        """기본 카운트 테스트."""
        result = await search.get_article_count(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-10",
        )

        assert result["keyword"] == "AI"
        assert result["total_count"] > 0
        assert "2024-12-01" in result["date_range"]


class TestScrapeArticle:
    """scrape_article_url 도구 테스트."""

    @pytest.mark.asyncio
    async def test_scrape_naver_news(self, setup_tools):
        """네이버 뉴스 스크래핑 테스트."""
        result = await article.scrape_article_url(
            url="https://n.news.naver.com/article/015/0005079123"
        )

        assert result["success"] is True
        assert result["title"] is not None
        assert len(result["content"]) > 0

    @pytest.mark.asyncio
    async def test_scrape_invalid_url(self, setup_tools):
        """잘못된 URL 스크래핑 테스트."""
        result = await article.scrape_article_url(
            url="https://example.com/nonexistent-article-12345"
        )

        # 실패해도 에러 없이 결과 반환
        assert "success" in result
        assert "error" in result


class TestCache:
    """캐시 테스트."""

    def test_cache_search(self):
        """검색 캐시 테스트."""
        cache = MCPCache()

        cache.set_search({"test": "data"}, keyword="AI", date="2024-12-01")
        result = cache.get_search(keyword="AI", date="2024-12-01")

        assert result == {"test": "data"}

    def test_cache_article(self):
        """기사 캐시 테스트."""
        cache = MCPCache()

        cache.set_article("news123", {"title": "Test"})
        result = cache.get_article("news123")

        assert result == {"title": "Test"}

    def test_cache_miss(self):
        """캐시 미스 테스트."""
        cache = MCPCache()

        result = cache.get_search(keyword="nonexistent")
        assert result is None
