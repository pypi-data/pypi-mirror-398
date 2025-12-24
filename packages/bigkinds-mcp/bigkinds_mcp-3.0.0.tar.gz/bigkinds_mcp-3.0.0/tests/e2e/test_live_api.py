"""E2E 테스트 - 실제 BigKinds API 호출."""

import pytest

from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.async_scraper import AsyncArticleScraper
from bigkinds_mcp.core.cache import MCPCache
from bigkinds_mcp.tools import article, search


@pytest.fixture
def setup_real_tools():
    """실제 클라이언트로 Tools 초기화."""
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


@pytest.mark.e2e
class TestSearchNewsE2E:
    """search_news E2E 테스트."""

    @pytest.mark.asyncio
    async def test_search_basic(self, setup_real_tools):
        """기본 검색 테스트."""
        result = await search.search_news(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-05",
            page=1,
            page_size=10,
            sort_by="date",
        )

        assert result["total_count"] >= 0
        assert "articles" in result
        assert result["keyword"] == "AI"

    @pytest.mark.asyncio
    async def test_search_sort_both(self, setup_real_tools):
        """sort_by=both 테스트."""
        result = await search.search_news(
            keyword="반도체",
            start_date="2024-12-01",
            end_date="2024-12-03",
            page=1,
            page_size=10,
            sort_by="both",
        )

        assert result["sort_by"] == "both"
        # 중복 없이 병합되어야 함
        if result["articles"]:
            news_ids = [a["news_id"] for a in result["articles"]]
            assert len(news_ids) == len(set(news_ids))

    @pytest.mark.asyncio
    async def test_search_empty_results(self, setup_real_tools):
        """빈 결과 테스트."""
        result = await search.search_news(
            keyword="xyznonexistentkeyword123456",
            start_date="2024-12-01",
            end_date="2024-12-02",
            page=1,
            page_size=10,
        )

        assert result["total_count"] == 0
        assert result["articles"] == []
        # 빈 결과에 대한 메시지/제안 확인
        assert "message" in result or result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_search_pagination(self, setup_real_tools):
        """페이지네이션 테스트."""
        result = await search.search_news(
            keyword="경제",
            start_date="2024-12-01",
            end_date="2024-12-10",
            page=1,
            page_size=5,
            sort_by="date",
        )

        if result["total_count"] > 5:
            assert result["has_next"] is True
            assert result["total_pages"] > 1


@pytest.mark.e2e
class TestArticleCountE2E:
    """get_article_count E2E 테스트."""

    @pytest.mark.asyncio
    async def test_count_basic(self, setup_real_tools):
        """기본 카운트 테스트."""
        result = await search.get_article_count(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-10",
        )

        assert result["keyword"] == "AI"
        assert result["total_count"] >= 0


@pytest.mark.e2e
class TestScrapeArticleE2E:
    """scrape_article_url E2E 테스트."""

    @pytest.mark.asyncio
    async def test_scrape_naver_news(self, setup_real_tools):
        """네이버 뉴스 스크래핑 테스트."""
        # 실제 네이버 뉴스 URL (변경될 수 있음)
        result = await article.scrape_article_url(
            url="https://n.news.naver.com/article/015/0005079123",
            include_markdown=True,
        )

        if result["success"]:
            assert result["title"] is not None
            assert result["content"] is not None
            assert "content_markdown" in result
            assert "llm_context" in result
        else:
            # URL이 더 이상 유효하지 않을 수 있음
            assert "error" in result

    @pytest.mark.asyncio
    async def test_scrape_invalid_url(self, setup_real_tools):
        """잘못된 URL 테스트."""
        result = await article.scrape_article_url(
            url="https://example.com/nonexistent-article-12345",
        )

        # 실패해도 에러 없이 결과 반환
        assert "success" in result
        if not result["success"]:
            assert "error" in result

    @pytest.mark.asyncio
    async def test_scrape_with_image_filter(self, setup_real_tools):
        """이미지 필터링 테스트."""
        result = await article.scrape_article_url(
            url="https://n.news.naver.com/article/015/0005079123",
            extract_images=True,
        )

        if result["success"] and result.get("images"):
            # 필터링된 이미지만 있어야 함
            for img in result["images"]:
                url = img.get("url", "").lower()
                # 광고/로고/트래커 URL이 없어야 함
                assert "logo" not in url
                assert "ads." not in url
                assert "pixel" not in url


@pytest.mark.e2e
class TestMarkdownOutputE2E:
    """마크다운 출력 E2E 테스트."""

    @pytest.mark.asyncio
    async def test_markdown_output(self, setup_real_tools):
        """마크다운 출력 테스트."""
        result = await article.scrape_article_url(
            url="https://n.news.naver.com/article/015/0005079123",
            include_markdown=True,
        )

        if result["success"]:
            # 마크다운 출력 확인
            assert "content_markdown" in result
            if result["content_markdown"]:
                # 불필요한 HTML 태그가 없어야 함
                assert "<script>" not in result["content_markdown"]
                assert "<div" not in result["content_markdown"]

            # LLM context 출력 확인
            assert "llm_context" in result
            if result["llm_context"]:
                # 구조화된 형식이어야 함
                assert "#" in result["llm_context"]  # 마크다운 헤딩
