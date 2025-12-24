"""DateValidator 단위 테스트 (AC12)."""

import pytest
from datetime import date, timedelta

from bigkinds_mcp.validation.date_validator import DateValidator
from bigkinds_mcp.utils.errors import ErrorCode


class TestDateValidator:
    """DateValidator 테스트."""

    def test_valid_date_range(self):
        """유효한 날짜 범위 검증."""
        result = DateValidator.validate_date_range("2025-12-01", "2025-12-15")
        assert result is None

    def test_same_start_end_date(self):
        """시작일과 종료일이 같은 경우."""
        result = DateValidator.validate_date_range("2025-12-15", "2025-12-15")
        assert result is None

    def test_future_date_rejected(self):
        """미래 날짜 거부."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = DateValidator.validate_date_range(tomorrow, tomorrow)

        assert result is not None
        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.FUTURE_DATE_NOT_ALLOWED.value
        assert "미래 날짜" in result["error"]["message"]
        assert "today" in result["error"]["details"]

    def test_future_end_date_rejected(self):
        """종료일만 미래인 경우 거부."""
        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = DateValidator.validate_date_range(today, tomorrow)

        assert result is not None
        assert result["error"]["code"] == ErrorCode.FUTURE_DATE_NOT_ALLOWED.value

    def test_date_before_1990_rejected(self):
        """1990년 이전 날짜 거부."""
        result = DateValidator.validate_date_range("1989-12-31", "1990-01-01")

        assert result is not None
        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.DATE_TOO_OLD.value
        assert "날짜 범위" in result["error"]["message"]

    def test_start_date_before_1990_rejected(self):
        """시작일만 1990년 이전인 경우 거부."""
        result = DateValidator.validate_date_range("1989-12-31", "2025-01-01")

        assert result is not None
        assert result["error"]["code"] == ErrorCode.DATE_TOO_OLD.value

    def test_end_before_start_rejected(self):
        """종료일 < 시작일 거부."""
        result = DateValidator.validate_date_range("2025-12-15", "2025-12-01")

        assert result is not None
        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.INVALID_DATE_ORDER.value
        assert "종료일" in result["error"]["message"]
        assert "시작일" in result["error"]["message"]

    def test_invalid_format_rejected(self):
        """잘못된 형식 거부."""
        result = DateValidator.validate_date_range("2025/12/01", "2025-12-15")

        assert result is not None
        assert result["success"] is False
        assert result["error"]["code"] == ErrorCode.INVALID_DATE_FORMAT.value
        assert "형식" in result["error"]["message"]
        assert "YYYY-MM-DD" in result["error"]["details"]["format"]

    def test_invalid_format_end_date(self):
        """종료일 형식 오류."""
        result = DateValidator.validate_date_range("2025-12-01", "12-15-2025")

        assert result is not None
        assert result["error"]["code"] == ErrorCode.INVALID_DATE_FORMAT.value

    def test_invalid_date_values(self):
        """존재하지 않는 날짜 거부."""
        result = DateValidator.validate_date_range("2025-02-30", "2025-03-01")

        assert result is not None
        assert result["error"]["code"] == ErrorCode.INVALID_DATE_FORMAT.value

    def test_boundary_1990_01_01(self):
        """경계값 테스트: 1990-01-01은 허용."""
        result = DateValidator.validate_date_range("1990-01-01", "1990-01-31")
        assert result is None

    def test_boundary_today(self):
        """경계값 테스트: 오늘 날짜는 허용."""
        today = date.today().isoformat()
        result = DateValidator.validate_date_range(today, today)
        assert result is None

    def test_long_date_range(self):
        """긴 날짜 범위 검증."""
        result = DateValidator.validate_date_range("1990-01-01", "2025-12-15")
        assert result is None

    def test_error_response_structure(self):
        """에러 응답 구조 검증."""
        result = DateValidator.validate_date_range("2025-12-15", "2025-12-01")

        # 표준 에러 응답 구조
        assert "success" in result
        assert "error" in result
        assert "code" in result["error"]
        assert "message" in result["error"]
        assert "details" in result["error"]

        # AC12 필수 필드
        assert result["success"] is False
        assert isinstance(result["error"]["details"], dict)

    def test_solution_provided_in_error(self):
        """모든 에러에 해결 방법 포함."""
        # 형식 오류
        result = DateValidator.validate_date_range("invalid", "2025-12-01")
        assert "solution" in result["error"]

        # 미래 날짜
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = DateValidator.validate_date_range(tomorrow, tomorrow)
        assert "solution" in result["error"]

        # 1990년 이전
        result = DateValidator.validate_date_range("1989-01-01", "1989-12-31")
        assert "solution" in result["error"]

        # 날짜 순서 오류
        result = DateValidator.validate_date_range("2025-12-15", "2025-12-01")
        assert "solution" in result["error"]
