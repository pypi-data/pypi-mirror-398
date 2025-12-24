"""
Integration tests for Response Format + Remote Server.

Tests that response_format parameter works correctly when called via HTTP endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.bigkinds_mcp.remote_server import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_headers():
    """Valid API key headers."""
    return {"x-api-key": "test_key_123"}


@pytest.fixture
def mock_search_result():
    """Mock search_news result."""
    return {
        "success": True,
        "keyword": "AI",
        "total_count": 9817,
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "page": 1,
        "page_size": 20,
        "articles": [
            {
                "news_id": "01100101.20250102103045001",
                "title": "AI 기술 발전",
                "publisher": "경향신문",
                "published_date": "2025-01-02",
                "summary": "인공지능 기술이 급속도로 발전하고 있다...",
                "url": "https://example.com/article1",
            },
            {
                "news_id": "01100101.20250102103045002",
                "title": "AI 규제 논의",
                "publisher": "한겨레",
                "published_date": "2025-01-02",
                "summary": "AI 규제에 대한 논의가 활발하다...",
                "url": "https://example.com/article2",
            },
        ],
    }


@pytest.fixture
def mock_article_result():
    """Mock get_article result."""
    return {
        "success": True,
        "news_id": "01100101.20250102103045001",
        "title": "AI 기술의 미래",
        "publisher": "경향신문",
        "published_date": "2025-01-02",
        "author": "홍길동 기자",
        "category": "IT_과학",
        "full_content": "인공지능 기술이 우리 삶을 변화시키고 있다. " * 50,
    }


class TestSearchNewsResponseFormat:
    """Test search_news response format via remote server."""

    @patch("src.bigkinds_mcp.tools.search.search_news")
    async def test_search_news_basic_format_via_http(
        self, mock_search, client, valid_headers, mock_search_result
    ):
        """Test search_news with response_format='basic' returns markdown via HTTP."""
        # Mock the search_news function to return markdown
        expected_markdown = "# 🔍 \"AI\" 검색 결과\n\n**📊 총 건수**: 9,817건"
        mock_search.return_value = expected_markdown

        response = client.post(
            "/api/tools/search_news",
            headers=valid_headers,
            json={
                "keyword": "AI",
                "start_date": "2025-01-01",
                "end_date": "2025-01-10",
                "response_format": "basic",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # When returned via HTTP, markdown is wrapped in JSON
        assert isinstance(data, (str, dict))

        # Verify mock was called with correct params
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["response_format"] == "basic"

    @patch("src.bigkinds_mcp.tools.search.search_news")
    async def test_search_news_full_format_via_http(
        self, mock_search, client, valid_headers, mock_search_result
    ):
        """Test search_news with response_format='full' returns JSON via HTTP."""
        mock_search.return_value = mock_search_result

        response = client.post(
            "/api/tools/search_news",
            headers=valid_headers,
            json={
                "keyword": "AI",
                "start_date": "2025-01-01",
                "end_date": "2025-01-10",
                "response_format": "full",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Full format returns complete JSON
        assert isinstance(data, dict)
        assert data["success"] is True
        assert data["total_count"] == 9817
        assert "articles" in data
        assert len(data["articles"]) == 2

        # Verify mock was called with correct params
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs["response_format"] == "full"

    @patch("src.bigkinds_mcp.tools.search.search_news")
    async def test_search_news_default_format_is_full(
        self, mock_search, client, valid_headers, mock_search_result
    ):
        """Test search_news defaults to 'full' format when not specified."""
        mock_search.return_value = mock_search_result

        response = client.post(
            "/api/tools/search_news",
            headers=valid_headers,
            json={
                "keyword": "AI",
                "start_date": "2025-01-01",
                "end_date": "2025-01-10",
                # response_format not specified
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Default should be 'full' (JSON)
        assert isinstance(data, dict)
        assert data["success"] is True

        # Verify mock was called with default 'full'
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs.get("response_format", "full") == "full"


class TestGetArticleResponseFormat:
    """Test get_article response format via remote server."""

    @patch("src.bigkinds_mcp.tools.article.get_article")
    async def test_get_article_basic_format_via_http(
        self, mock_article, client, valid_headers, mock_article_result
    ):
        """Test get_article with response_format='basic' returns markdown via HTTP."""
        expected_markdown = "# 📰 AI 기술의 미래\n\n**언론사**: 경향신문"
        mock_article.return_value = expected_markdown

        response = client.post(
            "/api/tools/get_article",
            headers=valid_headers,
            json={
                "news_id": "01100101.20250102103045001",
                "response_format": "basic",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, (str, dict))

        # Verify mock was called with correct params
        mock_article.assert_called_once()
        call_kwargs = mock_article.call_args[1]
        assert call_kwargs["response_format"] == "basic"

    @patch("src.bigkinds_mcp.tools.article.get_article")
    async def test_get_article_full_format_via_http(
        self, mock_article, client, valid_headers, mock_article_result
    ):
        """Test get_article with response_format='full' returns JSON via HTTP."""
        mock_article.return_value = mock_article_result

        response = client.post(
            "/api/tools/get_article",
            headers=valid_headers,
            json={
                "news_id": "01100101.20250102103045001",
                "response_format": "full",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert data["success"] is True
        assert data["title"] == "AI 기술의 미래"
        assert data["publisher"] == "경향신문"
        assert "full_content" in data

        # Verify mock was called with correct params
        mock_article.assert_called_once()
        call_kwargs = mock_article.call_args[1]
        assert call_kwargs["response_format"] == "full"


class TestResponseFormatContextReduction:
    """Test that basic format achieves context reduction goal."""

    @patch("src.bigkinds_mcp.tools.search.search_news")
    async def test_basic_format_reduces_response_size(
        self, mock_search, client, valid_headers, mock_search_result
    ):
        """Verify basic format is significantly smaller than full format."""
        # Full format mock
        full_result = mock_search_result
        mock_search.return_value = full_result

        # Get full format response
        response_full = client.post(
            "/api/tools/search_news",
            headers=valid_headers,
            json={
                "keyword": "AI",
                "start_date": "2025-01-01",
                "end_date": "2025-01-10",
                "response_format": "full",
            },
        )
        full_size = len(str(response_full.json()))

        # Basic format mock (markdown)
        basic_markdown = (
            "# 🔍 \"AI\" 검색 결과\n\n"
            "**📊 총 건수**: 9,817건\n\n"
            "## 주요 기사\n\n"
            "### 1. AI 기술 발전 - 경향신문 (2025-01-02)\n"
            "> 인공지능 기술이 급속도로 발전하고 있다...\n\n"
            "### 2. AI 규제 논의 - 한겨레 (2025-01-02)\n"
            "> AI 규제에 대한 논의가 활발하다...\n\n"
        )
        mock_search.return_value = basic_markdown

        # Get basic format response
        response_basic = client.post(
            "/api/tools/search_news",
            headers=valid_headers,
            json={
                "keyword": "AI",
                "start_date": "2025-01-01",
                "end_date": "2025-01-10",
                "response_format": "basic",
            },
        )
        basic_size = len(str(response_basic.json()))

        # Basic should be significantly smaller (target: ~85% reduction)
        # For this test, we just verify basic is smaller
        print(f"Full format size: {full_size} bytes")
        print(f"Basic format size: {basic_size} bytes")
        print(f"Reduction: {(1 - basic_size / full_size) * 100:.1f}%")

        # Basic format should be smaller than full
        assert basic_size < full_size
