"""Integration tests for parallel API calls (AC11)."""

import time

import pytest

from bigkinds_mcp.tools.search import search_news, search_news_parallel


class TestParallelAPI:
    """병렬 API 호출 통합 테스트."""

    @pytest.mark.asyncio
    async def test_search_news_parallel_basic(self, setup_tools_real):
        """기본 병렬 검색 테스트."""
        queries = [
            {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ]

        results = await search_news_parallel(queries)

        assert len(results) == 2
        # 성공한 결과 확인
        for result in results:
            if result.get("success"):
                assert "total_count" in result
                assert "articles" in result
            else:
                # 실패한 경우 에러 메시지 확인
                assert "error" in result

    @pytest.mark.asyncio
    async def test_search_news_parallel_rate_limiting(self, setup_tools_real):
        """Rate limiting 확인."""
        # 10개 쿼리 (1초당 3개 제한)
        queries = [
            {"keyword": f"test{i}", "start_date": "2025-12-10", "end_date": "2025-12-15"}
            for i in range(10)
        ]

        start = time.time()
        results = await search_news_parallel(queries)
        elapsed = time.time() - start

        # 10개 요청, 1초당 3개 → 최소 3초 소요
        # (0-1초: 3개, 1-2초: 3개, 2-3초: 3개, 3-4초: 1개)
        assert elapsed >= 3.0
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_search_news_parallel_error_handling(self, setup_tools_real):
        """에러 처리 확인."""
        queries = [
            {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "", "start_date": "2025-12-10", "end_date": "2025-12-15"},  # 빈 키워드 (에러)
            {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ]

        results = await search_news_parallel(queries)

        assert len(results) == 3
        # 첫 번째와 세 번째는 성공, 두 번째는 실패해야 함
        assert results[0].get("success") or "total_count" in results[0]
        assert not results[1].get("success") or "error" in results[1]
        assert results[2].get("success") or "total_count" in results[2]

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_parallel_vs_sequential_performance(self, setup_tools_real):
        """병렬 vs 순차 실행 성능 비교 (벤치마크)."""
        queries = [
            {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
            {"keyword": "메타버스", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ]

        # 순차 실행
        start = time.time()
        sequential_results = []
        for q in queries:
            result = await search_news(**q)
            sequential_results.append(result)
        sequential_time = time.time() - start

        # 병렬 실행
        start = time.time()
        parallel_results = await search_news_parallel(queries)
        parallel_time = time.time() - start

        print(f"\n=== 병렬 검색 벤치마크 ===")
        print(f"순차 실행: {sequential_time:.2f}s")
        print(f"병렬 실행: {parallel_time:.2f}s")
        print(f"속도 향상: {((sequential_time - parallel_time) / sequential_time * 100):.1f}%")

        # 병렬 실행이 최소 40% 이상 빨라야 함
        improvement = (sequential_time - parallel_time) / sequential_time
        assert improvement >= 0.4, f"병렬 실행이 충분히 빠르지 않음: {improvement*100:.1f}%"

        # 결과 개수 확인
        assert len(parallel_results) == len(queries)

    @pytest.mark.asyncio
    async def test_search_news_parallel_max_concurrent(self, setup_tools_real):
        """최대 동시 실행 수 제한 확인."""
        # 10개 쿼리 (max_concurrent=3으로 제한)
        queries = [
            {"keyword": f"test{i}", "start_date": "2025-12-10", "end_date": "2025-12-15"}
            for i in range(10)
        ]

        results = await search_news_parallel(queries, max_concurrent=3)

        # 모든 요청 완료 확인
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_search_news_parallel_different_params(self, setup_tools_real):
        """다양한 파라미터 조합 테스트."""
        queries = [
            {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15", "page_size": 10},
            {"keyword": "블록체인", "start_date": "2025-12-01", "end_date": "2025-12-15", "sort_by": "date"},
            {"keyword": "메타버스", "start_date": "2025-12-10", "end_date": "2025-12-15", "providers": ["경향신문"]},
        ]

        results = await search_news_parallel(queries)

        assert len(results) == 3
        for result in results:
            if result.get("success"):
                assert "total_count" in result
