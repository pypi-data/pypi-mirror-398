"""Circuit Breaker 패턴 단위 테스트.

PRD AC16 충족 확인:
- 3가지 상태 전환 (CLOSED → OPEN → HALF_OPEN → CLOSED)
- 실패 threshold (5회) 도달 시 OPEN으로 전환
- OPEN 상태에서 즉시 에러 반환
- recovery_timeout 후 HALF_OPEN으로 전환
- HALF_OPEN에서 성공 시 CLOSED로 복구
- HALF_OPEN에서 실패 시 다시 OPEN
"""

import asyncio

import pytest

from bigkinds_mcp.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


class TestCircuitBreaker:
    """Circuit Breaker 단위 테스트."""

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self):
        """초기 상태는 CLOSED."""
        circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        assert circuit.state == CircuitState.CLOSED
        assert circuit.failure_count == 0

    @pytest.mark.asyncio
    async def test_successful_call_keeps_circuit_closed(self):
        """성공한 호출은 CLOSED 상태 유지."""
        circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        async def success_func():
            return "OK"

        result = await circuit.call(success_func)
        assert result == "OK"
        assert circuit.state == CircuitState.CLOSED
        assert circuit.failure_count == 0

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        """임계값(5회) 초과 시 OPEN으로 전환."""
        circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=1)

        async def failing_func():
            raise Exception("Simulated failure")

        # 5번 실패 → OPEN으로 전환
        for i in range(5):
            with pytest.raises(Exception, match="Simulated failure"):
                await circuit.call(failing_func)
            if i < 4:
                assert circuit.state == CircuitState.CLOSED
            else:
                assert circuit.state == CircuitState.OPEN

        assert circuit.state == CircuitState.OPEN
        assert circuit.failure_count == 5

    @pytest.mark.asyncio
    async def test_blocks_requests_when_open(self):
        """OPEN 상태일 때 요청 즉시 차단."""
        circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        async def failing_func():
            raise Exception("Fail")

        # 3번 실패 → OPEN
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit.call(failing_func)

        assert circuit.state == CircuitState.OPEN

        # OPEN 상태에서 즉시 차단 (API 호출 없음)
        call_count = 0

        async def counting_func():
            nonlocal call_count
            call_count += 1
            return "OK"

        with pytest.raises(CircuitBreakerOpenError, match="차단 상태입니다"):
            await circuit.call(counting_func)

        # API가 실제로 호출되지 않았는지 확인
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self):
        """recovery_timeout 후 HALF_OPEN으로 전환."""
        circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        async def failing_func():
            raise Exception("Fail")

        # OPEN으로 전환
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit.call(failing_func)

        assert circuit.state == CircuitState.OPEN

        # recovery_timeout (1초) 대기
        await asyncio.sleep(1.1)

        # 다음 호출 시 HALF_OPEN으로 전환 (성공 시도)
        async def success_func():
            return "Recovered"

        result = await circuit.call(success_func)
        assert result == "Recovered"
        assert circuit.state == CircuitState.CLOSED  # 성공 시 CLOSED로 복구

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self):
        """HALF_OPEN에서 성공 시 CLOSED로 복구."""
        circuit = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)

        async def failing_func():
            raise Exception("Fail")

        # OPEN으로 전환
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit.call(failing_func)

        assert circuit.state == CircuitState.OPEN

        # recovery_timeout 대기
        await asyncio.sleep(0.6)

        # HALF_OPEN에서 성공 → CLOSED
        async def success_func():
            return "OK"

        result = await circuit.call(success_func)
        assert result == "OK"
        assert circuit.state == CircuitState.CLOSED
        assert circuit.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self):
        """HALF_OPEN에서 실패 시 다시 OPEN."""
        circuit = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)

        async def failing_func():
            raise Exception("Fail")

        # OPEN으로 전환
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit.call(failing_func)

        assert circuit.state == CircuitState.OPEN

        # recovery_timeout 대기
        await asyncio.sleep(0.6)

        # HALF_OPEN에서 실패 → 다시 OPEN
        with pytest.raises(Exception):
            await circuit.call(failing_func)

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_get_status(self):
        """get_status()가 정확한 상태 정보 반환."""
        circuit = CircuitBreaker(
            failure_threshold=5, timeout=60, recovery_timeout=30, name="test_circuit"
        )

        status = circuit.get_status()
        assert status["name"] == "test_circuit"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 5
        assert status["recovery_timeout"] == 30
        assert status["last_failure_time"] is None

    @pytest.mark.asyncio
    async def test_synchronous_function_support(self):
        """동기 함수도 지원."""
        circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        def sync_func():
            return "Sync OK"

        result = await circuit.call(sync_func)
        assert result == "Sync OK"

    @pytest.mark.asyncio
    async def test_multiple_circuits_independent(self):
        """여러 Circuit Breaker가 독립적으로 동작."""
        circuit1 = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="api1")
        circuit2 = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="api2")

        async def failing_func():
            raise Exception("Fail")

        # circuit1만 OPEN
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit1.call(failing_func)

        assert circuit1.state == CircuitState.OPEN
        assert circuit2.state == CircuitState.CLOSED

        # circuit2는 여전히 정상 동작
        async def success_func():
            return "OK"

        result = await circuit2.call(success_func)
        assert result == "OK"

    @pytest.mark.asyncio
    async def test_concurrent_calls_with_lock(self):
        """동시 호출 시 lock으로 안전하게 처리."""
        circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=1)
        call_count = 0

        async def concurrent_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return "OK"

        # 10개 동시 호출
        tasks = [circuit.call(concurrent_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r == "OK" for r in results)
        assert call_count == 10
        assert circuit.state == CircuitState.CLOSED
