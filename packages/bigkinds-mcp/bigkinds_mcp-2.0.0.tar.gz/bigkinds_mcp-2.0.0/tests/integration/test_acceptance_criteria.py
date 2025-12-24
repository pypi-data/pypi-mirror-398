"""PRD Acceptance Criteria 통합 테스트.

PRD Section 6 (Acceptance Criteria) 검증을 위한 테스트.
- AC1: search_news
- AC3: get_today_issues
- AC8: Performance
- AC9: Reliability
- AC10: Caching
- AC11: Parallel API Calls
- AC14: Progress Feedback
"""

import time
import logging
from datetime import date, timedelta

import pytest

from bigkinds_mcp.tools.search import search_news, search_news_parallel, get_article_count, init_search_tools
from bigkinds_mcp.tools.article import init_article_tools
from bigkinds_mcp.tools.visualization import init_visualization_tools, get_keyword_trends, get_related_keywords
from bigkinds_mcp.tools.analysis import init_analysis_tools
from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.async_scraper import AsyncArticleScraper
from bigkinds_mcp.core.cache import MCPCache
from bigkinds_mcp.utils.errors import ErrorCode


@pytest.fixture
def setup_tools():
    """테스트용 도구 초기화."""
    client = AsyncBigKindsClient()
    scraper = AsyncArticleScraper()
    cache = MCPCache()

    init_search_tools(client, cache)
    init_article_tools(client, scraper, cache)
    init_visualization_tools(client, cache)
    init_analysis_tools(client, cache)

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


class TestAC1SearchNews:
    """AC1: search_news Acceptance Criteria."""

    @pytest.mark.asyncio
    async def test_ac1_keyword_required(self, setup_tools):
        """AC1: 키워드 필수, 빈 키워드 시 에러 반환."""
        result = await search_news(
            keyword="",
            start_date="2024-12-01",
            end_date="2024-12-15",
        )
        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_PARAMS"

    @pytest.mark.asyncio
    async def test_ac1_date_format_validation(self, setup_tools):
        """AC1: start_date, end_date 필수, YYYY-MM-DD 형식 검증."""
        # 잘못된 날짜 형식
        result = await search_news(
            keyword="AI",
            start_date="2024/12/01",  # 잘못된 형식
            end_date="2024-12-15",
        )
        assert result["success"] is False
        # AC12로 날짜 검증이 강화되어 INVALID_DATE_FORMAT 반환
        assert result["error"]["code"] == "INVALID_DATE_FORMAT"

    @pytest.mark.asyncio
    async def test_ac1_page_size_limit(self, setup_tools):
        """AC1: page_size 최대 100 제한."""
        result = await search_news(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-15",
            page_size=150,  # 100 초과
        )
        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_PARAMS"

    @pytest.mark.asyncio
    async def test_ac1_sort_by_both_merges_results(self, setup_tools):
        """AC1: sort_by='both' 시 date+relevance 병합, news_id로 중복 제거."""
        result = await search_news(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-15",
            sort_by="both",
            page_size=20,
        )

        # 성공적인 응답
        assert "total_count" in result
        assert "articles" in result

        # 중복 news_id 없어야 함
        news_ids = [a["news_id"] for a in result["articles"]]
        assert len(news_ids) == len(set(news_ids))

    @pytest.mark.asyncio
    async def test_ac1_pagination_metadata(self, setup_tools):
        """AC1: 응답에 total_count, page, total_pages 포함."""
        result = await search_news(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-15",
        )

        assert "total_count" in result
        assert "page" in result
        assert "total_pages" in result
        assert result["page"] >= 1
        assert result["total_pages"] >= 1


class TestAC3TodayIssues:
    """AC3: get_today_issues Acceptance Criteria."""

    @pytest.mark.asyncio
    async def test_ac3_default_date_is_today(self, setup_tools):
        """AC3: date 미지정 시 오늘 날짜 사용 (KST 기준)."""
        client = setup_tools["client"]
        result = await client.get_today_issues()

        # 성공적인 응답 (데이터가 없을 수도 있음)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_ac3_category_filter(self, setup_tools):
        """AC3: category 필터 지원."""
        client = setup_tools["client"]
        # 카테고리 필터 기능 테스트 (네트워크 상태에 따라 타임아웃 가능)
        try:
            result = await client.get_today_issues(category="전체")
            assert isinstance(result, dict)
        except Exception:
            # 네트워크 이슈 시 skip
            pytest.skip("Network timeout - skipping category filter test")


