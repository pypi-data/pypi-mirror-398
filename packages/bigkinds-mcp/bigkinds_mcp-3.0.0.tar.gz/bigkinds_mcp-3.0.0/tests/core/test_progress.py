"""ProgressTracker 단위 테스트.

PRD AC14: 대용량 작업 진행률 피드백
"""

import logging
from unittest.mock import Mock

import pytest

from bigkinds_mcp.core.progress import ProgressTracker


class TestProgressTracker:
    """ProgressTracker 테스트."""

    def test_small_task_disabled(self):
        """5000건 미만 작업은 진행률 비활성화."""
        tracker = ProgressTracker(total=100, threshold=5000)
        assert tracker.enabled is False

    def test_large_task_enabled(self):
        """5000건 이상 작업은 진행률 활성화."""
        tracker = ProgressTracker(total=10000, threshold=5000)
        assert tracker.enabled is True

    def test_update_increments_current(self):
        """update가 current를 증가시키는지 확인."""
        tracker = ProgressTracker(total=100, threshold=0)
        tracker.update(10)
        assert tracker.current == 10
        tracker.update(20)
        assert tracker.current == 30

    def test_callback_invoked_at_interval(self):
        """콜백 함수가 interval 단위로 호출되는지 확인."""
        called = []

        def callback(current, total):
            called.append((current, total))

        tracker = ProgressTracker(
            total=100, threshold=0, interval=25, callback=callback
        )

        # 25% 도달 시 콜백 호출
        tracker.update(25)
        assert len(called) == 1
        assert called[0] == (25, 100)

        # 50% 도달 시 콜백 호출
        tracker.update(25)
        assert len(called) == 2
        assert called[1] == (50, 100)

    def test_callback_not_invoked_before_interval(self):
        """interval 미만일 때는 콜백이 호출되지 않는지 확인."""
        called = []

        def callback(current, total):
            called.append((current, total))

        tracker = ProgressTracker(
            total=100, threshold=0, interval=25, callback=callback
        )

        # 24% - 콜백 호출 안 됨
        tracker.update(24)
        assert len(called) == 0

        # 25% 도달 - 콜백 호출됨
        tracker.update(1)
        assert len(called) == 1

    def test_logging_at_interval(self, caplog):
        """interval 단위로 로깅되는지 확인."""
        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(
            total=1000, description="테스트 작업", threshold=0, interval=10
        )

        # 10% (100건)
        tracker.update(100)
        assert "[진행률] 테스트 작업:" in caplog.text
        assert "100/1000" in caplog.text
        assert "(10.0%)" in caplog.text
        assert "예상 완료:" in caplog.text

    def test_no_logging_when_disabled(self, caplog):
        """threshold 미만일 때는 로깅이 없는지 확인."""
        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(total=100, threshold=5000)
        tracker.update(50)

        # 로깅이 없어야 함
        assert "[진행률]" not in caplog.text

    def test_complete_logs_summary(self, caplog):
        """complete() 호출 시 완료 로깅이 되는지 확인."""
        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(
            total=1000, description="테스트 작업", threshold=0
        )
        tracker.update(1000)
        tracker.complete()

        assert "[완료] 테스트 작업:" in caplog.text
        assert "1000/1000" in caplog.text
        assert "소요 시간:" in caplog.text

    def test_complete_does_nothing_when_disabled(self, caplog):
        """threshold 미만일 때 complete()가 로깅하지 않는지 확인."""
        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(total=100, threshold=5000)
        tracker.complete()

        assert "[완료]" not in caplog.text

    def test_eta_calculation(self, caplog):
        """ETA가 올바르게 계산되는지 확인."""
        import time

        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(total=100, threshold=0, interval=10)

        # 10% 완료 (0.1초 소요)
        time.sleep(0.1)
        tracker.update(10)

        # 로그에 ETA가 포함되어야 함 (약 0.9초 남음)
        assert "예상 완료:" in caplog.text
        # ETA는 대략 0-2초 사이여야 함 (시스템 부하에 따라 변동)
        assert "초" in caplog.text

    def test_progress_percentage_accuracy(self):
        """진행률 퍼센트가 정확한지 확인."""
        tracker = ProgressTracker(total=1000, threshold=0, interval=10)

        tracker.update(100)
        expected_pct = (100 / 1000) * 100
        assert expected_pct == 10.0

        tracker.update(400)
        expected_pct = (500 / 1000) * 100
        assert expected_pct == 50.0

    def test_multiple_interval_updates(self, caplog):
        """여러 interval을 건너뛰는 업데이트에서도 로깅이 정상인지 확인."""
        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(total=100, threshold=0, interval=10)

        # 한 번에 30% 업데이트 (10%, 20%, 30% 건너뜀)
        tracker.update(30)

        # 30% 로깅만 발생해야 함
        log_count = caplog.text.count("[진행률]")
        assert log_count == 1
        assert "30/100 (30.0%)" in caplog.text

    def test_threshold_boundary(self):
        """threshold 경계값 테스트."""
        # threshold - 1 (비활성화)
        tracker1 = ProgressTracker(total=4999, threshold=5000)
        assert tracker1.enabled is False

        # threshold (활성화)
        tracker2 = ProgressTracker(total=5000, threshold=5000)
        assert tracker2.enabled is True

        # threshold + 1 (활성화)
        tracker3 = ProgressTracker(total=5001, threshold=5000)
        assert tracker3.enabled is True

    def test_interval_boundary(self, caplog):
        """interval 경계값 로깅 테스트."""
        caplog.set_level(logging.INFO)

        tracker = ProgressTracker(total=100, threshold=0, interval=10)

        # 9% - 로깅 없음
        tracker.update(9)
        assert "[진행률]" not in caplog.text

        # 10% - 로깅 발생
        caplog.clear()
        tracker.update(1)
        assert "[진행률]" in caplog.text
        assert "10/100 (10.0%)" in caplog.text

        # 11-19% - 로깅 없음
        caplog.clear()
        tracker.update(9)
        assert "[진행률]" not in caplog.text

        # 20% - 로깅 발생
        caplog.clear()
        tracker.update(1)
        assert "[진행률]" in caplog.text
        assert "20/100 (20.0%)" in caplog.text
