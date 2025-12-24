"""Unit tests for RateLimiter (AC11)."""

import asyncio
import time

import pytest

from bigkinds_mcp.core.rate_limiter import RateLimiter


class TestRateLimiter:
    """RateLimiter 단위 테스트."""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """기본 동작 테스트: 3개 요청은 즉시 통과."""
        limiter = RateLimiter(max_requests=3, period=1.0)

        start = time.time()
        for _ in range(3):
            await limiter.acquire()
        elapsed = time.time() - start

        # 3개 요청은 대기 없이 즉시 통과
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_limit(self):
        """Rate limit 초과 시 대기."""
        limiter = RateLimiter(max_requests=3, period=1.0)

        start = time.time()
        # 4번째 요청은 대기해야 함
        for _ in range(4):
            await limiter.acquire()
        elapsed = time.time() - start

        # 4번째 요청은 최소 1초 대기
        assert elapsed >= 1.0

    @pytest.mark.asyncio
    async def test_rate_limiter_sliding_window(self):
        """Sliding window 동작 확인."""
        limiter = RateLimiter(max_requests=3, period=1.0)

        # 3개 요청
        for _ in range(3):
            await limiter.acquire()

        # 0.5초 대기
        await asyncio.sleep(0.5)

        # 4번째 요청 (첫 번째 요청이 만료되지 않아 대기)
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # 최소 0.5초 대기 (1초 - 0.5초 = 0.5초)
        assert elapsed >= 0.4  # 약간의 오차 허용

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent(self):
        """동시 요청 처리."""
        limiter = RateLimiter(max_requests=3, period=1.0)

        async def make_request():
            await limiter.acquire()
            return time.time()

        start = time.time()
        # 10개 동시 요청
        results = await asyncio.gather(*[make_request() for _ in range(10)])
        elapsed = time.time() - start

        # 10개 요청, 1초당 3개 → 약 2-3초 소요 (sliding window로 약간 더 효율적)
        # (0-1초: 3개, 1-2초: 3개, 2-3초: 3개, 나머지: 1개)
        assert elapsed >= 2.0  # 최소 2초 (약간의 오차 허용)
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_rate_limiter_custom_settings(self):
        """커스텀 설정 테스트."""
        # 5개 요청/2초
        limiter = RateLimiter(max_requests=5, period=2.0)

        start = time.time()
        for _ in range(6):
            await limiter.acquire()
        elapsed = time.time() - start

        # 6번째 요청은 최소 2초 대기
        assert elapsed >= 2.0
