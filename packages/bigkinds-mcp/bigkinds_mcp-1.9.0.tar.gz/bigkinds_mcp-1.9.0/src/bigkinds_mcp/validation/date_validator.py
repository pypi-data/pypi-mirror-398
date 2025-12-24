"""날짜 검증 로직 (AC12)."""

from datetime import datetime, date
from typing import Any

from ..utils.errors import ErrorCode, error_response

MIN_DATE = "1990-01-01"  # BigKinds 데이터 시작일


class DateValidator:
    """날짜 검증 로직."""

    @staticmethod
    def validate_date_range(
        start_date: str,
        end_date: str,
    ) -> dict[str, Any] | None:
        """
        날짜 범위 검증 (AC12).

        검증 규칙:
        1. 형식 검증 (YYYY-MM-DD)
        2. 미래 날짜 거부 (must be <= today in KST)
        3. 최소 날짜 검증 (>= 1990-01-01)
        4. 날짜 순서 검증 (end_date >= start_date)

        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)

        Returns:
            None: 검증 성공
            dict: 에러 응답 (ErrorCode 포함)
        """
        # 1. 형식 검증 (YYYY-MM-DD)
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return error_response(
                code=ErrorCode.INVALID_DATE_FORMAT,
                details={
                    "format": "YYYY-MM-DD",
                    "example": "2025-12-16",
                },
            )

        # 2. 미래 날짜 검증 (KST 기준)
        today = date.today()
        if start > today or end > today:
            return error_response(
                code=ErrorCode.FUTURE_DATE_NOT_ALLOWED,
                details={
                    "today": today.isoformat(),
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )

        # 3. 최소 날짜 검증 (1990-01-01)
        min_date = datetime.strptime(MIN_DATE, "%Y-%m-%d").date()
        if start < min_date or end < min_date:
            return error_response(
                code=ErrorCode.DATE_TOO_OLD,
                details={
                    "min_date": MIN_DATE,
                    "max_date": today.isoformat(),
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )

        # 4. 날짜 순서 검증
        if end < start:
            return error_response(
                code=ErrorCode.INVALID_DATE_ORDER,
                details={
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )

        return None  # 검증 성공