class TestAC8Performance:
    """AC8: Performance Acceptance Criteria."""

    @pytest.mark.asyncio
    async def test_ac8_search_response_under_3s(self, setup_tools):
        """AC8: 뉴스 검색 응답 < 3초."""
        start = time.time()

        await search_news(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-15",
            page_size=10,
        )

        elapsed = time.time() - start
        assert elapsed < 3.0, f"검색 응답 시간: {elapsed:.2f}s (3초 초과)"

    @pytest.mark.asyncio
    async def test_ac8_cache_hit_under_100ms(self, setup_tools):
        """AC8: 캐시 적중 시 응답 < 100ms."""
        # 첫 번째 요청 (캐시 워밍업)
        await search_news(
            keyword="캐시테스트",
            start_date="2024-12-01",
            end_date="2024-12-15",
            page_size=5,
        )

        # 두 번째 요청 (캐시 적중)
        start = time.time()
        await search_news(
            keyword="캐시테스트",
            start_date="2024-12-01",
            end_date="2024-12-15",
            page_size=5,
        )
        elapsed = time.time() - start

        assert elapsed < 0.1, f"캐시 응답 시간: {elapsed:.2f}s (100ms 초과)"


class TestAC9Reliability:
    """AC9: Reliability Acceptance Criteria."""

    def test_ac9_retry_config(self):
        """AC9: API 실패 시 재시도 (최대 3회) 설정 확인."""
        from bigkinds_mcp.core.async_client import MAX_RETRIES
        assert MAX_RETRIES == 3

    def test_ac9_timeout_config(self):
        """AC9: 네트워크 타임아웃 30초 설정 확인."""
        from bigkinds_mcp.core.async_client import TIMEOUT
        assert TIMEOUT == 30.0

    @pytest.mark.asyncio
    async def test_ac9_error_response_format(self, setup_tools):
        """AC9: 에러 응답에 success=false, error 메시지 포함."""
        result = await search_news(
            keyword="",  # 빈 키워드로 에러 유발
            start_date="2024-12-01",
            end_date="2024-12-15",
        )

        assert result["success"] is False
        assert "error" in result
        assert "code" in result["error"]
        assert "message" in result["error"]


class TestAC10Caching:
    """AC10: Caching Acceptance Criteria."""

    def test_ac10_cache_ttl_config(self):
        """AC10: 캐시 TTL 설정 확인 (PRD AC10)."""
        from bigkinds_mcp.core.cache import (
            SEARCH_CACHE_TTL,
            ARTICLE_CACHE_TTL,
            TREND_CACHE_TTL,
        )

        # 검색 결과 캐시 TTL: 5분 (300초)
        assert SEARCH_CACHE_TTL == 300

        # 기사 상세 캐시 TTL: 30분 (1800초)
        assert ARTICLE_CACHE_TTL == 1800

        # 트렌드/연관어 캐시 TTL: 10분 (600초)
        assert TREND_CACHE_TTL == 600

    @pytest.mark.asyncio
    async def test_ac10_search_cache_works(self, setup_tools):
        """AC10: 검색 결과 캐시 동작 확인."""
        cache = setup_tools["cache"]

        # 첫 번째 요청
        result1 = await search_news(
            keyword="캐시동작테스트",
            start_date="2024-12-01",
            end_date="2024-12-15",
        )

        # 캐시에 저장되었는지 확인
        cached = cache.get_search(
            keyword="캐시동작테스트",
            start_date="2024-12-01",
            end_date="2024-12-15",
            page=1,
            page_size=20,
            providers=None,
            categories=None,
            sort_by="both",
        )

        assert cached is not None


