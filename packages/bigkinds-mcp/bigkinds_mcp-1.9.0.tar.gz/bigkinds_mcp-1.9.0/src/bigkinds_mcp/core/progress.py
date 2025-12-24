"""대용량 작업 진행률 추적 모듈.

PRD AC14: 대용량 작업 시 진행률 피드백 제공
"""

import logging
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ProgressTracker:
    """대용량 작업 진행률 추적기.

    5000건 이상의 작업에 대해 10% 단위로 진행률과 예상 완료 시간을 로깅합니다.

    Example:
        >>> tracker = ProgressTracker(total=10000, description="기사 내보내기")
        >>> for i in range(100):
        ...     tracker.update(100)  # 100건씩 업데이트
        [진행률] 기사 내보내기: 1000/10000 (10.0%) - 예상 완료: 27초
        [진행률] 기사 내보내기: 2000/10000 (20.0%) - 예상 완료: 24초
        ...
    """

    def __init__(
        self,
        total: int,
        description: str = "Processing",
        threshold: int = 5000,
        interval: int = 10,
        callback: Optional[Callable[[int, int], None]] = None,
    ):
        """ProgressTracker 초기화.

        Args:
            total: 전체 작업 항목 수
            description: 작업 설명 (로그에 표시됨)
            threshold: 진행률 표시 최소 건수 (기본: 5000)
            interval: 진행률 업데이트 주기 (%, 기본: 10)
            callback: 진행률 업데이트 시 호출할 콜백 함수 (current, total)
        """
        self.total = total
        self.description = description
        self.threshold = threshold
        self.interval = interval
        self.callback = callback
        self.current = 0
        self.start_time = datetime.now()
        self.last_reported = 0

        # threshold 미만이면 진행률 표시 비활성화
        self.enabled = total >= threshold

    def update(self, amount: int = 1) -> None:
        """진행률 업데이트.

        Args:
            amount: 증가량 (기본: 1)
        """
        if not self.enabled:
            return

        self.current += amount
        progress_pct = (self.current / self.total) * 100

        # interval 단위로만 로깅 (예: 10%, 20%, 30%, ...)
        if progress_pct >= self.last_reported + self.interval:
            self._log_progress(progress_pct)
            self.last_reported = int(progress_pct / self.interval) * self.interval

            if self.callback:
                self.callback(self.current, self.total)

    def _log_progress(self, progress_pct: float) -> None:
        """진행률 로깅.

        Args:
            progress_pct: 진행률 (퍼센트)
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # 예상 완료 시간 계산 (ETA)
        if progress_pct > 0:
            eta = (elapsed / progress_pct) * (100 - progress_pct)
        else:
            eta = 0

        logger.info(
            f"[진행률] {self.description}: "
            f"{self.current}/{self.total} ({progress_pct:.1f}%) - "
            f"예상 완료: {eta:.0f}초"
        )

    def complete(self) -> None:
        """작업 완료 로깅."""
        if not self.enabled:
            return

        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(
            f"[완료] {self.description}: "
            f"{self.current}/{self.total} - "
            f"소요 시간: {elapsed:.1f}초"
        )
