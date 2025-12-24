"""Circuit Breaker 통합 테스트.

AsyncBigKindsClient와 Circuit Breaker 통합 검증:
- 실제 API 실패 시뮬레이션
- 캐시 fallback 동작 확인
- 복구 시나리오 테스트
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.circuit_breaker import CircuitBreakerOpenError, CircuitState


@pytest.fixture
def mock_client():
    """AsyncBigKindsClient 모킹."""
    client = AsyncBigKindsClient()
    return client


class TestCircuitBreakerIntegration:
    """Circuit Breaker 통합 테스트."""

    @pytest.mark.asyncio
    async def test_search_circuit_breaker_opens_on_failures(self, mock_client):
        """검색 API 연속 실패 시 Circuit OPEN."""
        from bigkinds.models import SearchRequest

        # 검색 API가 5번 연속 실패하도록 모킹
        with patch.object(
            mock_client._client, "search", side_effect=Exception("API Error")
        ):
            request = SearchRequest(
                keyword="테스트", start_date="2025-12-01", end_date="2025-12-15"
            )

            # 5번 실패 → Circuit OPEN
            for i in range(5):
                with pytest.raises(Exception):
                    await mock_client.search(request)

            # 5번 실패 후 Circuit OPEN
            assert mock_client.search_circuit.state == CircuitState.OPEN

            # OPEN 상태에서 즉시 차단
            with pytest.raises(CircuitBreakerOpenError):
                await mock_client.search(request)

    @pytest.mark.asyncio
    async def test_search_circuit_breaker_cache_fallback(self, mock_client):
        """Circuit OPEN 시 캐시 fallback."""
        from bigkinds.models import SearchRequest, SearchResponse

        request = SearchRequest(
            keyword="AI", start_date="2025-12-01", end_date="2025-12-15"
        )

        # 1. 먼저 성공 응답으로 캐시 저장
        mock_response = SearchResponse(
            success=True,
            total_count=100,
            result_list=[],
            category_list=[],
            provider_list=[],
        )

        with patch.object(mock_client._client, "search", return_value=mock_response):
            result = await mock_client.search(request)
            assert result.total_count == 100

        # 2. API를 5번 실패시켜 Circuit OPEN
        with patch.object(
            mock_client._client, "search", side_effect=Exception("API Down")
        ):
            for _ in range(5):
                with pytest.raises(Exception):
                    await mock_client.search(request)

        assert mock_client.search_circuit.state == CircuitState.OPEN

        # 3. Circuit OPEN 상태에서도 캐시 데이터 반환
        with patch.object(
            mock_client._client, "search", side_effect=Exception("Should not be called")
        ):
            cached_result = await mock_client.search(request)
            assert cached_result.total_count == 100

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery_flow(self, mock_client):
        """Circuit Breaker 복구 시나리오."""
        from bigkinds.models import SearchRequest, SearchResponse

        request = SearchRequest(
            keyword="테스트", start_date="2025-12-01", end_date="2025-12-15"
        )

        # 1. Circuit을 OPEN으로 만들기 (failure_threshold=5)
        with patch.object(
            mock_client._client, "search", side_effect=Exception("Fail")
        ):
            for _ in range(5):
                with pytest.raises(Exception):
                    await mock_client.search(request)

        assert mock_client.search_circuit.state == CircuitState.OPEN

        # 2. recovery_timeout (30초) 대기 시뮬레이션
        # 테스트를 위해 circuit의 recovery_timeout을 짧게 설정
        mock_client.search_circuit.recovery_timeout = 1
        await asyncio.sleep(1.1)

        # 3. HALF_OPEN에서 성공 시 CLOSED로 복구
        mock_response = SearchResponse(
            success=True,
            total_count=10,
            result_list=[],
            category_list=[],
            provider_list=[],
        )

        with patch.object(mock_client._client, "search", return_value=mock_response):
            result = await mock_client.search(request)
            assert result.total_count == 10
            assert mock_client.search_circuit.state == CircuitState.CLOSED
            assert mock_client.search_circuit.failure_count == 0

    @pytest.mark.asyncio
    async def test_detail_circuit_breaker_with_cache(self, mock_client):
        """기사 상세 조회 Circuit Breaker + 캐시."""
        news_id = "test_news_123"

        # 1. 먼저 성공 응답으로 캐시 저장
        mock_detail = {
            "success": True,
            "detail": {
                "TITLE": "테스트 기사",
                "CONTENT": "본문 내용",
            },
        }

        # httpx.AsyncClient를 모킹하여 detailView API 응답 시뮬레이션
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client_instance = AsyncMock()
            mock_httpx.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock()

            # 메인 페이지, 뉴스 페이지 응답
            # response.json()을 위한 mock 설정
            detail_response = AsyncMock()
            detail_response.status_code = 200
            detail_response.url = "https://www.bigkinds.or.kr/news/detailView.do"
            detail_response.json = AsyncMock(return_value=mock_detail)
            detail_response.raise_for_status = AsyncMock()

            mock_client_instance.get.side_effect = [
                AsyncMock(status_code=200),  # 메인 페이지
                AsyncMock(status_code=200),  # 뉴스 페이지
                detail_response,  # detailView API
            ]

            result = await mock_client.get_article_detail(news_id)
            assert result["success"] is True
            assert result["detail"]["TITLE"] == "테스트 기사"

        # 2. API를 5번 실패시켜 Circuit OPEN
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client_instance = AsyncMock()
            mock_httpx.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(side_effect=Exception("API Down"))

            for _ in range(5):
                with pytest.raises(Exception):
                    news_id_fail = f"fail_{_}"
                    await mock_client.get_article_detail(news_id_fail)

        assert mock_client.detail_circuit.state == CircuitState.OPEN

        # 3. Circuit OPEN 상태에서도 캐시된 기사는 반환
        cached_result = await mock_client.get_article_detail(news_id)
        assert cached_result["success"] is True
        assert cached_result["detail"]["TITLE"] == "테스트 기사"

    @pytest.mark.asyncio
    async def test_multiple_circuits_independent_operation(self, mock_client):
        """search와 detail Circuit이 독립적으로 동작."""
        from bigkinds.models import SearchRequest

        # 1. search Circuit만 OPEN
        request = SearchRequest(
            keyword="테스트", start_date="2025-12-01", end_date="2025-12-15"
        )

        with patch.object(
            mock_client._client, "search", side_effect=Exception("Search Fail")
        ):
            for _ in range(5):
                with pytest.raises(Exception):
                    await mock_client.search(request)

        assert mock_client.search_circuit.state == CircuitState.OPEN
        assert mock_client.detail_circuit.state == CircuitState.CLOSED

        # 2. detail API는 여전히 정상 동작
        news_id = "test_news_456"
        mock_detail = {
            "success": True,
            "detail": {"TITLE": "정상 기사", "CONTENT": "내용"},
        }

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client_instance = AsyncMock()
            mock_httpx.return_value.__aenter__.return_value = mock_client_instance

            # response.json()을 위한 mock 설정
            detail_response = AsyncMock()
            detail_response.status_code = 200
            detail_response.url = "https://www.bigkinds.or.kr/news/detailView.do"
            detail_response.json = AsyncMock(return_value=mock_detail)
            detail_response.raise_for_status = AsyncMock()

            mock_client_instance.get.side_effect = [
                AsyncMock(status_code=200),
                AsyncMock(status_code=200),
                detail_response,
            ]

            result = await mock_client.get_article_detail(news_id)
            assert result["success"] is True
            assert mock_client.detail_circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_status_reporting(self, mock_client):
        """Circuit Breaker 상태 조회."""
        status = mock_client.search_circuit.get_status()

        assert status["name"] == "search_api"
        assert status["state"] == "closed"
        assert status["failure_threshold"] == 5
        assert status["recovery_timeout"] == 30

        # API 실패 후 상태 변경 확인
        from bigkinds.models import SearchRequest

        request = SearchRequest(
            keyword="테스트", start_date="2025-12-01", end_date="2025-12-15"
        )

        with patch.object(
            mock_client._client, "search", side_effect=Exception("Fail")
        ):
            for _ in range(5):
                with pytest.raises(Exception):
                    await mock_client.search(request)

        status = mock_client.search_circuit.get_status()
        assert status["state"] == "open"
        assert status["failure_count"] == 5
        assert status["last_failure_time"] is not None