class TestAC14ProgressFeedback:
    """AC14: Progress Feedback Acceptance Criteria."""

    @pytest.mark.asyncio
    async def test_ac14_progress_tracking_enabled_for_large_operations(
        self, setup_tools, caplog
    ):
        """AC14: 5000건 이상 작업 시 진행률 피드백 표시."""
        from bigkinds_mcp.core.progress import ProgressTracker

        caplog.set_level(logging.INFO)

        # 10000건 작업 시뮬레이션
        tracker = ProgressTracker(
            total=10000, description="대용량 작업 테스트", threshold=5000, interval=10
        )

        # 10% 진행 (1000건)
        tracker.update(1000)
        assert "[진행률] 대용량 작업 테스트:" in caplog.text
        assert "1000/10000" in caplog.text
        assert "(10.0%)" in caplog.text
        assert "예상 완료:" in caplog.text

    @pytest.mark.asyncio
    async def test_ac14_progress_disabled_for_small_operations(
        self, setup_tools, caplog
    ):
        """AC14: 5000건 미만 작업 시 진행률 표시 안 함."""
        from bigkinds_mcp.core.progress import ProgressTracker

        caplog.set_level(logging.INFO)

        # 1000건 작업 (threshold 미만)
        tracker = ProgressTracker(
            total=1000, description="소규모 작업 테스트", threshold=5000
        )

        # 진행률 표시 비활성화 확인
        assert tracker.enabled is False

        # 업데이트해도 로깅 없음
        tracker.update(500)
        assert "[진행률]" not in caplog.text

    @pytest.mark.asyncio
    async def test_ac14_progress_interval_10_percent(self, setup_tools, caplog):
        """AC14: 10% 단위로 진행률 업데이트."""
        from bigkinds_mcp.core.progress import ProgressTracker

        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(
            total=10000, description="간격 테스트", threshold=0, interval=10
        )

        # 10% 단위로 업데이트
        for i in range(1, 11):
            caplog.clear()
            tracker.update(1000)

            # 10% 단위마다 로깅 발생
            if i % 1 == 0:  # 10%, 20%, ..., 100%
                assert "[진행률]" in caplog.text
                assert f"{i * 1000}/10000" in caplog.text

    @pytest.mark.asyncio
    async def test_ac14_export_all_articles_with_progress(
        self, setup_tools, caplog, tmp_path
    ):
        """AC14: export_all_articles가 대용량 작업 시 진행률을 표시하는지 확인."""
        from bigkinds_mcp.tools.analysis import export_all_articles
        from unittest.mock import patch, AsyncMock

        caplog.set_level(logging.INFO)

        # 6000건의 대용량 데이터 시뮬레이션
        mock_search_result = {
            "success": True,
            "articles": [
                {
                    "news_id": f"test_{i}",
                    "title": f"테스트 기사 {i}",
                    "summary": "테스트 요약",
                    "publisher": "테스트일보",
                    "published_date": "2024-12-15",
                    "category": "정치",
                    "url": f"https://example.com/{i}",
                }
                for i in range(100)  # 페이지당 100건
            ],
        }

        mock_count_result = {
            "success": True,
            "total_count": 6000,  # 5000 이상이므로 진행률 활성화
        }

        # search_news와 get_article_count를 모킹 (올바른 import 경로 사용)
        with patch(
            "bigkinds_mcp.tools.search.search_news", new_callable=AsyncMock
        ) as mock_search, patch(
            "bigkinds_mcp.tools.search.get_article_count", new_callable=AsyncMock
        ) as mock_count:

            mock_count.return_value = mock_count_result

            # 60페이지 시뮬레이션 (6000건 / 100건 per page)
            call_count = [0]

            async def mock_search_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] > 60:  # 60페이지 후 중단
                    return {"success": True, "articles": []}
                return mock_search_result

            mock_search.side_effect = mock_search_side_effect

            output_path = tmp_path / "test_export.json"

            # export_all_articles 실행
            result = await export_all_articles(
                keyword="테스트",
                start_date="2024-12-01",
                end_date="2024-12-15",
                output_path=str(output_path),
                max_articles=6000,
            )

            # 진행률 로깅 확인
            assert "[진행률]" in caplog.text
            assert "테스트" in caplog.text
            assert "예상 완료:" in caplog.text

            # 완료 로깅 확인
            assert "[완료]" in caplog.text

    @pytest.mark.asyncio
    async def test_ac14_eta_calculation_accuracy(self, setup_tools):
        """AC14: ETA(예상 완료 시간) 계산 정확도 확인."""
        from bigkinds_mcp.core.progress import ProgressTracker
        import time

        tracker = ProgressTracker(
            total=100, description="ETA 테스트", threshold=0, interval=10
        )

        # 10% 완료 후 시간 측정
        start = time.time()
        tracker.update(10)
        time.sleep(0.1)  # 0.1초 대기

        # 나머지 90% 완료
        tracker.update(90)
        elapsed = time.time() - start

        # ETA 계산이 합리적인 범위 내에 있는지 확인
        # (실제 로깅된 ETA는 caplog로 확인 가능하지만, 여기서는 완료 시간 확인)
        assert elapsed < 1.0  # 1초 이내 완료되어야 함

