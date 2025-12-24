"""Rate limiting for API calls.

PRD AC11 충족:
- 병렬 API 호출 시 과도한 요청 방지
- 1초당 최대 3개 요청 제한
"""

import asyncio
from datetime import datetime, timedelta
from collections import deque


class RateLimiter:
    """Rate limiting for API calls.

    Implements a sliding window rate limiter using asyncio.
    """

    def __init__(self, max_requests: int = 3, period: float = 1.0):
        """
        Args:
            max_requests: 기간당 최대 요청 수 (기본: 3)
            period: 제한 기간(초) (기본: 1.0)
        """
        self.max_requests = max_requests
        self.period = period
        self.requests = deque()
        self._lock = None  # Lazy initialization to avoid event loop issues
        self._loop = None  # Track which event loop created the lock

    @property
    def lock(self):
        """Lazy lock creation to bind to current event loop."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop - create one
            current_loop = None

        # Reset lock if we're in a different event loop
        if self._lock is None or self._loop != current_loop:
            self._lock = asyncio.Lock()
            self._loop = current_loop
            # Clear old requests when switching event loops
            self.requests.clear()

        return self._lock

    async def acquire(self):
        """요청 허가 획득 (필요 시 대기).

        Rate limit를 초과하면 자동으로 대기합니다.
        """
        async with self.lock:
            now = datetime.now()

            # 만료된 요청 제거 (sliding window)
            while self.requests and self.requests[0] < now - timedelta(seconds=self.period):
                self.requests.popleft()

            # Rate limit 초과 시 대기
            if len(self.requests) >= self.max_requests:
                # 가장 오래된 요청이 만료될 때까지 대기
                sleep_time = (self.requests[0] + timedelta(seconds=self.period) - now).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.requests.popleft()

            # 요청 기록
            self.requests.append(now)
