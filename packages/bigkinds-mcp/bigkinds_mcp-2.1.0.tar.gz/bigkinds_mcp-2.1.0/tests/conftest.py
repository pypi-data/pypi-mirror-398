"""테스트 공통 fixtures."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.async_scraper import AsyncArticleScraper
from bigkinds_mcp.core.cache import MCPCache
from bigkinds_mcp.tools import article, search

# Fixtures 디렉토리
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load JSON fixture file."""
    with open(FIXTURES_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# Mock Fixtures
# ============================================================


@pytest.fixture
def mock_search_response():
    """Mock search response data."""
    return {
        "success": True,
        "total_count": 100,
        "articles": [
            {
                "NEWS_ID": f"test-news-{i}",
                "TITLE": f"테스트 기사 {i}",
                "CONTENT": f"테스트 본문 내용 {i}",
                "PROVIDER": "테스트언론",
                "CATEGORY": "경제",
                "NEWS_DATE": "2024-12-15",
                "URL": f"https://test.com/article/{i}",
            }
            for i in range(10)
        ],
    }


@pytest.fixture
def mock_empty_response():
    """Mock empty search response."""
    return {
        "success": True,
        "total_count": 0,
        "articles": [],
    }


@pytest.fixture
def mock_error_response():
    """Mock error response."""
    return {
        "success": False,
        "error_message": "API Error",
        "error_code": "500",
    }


@pytest.fixture
def mock_scraped_article():
    """Mock scraped article."""
    from bigkinds.article_scraper import ScrapedArticle

    return ScrapedArticle(
        source_url="https://test.com/article/1",
        final_url="https://test.com/article/1",
        title="테스트 기사 제목",
        content="테스트 기사 본문입니다. " * 20,
        content_html="<article><h1>테스트 기사 제목</h1><p>테스트 기사 본문입니다.</p></article>",
        description="테스트 요약",
        author="테스트 기자",
        published_date="2024-12-15T10:00:00+09:00",
        publisher="테스트언론",
        keywords=["테스트", "기사", "뉴스"],
        images=[
            {"url": "https://test.com/img/main.jpg", "caption": "메인 이미지", "is_main": True},
            {"url": "https://test.com/img/sub.jpg", "caption": "서브 이미지", "is_main": False},
        ],
        success=True,
    )


@pytest.fixture
def mock_scraped_article_failed():
    """Mock failed scrape."""
    from bigkinds.article_scraper import ScrapedArticle

    return ScrapedArticle(
        source_url="https://test.com/404",
        success=False,
        error="HTTP 404",
    )


# ============================================================
# Client Fixtures
# ============================================================


@pytest.fixture
def mock_bigkinds_client(mock_search_response):
    """Mock BigKinds client."""
    client = AsyncMock(spec=AsyncBigKindsClient)

    # Mock search method
    async def mock_search(*args, **kwargs):
        from bigkinds.models import SearchResponse, NewsArticle

        articles = [
            NewsArticle.from_api_response(a)
            for a in mock_search_response["articles"]
        ]
        return SearchResponse(
            success=True,
            total_count=mock_search_response["total_count"],
            articles=articles,
            keyword=kwargs.get("keyword", "test"),
            date_range="2024-12-01 to 2024-12-15",
        )

    client.search = mock_search
    client.close = MagicMock()
    return client


@pytest.fixture
def mock_scraper(mock_scraped_article):
    """Mock article scraper."""
    scraper = AsyncMock(spec=AsyncArticleScraper)

    async def mock_scrape(url: str):
        if "404" in url or "error" in url:
            from bigkinds.article_scraper import ScrapedArticle
            return ScrapedArticle(source_url=url, success=False, error="HTTP 404")
        return mock_scraped_article

    scraper.scrape = mock_scrape
    scraper.close = MagicMock()
    return scraper


@pytest.fixture
def cache():
    """Fresh cache instance."""
    return MCPCache()


# ============================================================
# Tool Initialization Fixtures
# ============================================================


@pytest.fixture
def setup_tools_mock(mock_bigkinds_client, mock_scraper, cache):
    """Initialize tools with mocks."""
    search.init_search_tools(mock_bigkinds_client, cache)
    article.init_article_tools(mock_bigkinds_client, mock_scraper, cache)

    yield {
        "client": mock_bigkinds_client,
        "scraper": mock_scraper,
        "cache": cache,
    }


@pytest.fixture
def setup_tools_real():
    """Initialize tools with real clients (for E2E tests)."""
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
            # If loop is running, create task
            asyncio.create_task(client.close())
        else:
            # If loop not running, run_until_complete
            loop.run_until_complete(client.close())
    except RuntimeError:
        # Fallback: create new loop
        asyncio.run(client.close())

    # Scraper close is synchronous
    scraper.close()


# ============================================================
# Image Filter Test Data
# ============================================================


@pytest.fixture
def sample_images():
    """Sample images for filter testing."""
    return [
        # Good images
        {"url": "https://news.com/img/2024/12/article-main.jpg", "caption": "기사 이미지", "is_main": True},
        {"url": "https://news.com/img/2024/12/15/abcd1234567890ab.jpg", "caption": None, "is_main": False},
        # Bad images (should be filtered)
        {"url": "https://ads.example.com/banner.jpg", "caption": None, "is_main": False},
        {"url": "https://news.com/logo.png", "caption": None, "is_main": False},
        {"url": "https://news.com/icon/share-facebook.png", "caption": None, "is_main": False},
        {"url": "https://tracker.com/pixel.gif", "caption": None, "is_main": False},
        {"url": "https://news.com/common/placeholder.jpg", "caption": None, "is_main": False},
    ]


# ============================================================
# Markdown Test Data
# ============================================================


@pytest.fixture
def sample_html():
    """Sample HTML for markdown conversion."""
    return """
    <article>
        <h1>테스트 기사 제목</h1>
        <p>첫 번째 문단입니다. <strong>중요한 내용</strong>이 있습니다.</p>
        <p>두 번째 문단입니다. <a href="https://example.com">링크</a>도 있습니다.</p>
        <ul>
            <li>항목 1</li>
            <li>항목 2</li>
        </ul>
        <div class="ad">광고 영역</div>
        <div class="related">관련 기사</div>
    </article>
    """