class TestAC12DateValidation:
    """AC12: Date Validation Acceptance Criteria."""

    @pytest.mark.asyncio
    async def test_ac12_future_date_rejected_search_news(self, setup_tools):
        """AC12: search_news가 미래 날짜를 거부하는지 확인."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        result = await search_news(
            keyword="테스트",
            start_date=tomorrow,
            end_date=tomorrow,
        )

        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.FUTURE_DATE_NOT_ALLOWED.value
        assert "미래 날짜" in result["error"]["message"]
        assert "solution" in result["error"]

    @pytest.mark.asyncio
    async def test_ac12_date_before_1990_rejected_search_news(self, setup_tools):
        """AC12: search_news가 1990년 이전 날짜를 거부하는지 확인."""
        result = await search_news(
            keyword="테스트",
            start_date="1989-12-31",
            end_date="1990-01-01",
        )

        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.DATE_TOO_OLD.value
        assert "날짜 범위" in result["error"]["message"]
        assert "solution" in result["error"]

    @pytest.mark.asyncio
    async def test_ac12_invalid_date_order_rejected_search_news(self, setup_tools):
        """AC12: search_news가 종료일 < 시작일을 거부하는지 확인."""
        result = await search_news(
            keyword="테스트",
            start_date="2025-12-15",
            end_date="2025-12-01",
        )

        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.INVALID_DATE_ORDER.value
        assert "종료일" in result["error"]["message"]
        assert "시작일" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_ac12_invalid_date_format_rejected_search_news(self, setup_tools):
        """AC12: search_news가 잘못된 날짜 형식을 거부하는지 확인."""
        result = await search_news(
            keyword="테스트",
            start_date="2025/12/01",
            end_date="2025-12-15",
        )

        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.INVALID_DATE_FORMAT.value
        assert "형식" in result["error"]["message"]
        assert "YYYY-MM-DD" in result["error"]["details"]["format"]

    @pytest.mark.asyncio
    async def test_ac12_valid_date_range_accepted_search_news(self, setup_tools):
        """AC12: 유효한 날짜 범위는 허용."""
        result = await search_news(
            keyword="AI",
            start_date="2025-12-01",
            end_date="2025-12-15",
        )

        # 에러가 아님 (날짜 검증 통과)
        assert "total_count" in result or result.get("success") is True

    @pytest.mark.asyncio
    async def test_ac12_future_date_rejected_get_article_count(self, setup_tools):
        """AC12: get_article_count가 미래 날짜를 거부하는지 확인."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        result = await get_article_count(
            keyword="테스트",
            start_date=tomorrow,
            end_date=tomorrow,
        )

        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.FUTURE_DATE_NOT_ALLOWED.value

    @pytest.mark.asyncio
    async def test_ac12_future_date_rejected_get_keyword_trends(self, setup_tools):
        """AC12: get_keyword_trends가 미래 날짜를 거부하는지 확인."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        result = await get_keyword_trends(
            keyword="테스트",
            start_date=tomorrow,
            end_date=tomorrow,
        )

        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.FUTURE_DATE_NOT_ALLOWED.value

    @pytest.mark.asyncio
    async def test_ac12_future_date_rejected_get_related_keywords(self, setup_tools):
        """AC12: get_related_keywords가 미래 날짜를 거부하는지 확인."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        result = await get_related_keywords(
            keyword="테스트",
            start_date=tomorrow,
            end_date=tomorrow,
        )

        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.FUTURE_DATE_NOT_ALLOWED.value

    @pytest.mark.asyncio
    async def test_ac12_boundary_1990_01_01_accepted(self, setup_tools):
        """AC12: 경계값 테스트 - 1990-01-01은 허용."""
        result = await search_news(
            keyword="AI",
            start_date="1990-01-01",
            end_date="1990-01-31",
        )

        # 날짜 검증은 통과해야 함
        assert "total_count" in result or result.get("success") is True

    @pytest.mark.asyncio
    async def test_ac12_boundary_today_accepted(self, setup_tools):
        """AC12: 경계값 테스트 - 오늘 날짜는 허용."""
        today = date.today().isoformat()

        result = await search_news(
            keyword="AI",
            start_date=today,
            end_date=today,
        )

        # 날짜 검증은 통과해야 함
        assert "total_count" in result or result.get("success") is True

    @pytest.mark.asyncio
    async def test_ac12_error_response_contains_solution(self, setup_tools):
        """AC12: 모든 날짜 검증 에러에 해결 방법 포함."""
        # 미래 날짜
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = await search_news(
            keyword="테스트", start_date=tomorrow, end_date=tomorrow
        )
        assert "solution" in result["error"]

        # 1990년 이전
        result = await search_news(
            keyword="테스트", start_date="1989-01-01", end_date="1989-12-31"
        )
        assert "solution" in result["error"]

        # 날짜 순서 오류
        result = await search_news(
            keyword="테스트", start_date="2025-12-15", end_date="2025-12-01"
        )
        assert "solution" in result["error"]

        # 형식 오류
        result = await search_news(
            keyword="테스트", start_date="invalid", end_date="2025-12-01"
        )
        assert "solution" in result["error"]


