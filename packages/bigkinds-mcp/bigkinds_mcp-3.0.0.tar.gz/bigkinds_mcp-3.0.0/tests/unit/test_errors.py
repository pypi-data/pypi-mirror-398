"""에러 처리 단위 테스트.

PRD Appendix C 에러 코드 기반 테스트.
"""

import pytest

from bigkinds_mcp.utils.errors import (
    ErrorCode,
    MCPError,
    empty_results_response,
    error_response,
    handle_api_error,
    handle_scrape_error,
    handle_timeout_error,
    handle_auth_error,
    handle_validation_error,
)


class TestErrorCode:
    """ErrorCode 열거형 테스트 (PRD Appendix C)."""

    def test_error_codes_exist(self):
        """PRD 정의 에러 코드 존재 확인."""
        # PRD 필수 에러 코드
        assert ErrorCode.AUTH_REQUIRED.value == "AUTH_REQUIRED"
        assert ErrorCode.AUTH_FAILED.value == "AUTH_FAILED"
        assert ErrorCode.INVALID_PARAMS.value == "INVALID_PARAMS"
        assert ErrorCode.API_ERROR.value == "API_ERROR"
        assert ErrorCode.RATE_LIMITED.value == "RATE_LIMITED"
        assert ErrorCode.TIMEOUT.value == "TIMEOUT"
        assert ErrorCode.SCRAPE_ERROR.value == "SCRAPE_ERROR"
        # 레거시 호환
        assert ErrorCode.NO_RESULTS.value == "NO_RESULTS"
        assert ErrorCode.NOT_FOUND.value == "NOT_FOUND"

    def test_all_codes_are_strings(self):
        """모든 코드가 문자열인지 확인."""
        for code in ErrorCode:
            assert isinstance(code.value, str)


class TestMCPError:
    """MCPError 클래스 테스트."""

    def test_creates_error(self):
        """에러 생성."""
        error = MCPError(
            code=ErrorCode.API_ERROR,
            message="테스트 에러",
        )
        assert error.code == ErrorCode.API_ERROR
        assert error.message == "테스트 에러"

    def test_to_dict(self):
        """dict 변환."""
        error = MCPError(
            code=ErrorCode.API_ERROR,
            message="테스트 에러",
            details={"status_code": 500},
            retry_after=60,
        )
        result = error.to_dict()

        assert result["success"] is False
        assert result["error"]["code"] == "API_ERROR"
        assert result["error"]["message"] == "테스트 에러"
        assert result["error"]["details"]["status_code"] == 500
        assert result["error"]["retry_after"] == 60

    def test_to_dict_without_optional_fields(self):
        """선택적 필드 없이 dict 변환."""
        error = MCPError(code=ErrorCode.NOT_FOUND, message="Not found")
        result = error.to_dict()

        assert "details" not in result["error"]
        assert "retry_after" not in result["error"]


class TestEmptyResultsResponse:
    """empty_results_response 함수 테스트."""

    def test_creates_empty_response(self):
        """빈 결과 응답 생성."""
        result = empty_results_response(
            keyword="테스트",
            date_range="2024-12-01 to 2024-12-15",
        )

        assert result["success"] is True
        assert result["total_count"] == 0
        assert result["articles"] == []
        assert "테스트" in result["message"]
        assert len(result["suggestions"]) > 0

    def test_includes_extra_info(self):
        """추가 정보 포함."""
        result = empty_results_response(
            keyword="테스트",
            date_range="2024-12-01 to 2024-12-15",
            extra_info={"custom_field": "value"},
        )
        assert result["custom_field"] == "value"


class TestErrorResponse:
    """error_response 함수 테스트."""

    def test_creates_error_response(self):
        """에러 응답 생성."""
        result = error_response(
            code=ErrorCode.INVALID_PARAMS,
            message="유효하지 않은 입력",
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_PARAMS"

    def test_includes_retry_after(self):
        """retry_after 포함."""
        result = error_response(
            code=ErrorCode.RATE_LIMITED,
            message="Rate limited",
            retry_after=60,
        )
        assert result["error"]["retry_after"] == 60


class TestHandleApiError:
    """handle_api_error 함수 테스트."""

    def test_handles_rate_limit(self):
        """429 에러 처리."""
        result = handle_api_error(429)
        assert result["error"]["code"] == "RATE_LIMITED"
        assert result["error"]["retry_after"] == 60

    def test_handles_server_error(self):
        """5xx 에러 처리 (PRD: API_ERROR)."""
        result = handle_api_error(500)
        assert result["error"]["code"] == "API_ERROR"

        result = handle_api_error(503)
        assert result["error"]["code"] == "API_ERROR"

    def test_handles_not_found(self):
        """404 에러 처리."""
        result = handle_api_error(404)
        assert result["error"]["code"] == "NOT_FOUND"

    def test_handles_other_errors(self):
        """기타 에러 처리."""
        result = handle_api_error(400, "Bad request")
        assert result["error"]["code"] == "API_ERROR"


class TestHandleScrapeError:
    """handle_scrape_error 함수 테스트 (PRD: SCRAPE_ERROR)."""

    def test_handles_timeout(self):
        """타임아웃 에러 처리."""
        result = handle_scrape_error("https://example.com", "Connection timeout")
        assert result["error"]["code"] == "SCRAPE_ERROR"

    def test_handles_blocked(self):
        """차단 에러 처리."""
        result = handle_scrape_error("https://example.com", "403 Forbidden")
        assert result["error"]["code"] == "SCRAPE_ERROR"

    def test_handles_generic_error(self):
        """일반 에러 처리."""
        result = handle_scrape_error("https://example.com", "Unknown error")
        assert result["error"]["code"] == "SCRAPE_ERROR"


class TestHandleTimeoutError:
    """handle_timeout_error 함수 테스트 (PRD AC9)."""

    def test_handles_timeout(self):
        """타임아웃 에러 처리."""
        result = handle_timeout_error("뉴스 검색")
        assert result["error"]["code"] == "TIMEOUT"
        assert "뉴스 검색" in result["error"]["message"]

    def test_default_operation(self):
        """기본 작업명 테스트."""
        result = handle_timeout_error()
        assert "API 요청" in result["error"]["message"]


class TestHandleAuthError:
    """handle_auth_error 함수 테스트 (PRD)."""

    def test_handles_missing_env(self):
        """환경변수 누락 에러."""
        result = handle_auth_error(missing_env=True)
        assert result["error"]["code"] == "AUTH_REQUIRED"

    def test_handles_invalid_credentials(self):
        """잘못된 자격증명 에러."""
        result = handle_auth_error(missing_env=False)
        assert result["error"]["code"] == "AUTH_FAILED"


class TestHandleValidationError:
    """handle_validation_error 함수 테스트 (PRD AC1)."""

    def test_handles_validation_error(self):
        """파라미터 검증 에러."""
        result = handle_validation_error("keyword", "키워드는 필수입니다")
        assert result["error"]["code"] == "INVALID_PARAMS"
        assert result["error"]["details"]["field"] == "keyword"
