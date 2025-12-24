"""Circuit Breaker 패턴 구현.

PRD AC16 충족:
- 3가지 상태: CLOSED (정상), OPEN (차단), HALF_OPEN (테스트)
- OPEN 상태에서 즉시 에러 반환 (API 호출 없음)
- 실패 threshold (5회), timeout (60초), recovery timeout (30초)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit Breaker 상태."""

    CLOSED = "closed"  # 정상 상태 (요청 허용)
    OPEN = "open"  # 차단 상태 (요청 거부)
    HALF_OPEN = "half_open"  # 복구 테스트 상태 (제한적 요청 허용)


class CircuitBreakerOpenError(Exception):
    """Circuit이 OPEN 상태일 때 발생하는 에러."""

    pass


class CircuitBreaker:
    """Circuit Breaker 패턴 구현.

    API 장애 시 자동으로 요청을 차단하고, 일정 시간 후 복구를 시도합니다.

    Args:
        failure_threshold: 연속 실패 임계값 (기본: 5)
        timeout: API 타임아웃 (초, 기본: 60)
        recovery_timeout: 복구 대기 시간 (초, 기본: 30)
        name: Circuit 이름 (로깅용)

    Example:
        circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

        async def api_call():
            return await some_http_request()

        try:
            result = await circuit.call(api_call)
        except CircuitBreakerOpenError:
            # Circuit이 OPEN 상태 - 캐시에서 데이터 반환
            result = get_from_cache()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_timeout: int = 30,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Circuit Breaker를 통해 함수 호출.

        Args:
            func: 호출할 함수 (동기/비동기 모두 지원)
            *args: 함수 인자
            **kwargs: 함수 키워드 인자

        Returns:
            함수 실행 결과

        Raises:
            CircuitBreakerOpenError: Circuit이 OPEN 상태일 때
            Exception: 함수 실행 중 발생한 에러
        """
        async with self.lock:
            # Circuit 상태 확인 및 업데이트
            self._check_state()

            if self.state == CircuitState.OPEN:
                logger.warning(
                    f"[CircuitBreaker:{self.name}] Circuit is OPEN - Request blocked "
                    f"(failures: {self.failure_count}/{self.failure_threshold})"
                )
                raise CircuitBreakerOpenError(
                    f"Circuit '{self.name}'이 차단 상태입니다. "
                    f"{self.recovery_timeout}초 후 재시도하세요."
                )

        # 함수 실행 (lock 외부에서 실행하여 병렬 처리 허용)
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    def _check_state(self):
        """현재 상태 확인 및 업데이트.

        OPEN 상태에서 recovery_timeout 경과 시 HALF_OPEN으로 전환
        """
        if self.state == CircuitState.OPEN:
            # recovery_timeout 경과 시 HALF_OPEN으로 전환
            if (
                self.last_failure_time
                and datetime.now() - self.last_failure_time
                > timedelta(seconds=self.recovery_timeout)
            ):
                self._change_state(CircuitState.HALF_OPEN)

    async def _on_success(self):
        """호출 성공 시 처리.

        HALF_OPEN 상태에서 성공하면 CLOSED로 복구
        """
        if self.state == CircuitState.HALF_OPEN:
            # HALF_OPEN에서 성공 → CLOSED로 복구
            self._change_state(CircuitState.CLOSED)
            self.failure_count = 0
            logger.info(
                f"[CircuitBreaker:{self.name}] Recovered - Circuit is now CLOSED"
            )

    async def _on_failure(self):
        """호출 실패 시 처리.

        실패 횟수를 증가시키고, threshold 도달 시 OPEN으로 전환
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # HALF_OPEN에서 실패 → 다시 OPEN
            self._change_state(CircuitState.OPEN)
            logger.warning(
                f"[CircuitBreaker:{self.name}] Recovery failed - Circuit reopened"
            )
        elif self.failure_count >= self.failure_threshold:
            # CLOSED에서 임계값 초과 → OPEN
            self._change_state(CircuitState.OPEN)
            logger.error(
                f"[CircuitBreaker:{self.name}] Failure threshold reached "
                f"({self.failure_count}/{self.failure_threshold}) - Circuit opened"
            )

    def _change_state(self, new_state: CircuitState):
        """상태 전환 및 로깅."""
        old_state = self.state
        self.state = new_state
        logger.info(
            f"[CircuitBreaker:{self.name}] State changed: {old_state.value} → {new_state.value}"
        )

    def get_status(self) -> dict:
        """Circuit Breaker 현재 상태 조회.

        Returns:
            상태 정보 딕셔너리
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "recovery_timeout": self.recovery_timeout,
        }