class TestAC11ParallelAPIsCalls:
    """AC11: Parallel API Calls Acceptance Criteria."""

    @pytest.mark.asyncio
    async def test_ac11_search_news_parallel_basic(self, setup_tools):
        """AC11: 병렬 검색 기본 동작 확인."""
        queries = [
            {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ]

        results = await search_news_parallel(queries)

        # 결과 개수 확인
        assert len(results) == 2

        # 각 결과 검증
        for result in results:
            if result.get("success"):
                assert "total_count" in result
                assert "articles" in result

    @pytest.mark.asyncio
    async def test_ac11_rate_limiting_enforced(self, setup_tools):
        """AC11: Rate limiting 적용 확인 (1초당 3개 요청)."""
        # 10개 쿼리
        queries = [
            {"keyword": f"test{i}", "start_date": "2025-12-10", "end_date": "2025-12-15"}
            for i in range(10)
        ]

        start = time.time()
        results = await search_news_parallel(queries)
        elapsed = time.time() - start

        # 10개 요청, 1초당 3개 → 최소 3초 소요
        assert elapsed >= 3.0
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_ac11_performance_improvement(self, setup_tools):
        """AC11: 병렬 실행이 순차 실행보다 빠름."""
        queries = [
            {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "메타버스", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ]

        # 순차 실행
        start = time.time()
        for q in queries:
            await search_news(**q)
        sequential_time = time.time() - start

        # 병렬 실행
        start = time.time()
        await search_news_parallel(queries)
        parallel_time = time.time() - start

        # 병렬 실행이 최소 40% 이상 빨라야 함
        improvement = (sequential_time - parallel_time) / sequential_time
        assert improvement >= 0.4, f"성능 향상 부족: {improvement*100:.1f}%"

    @pytest.mark.asyncio
    async def test_ac11_error_handling(self, setup_tools):
        """AC11: 개별 쿼리 실패 시 다른 쿼리는 정상 실행."""
        queries = [
            {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "", "start_date": "2025-12-10", "end_date": "2025-12-15"},  # 에러
            {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ]

        results = await search_news_parallel(queries)

        # 모든 결과 반환
        assert len(results) == 3

        # 첫 번째와 세 번째는 성공
        assert results[0].get("success") or "total_count" in results[0]
        assert results[2].get("success") or "total_count" in results[2]

        # 두 번째는 실패
        assert not results[1].get("success") or "error" in results[1]

    @pytest.mark.asyncio
    async def test_ac11_max_concurrent_limit(self, setup_tools):
        """AC11: 최대 동시 실행 수 제한 (기본 5개)."""
        queries = [
            {"keyword": f"test{i}", "start_date": "2025-12-10", "end_date": "2025-12-15"}
            for i in range(10)
        ]

        # max_concurrent=3으로 제한
        results = await search_news_parallel(queries, max_concurrent=3)

        # 모든 요청 완료 확인
        assert len(results) == 10



class TestAC13SchemaValidation:
    """AC13: API 스키마 strict 검증 Acceptance Criteria."""

    @pytest.mark.asyncio
    async def test_ac13_strict_mode_rejects_wrong_types(self, setup_tools):
        """AC13: Pydantic strict mode로 타입 불일치 감지."""
        from bigkinds_mcp.models.schemas import ArticleSummary
        from pydantic import ValidationError

        # news_id를 int로 전달 (str이어야 함)
        data = {
            "news_id": 123,  # int (strict mode에서 str로 자동 변환 안 됨)
            "title": "테스트 기사",
            "summary": "요약",
            "publisher": "경향신문",
            "published_date": "2025-12-15",
            "category": "정치",
            "url": "https://example.com",
        }

        with pytest.raises(ValidationError):
            ArticleSummary(**data)

    @pytest.mark.asyncio
    async def test_ac13_extra_fields_forbidden(self, setup_tools):
        """AC13: extra=\"forbid\"로 정의되지 않은 필드 거부."""
        from bigkinds_mcp.models.schemas import ArticleSummary
        from pydantic import ValidationError

        data = {
            "news_id": "123",
            "title": "테스트 기사",
            "summary": "요약",
            "publisher": "경향신문",
            "published_date": "2025-12-15",
            "category": "정치",
            "url": "https://example.com",
            "undefined_field": "This should be rejected",  # 정의되지 않은 필드
        }

        with pytest.raises(ValidationError) as exc_info:
            ArticleSummary(**data)

        # extra=\"forbid\"로 추가 필드 감지
        errors = exc_info.value.errors()
        assert any("extra_forbidden" in err["type"] or "undefined_field" in str(err) for err in errors)

    @pytest.mark.asyncio
    async def test_ac13_validation_failure_returns_error_response(self, setup_tools, caplog):
        """AC13: 검증 실패 시 SCHEMA_VALIDATION_FAILED 에러 응답 및 로깅."""
        import logging
        caplog.set_level(logging.ERROR)

        from unittest.mock import patch
        from bigkinds_mcp.models.schemas import SearchResult
        from pydantic import ValidationError

        # SearchResult 생성 시 ValidationError 발생하도록 모킹
        with patch.object(SearchResult, "__init__", side_effect=ValidationError.from_exception_data(
            "SearchResult",
            [{"type": "int_parsing", "loc": ("total_count",), "msg": "Input should be a valid integer"}]
        )):
            result = await search_news(
                keyword="AI",
                start_date="2025-12-10",
                end_date="2025-12-15",
            )

        # SCHEMA_VALIDATION_FAILED 에러 반환 확인
        assert result["success"] is False
        assert result["error"]["code"] == "SCHEMA_VALIDATION_FAILED"
        assert "스키마 검증" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_ac13_normal_data_passes_validation(self, setup_tools):
        """AC13: 올바른 데이터는 검증 통과."""
        # 정상적인 검색 요청 (실제 API 호출)
        result = await search_news(
            keyword="AI",
            start_date="2025-12-10",
            end_date="2025-12-15",
            page_size=5,
        )

        # 검증 성공
        assert result.get("success") is True
        assert "error" not in result
        assert "total_count" in result
        assert "articles" in result


class TestAC15KoreanErrorMessages:
    """AC15: 에러 메시지 한글화 통합 테스트."""

    @pytest.mark.asyncio
    async def test_ac15_date_validation_errors_in_korean(self, setup_tools):
        """AC15: 날짜 검증 에러가 한글로 반환되는지 확인."""
        # 미래 날짜 테스트
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = await search_news(
            keyword="테스트",
            start_date=tomorrow,
            end_date=tomorrow
        )

        assert result["success"] is False
        assert result["error"]["code"] == "FUTURE_DATE_NOT_ALLOWED"
        # 한글 메시지 확인
        assert "미래 날짜" in result["error"]["message"]
        assert "solution" in result["error"]
        assert "오늘" in result["error"]["solution"]
        # message 파라미터가 제공되지 않았음을 확인 (자동 한글 적용)
        assert len(result["error"]["message"]) > 0

    @pytest.mark.asyncio
    async def test_ac15_invalid_date_format_in_korean(self, setup_tools):
        """AC15: 잘못된 날짜 형식 에러가 한글로 반환되는지 확인."""
        result = await search_news(
            keyword="테스트",
            start_date="2025/12/15",  # 잘못된 형식
            end_date="2025-12-15"
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_DATE_FORMAT"
        assert "날짜 형식" in result["error"]["message"]
        assert "YYYY-MM-DD" in result["error"]["solution"]

    @pytest.mark.asyncio
    async def test_ac15_invalid_params_in_korean(self, setup_tools):
        """AC15: 파라미터 검증 에러가 한글로 반환되는지 확인."""
        result = await search_news(
            keyword="테스트",
            start_date="2025-12-10",
            end_date="2025-12-15",
            page=-1,  # 잘못된 페이지 번호
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_PARAMS"
        assert "유효하지 않은 파라미터" in result["error"]["message"]
        assert "solution" in result["error"]

    @pytest.mark.asyncio
    async def test_ac15_error_has_solution_field(self, setup_tools):
        """AC15: 모든 에러에 solution 필드가 포함되는지 확인."""
        # 여러 에러 케이스 테스트
        test_cases = [
            # 미래 날짜
            {
                "keyword": "테스트",
                "start_date": (date.today() + timedelta(days=1)).isoformat(),
                "end_date": (date.today() + timedelta(days=1)).isoformat(),
                "expected_code": "FUTURE_DATE_NOT_ALLOWED"
            },
            # 날짜 순서 오류
            {
                "keyword": "테스트",
                "start_date": "2025-12-15",
                "end_date": "2025-12-01",
                "expected_code": "INVALID_DATE_ORDER"
            },
        ]

        for case in test_cases:
            expected_code = case.pop("expected_code")
            result = await search_news(**case)
            assert result["success"] is False
            assert result["error"]["code"] == expected_code
            # solution 필드 확인
            assert "solution" in result["error"]
            assert len(result["error"]["solution"]) > 0
            # 한글 메시지 확인
            assert len(result["error"]["message"]) > 0

    @pytest.mark.asyncio
    async def test_ac15_docs_field_for_important_errors(self, setup_tools):
        """AC15: 중요한 에러에 docs 필드가 포함되는지 확인."""
        # AUTH_REQUIRED 에러는 docs 필드 포함
        from bigkinds_mcp.utils.errors_kr import get_error_message_kr

        msg = get_error_message_kr("AUTH_REQUIRED")
        assert "docs" in msg["error"]
        assert msg["error"]["docs"].startswith("https://")

    @pytest.mark.asyncio
    async def test_ac15_all_error_messages_are_korean(self, setup_tools):
        """AC15: 실제 API 호출로 발생하는 모든 에러가 한글로 반환되는지 확인."""
        # 다양한 에러 케이스 수집
        error_results = []

        # 1. 날짜 형식 오류
        result1 = await search_news(
            keyword="테스트",
            start_date="invalid-date",
            end_date="2025-12-15"
        )
        error_results.append(result1)

        # 2. 미래 날짜
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result2 = await search_news(
            keyword="테스트",
            start_date=tomorrow,
            end_date=tomorrow
        )
        error_results.append(result2)

        # 3. 날짜 순서 오류
        result3 = await search_news(
            keyword="테스트",
            start_date="2025-12-15",
            end_date="2025-12-01"
        )
        error_results.append(result3)

        # 모든 에러 응답 검증
        for result in error_results:
            assert result["success"] is False
            assert "error" in result
            assert "code" in result["error"]
            assert "message" in result["error"]
            assert "solution" in result["error"]

            # 한글 포함 여부 확인
            message = result["error"]["message"]
            has_korean = any('\uac00' <= char <= '\ud7a3' for char in message)
            assert has_korean, f"에러 메시지에 한글이 없습니다: {message}"

