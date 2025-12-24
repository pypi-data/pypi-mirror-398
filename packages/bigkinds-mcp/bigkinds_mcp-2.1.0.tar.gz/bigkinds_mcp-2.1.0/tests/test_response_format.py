"""
Tests for response_format parameter in MCP tools.

Tests both 'basic' (markdown) and 'full' (JSON) response formats.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.bigkinds_mcp.tools.search import search_news, init_search_tools
from src.bigkinds_mcp.tools.article import get_article, init_article_tools
from src.bigkinds_mcp.tools.visualization import get_keyword_trends, init_visualization_tools


@pytest.fixture
def mock_client():
    """Mock AsyncBigKindsClient."""
    client = AsyncMock()

    # Mock search response
    mock_search_response = MagicMock()
    mock_search_response.success = True
    mock_search_response.total_count = 100
    mock_search_response.articles = [
        MagicMock(
            news_id="test_id_1",
            title="Test Article 1",
            content="Test content 1",
            publisher="Test Publisher",
            news_date="2025-01-01",
            category="IT",
            url="https://example.com/1",
            provider_code="12345678",
        )
    ]
    client.search = AsyncMock(return_value=mock_search_response)

    # Mock get_total_count
    client.get_total_count = AsyncMock(return_value=100)

    # Mock get_article_detail
    client.get_article_detail = AsyncMock(return_value={
        "success": True,
        "detail": {
            "TITLE": "Test Article",
            "CONTENT": "Full test content for the article",
            "PROVIDER": "Test Publisher",
            "DATE": "2025-01-01",
            "BYLINE": "Test Reporter",
            "KEYWORD": "AI,Tech",
            "PROVIDER_LINK_PAGE": "https://example.com/article",
        }
    })

    # Mock get_keyword_trends
    client.get_keyword_trends = AsyncMock(return_value={
        "root": [
            {
                "keyword": "AI",
                "data": [
                    {"d": "2025-01-01", "c": 10},
                    {"d": "2025-01-02", "c": 15},
                    {"d": "2025-01-03", "c": 20},
                ]
            }
        ]
    })

    return client


@pytest.fixture
def mock_cache():
    """Mock MCPCache."""
    cache = MagicMock()
    cache.get_search = MagicMock(return_value=None)
    cache.set_search = MagicMock()
    cache.set_urls_batch = MagicMock()
    cache.get_article = MagicMock(return_value=None)
    cache.set_article = MagicMock()
    cache.get_url = MagicMock(return_value=None)
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    return cache


@pytest.fixture
def mock_scraper():
    """Mock AsyncArticleScraper."""
    scraper = AsyncMock()
    return scraper


@pytest.mark.asyncio
async def test_search_news_basic_format(mock_client, mock_cache):
    """Test search_news with response_format='basic' returns markdown."""
    init_search_tools(mock_client, mock_cache)

    result = await search_news(
        keyword="AI",
        start_date="2025-01-01",
        end_date="2025-01-10",
        response_format="basic"
    )

    # Should return string (markdown)
    assert isinstance(result, str)
    assert "# 🔍" in result  # Markdown header
    assert "AI" in result
    assert "검색 결과" in result or "주요 기사" in result


@pytest.mark.asyncio
async def test_search_news_full_format(mock_client, mock_cache):
    """Test search_news with response_format='full' returns JSON."""
    init_search_tools(mock_client, mock_cache)

    result = await search_news(
        keyword="AI",
        start_date="2025-01-01",
        end_date="2025-01-10",
        response_format="full"
    )

    # Should return dict (JSON)
    assert isinstance(result, dict)
    assert "success" in result
    assert "total_count" in result
    assert "articles" in result
    assert result["keyword"] == "AI"


@pytest.mark.asyncio
async def test_get_article_basic_format(mock_client, mock_scraper, mock_cache):
    """Test get_article with response_format='basic' returns markdown."""
    init_article_tools(mock_client, mock_scraper, mock_cache)

    result = await get_article(
        news_id="test_id_1",
        response_format="basic"
    )

    # Should return string (markdown)
    assert isinstance(result, str)
    assert "# 📰" in result  # Markdown header
    assert "Test Article" in result


@pytest.mark.asyncio
async def test_get_article_full_format(mock_client, mock_scraper, mock_cache):
    """Test get_article with response_format='full' returns JSON."""
    init_article_tools(mock_client, mock_scraper, mock_cache)

    result = await get_article(
        news_id="test_id_1",
        response_format="full"
    )

    # Should return dict (JSON)
    assert isinstance(result, dict)
    assert "news_id" in result
    assert "title" in result
    assert "full_content" in result


@pytest.mark.asyncio
async def test_get_keyword_trends_basic_format(mock_client, mock_cache):
    """Test get_keyword_trends with response_format='basic' returns markdown."""
    init_visualization_tools(mock_client, mock_cache)

    result = await get_keyword_trends(
        keyword="AI",
        start_date="2025-01-01",
        end_date="2025-01-03",
        response_format="basic"
    )

    # Should return string (markdown)
    assert isinstance(result, str)
    assert "# 📈" in result  # Markdown header
    assert "AI" in result
    assert "트렌드 분석" in result


@pytest.mark.asyncio
async def test_get_keyword_trends_full_format(mock_client, mock_cache):
    """Test get_keyword_trends with response_format='full' returns JSON."""
    init_visualization_tools(mock_client, mock_cache)

    result = await get_keyword_trends(
        keyword="AI",
        start_date="2025-01-01",
        end_date="2025-01-03",
        response_format="full"
    )

    # Should return dict (JSON)
    assert isinstance(result, dict)
    assert "success" in result
    assert "trends" in result
    assert "total_keywords" in result
    assert result["keyword"] == "AI"
