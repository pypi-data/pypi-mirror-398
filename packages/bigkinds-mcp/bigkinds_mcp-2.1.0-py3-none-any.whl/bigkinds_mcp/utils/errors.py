"""MCP 에러 처리 표준화 모듈.

PRD Appendix C 기반 에러 코드 정의.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """PRD 정의 에러 코드."""

    # 인증 관련 (PRD)
    AUTH_REQUIRED = "AUTH_REQUIRED"  # 로그인 필요 (환경변수 미설정)
    AUTH_FAILED = "AUTH_FAILED"  # 로그인 실패 (잘못된 자격증명)

    # 파라미터 관련 (PRD)
    INVALID_PARAMS = "INVALID_PARAMS"  # 파라미터 유효성 검증 실패

    # 날짜 검증 관련 (AC12)
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"  # 날짜 형식 오류
    FUTURE_DATE_NOT_ALLOWED = "FUTURE_DATE_NOT_ALLOWED"  # 미래 날짜 거부
    DATE_TOO_OLD = "DATE_TOO_OLD"  # 1990년 이전 날짜 거부
    INVALID_DATE_ORDER = "INVALID_DATE_ORDER"  # 시작일 > 종료일 오류

    # API 관련 (PRD)
    API_ERROR = "API_ERROR"  # BigKinds API 호출 실패
    RATE_LIMITED = "RATE_LIMITED"  # 요청 제한 초과
    TIMEOUT = "TIMEOUT"  # 요청 타임아웃

    # 스키마 검증 관련 (PRD AC13)
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"  # API 응답 스키마 검증 실패

    # 스크래핑 관련 (PRD)
    SCRAPE_ERROR = "SCRAPE_ERROR"  # 기사 스크래핑 실패

    # 레거시 호환 (기존 코드)
    NO_RESULTS = "NO_RESULTS"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class MCPError(Exception):
    """MCP 표준 에러."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        retry_after: int | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.retry_after = retry_after
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """에러를 dict로 변환."""
        result = {
            "success": False,
            "error": {
                "code": self.code.value,
                "message": self.message,
            },
        }
        if self.details:
            result["error"]["details"] = self.details
        if self.retry_after:
            result["error"]["retry_after"] = self.retry_after
        return result


class MCPResponse(BaseModel):
    """표준 MCP 응답."""

    success: bool = True
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    message: str | None = None
    suggestions: list[str] | None = None


def empty_results_response(
    keyword: str,
    date_range: str,
    extra_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """빈 검색 결과에 대한 친절한 응답 생성."""
    response = {
        "success": True,
        "total_count": 0,
        "articles": [],
        "keyword": keyword,
        "date_range": date_range,
        "message": f"'{keyword}' 검색 결과가 없습니다 ({date_range})",
        "suggestions": [
            "검색 기간을 늘려보세요",
            "다른 키워드를 시도해보세요",
            "키워드를 더 일반적인 용어로 바꿔보세요",
        ],
    }
    if extra_info:
        response.update(extra_info)
    return response


def error_response(
    code: ErrorCode,
    message: str = "",  # 더 이상 필수 아님 (AC15: 한글 메시지 자동 적용)
    details: dict[str, Any] | None = None,
    retry_after: int | None = None,
) -> dict[str, Any]:
    """
    에러 응답 생성 (AC15: 한글 자동 적용).

    Args:
        code: ErrorCode 열거형
        message: 사용자 정의 메시지 (선택사항, 미제공 시 한글 메시지 자동 적용)
        details: 추가 상세 정보
        retry_after: 재시도 대기 시간 (초)

    Returns:
        표준 에러 응답 딕셔너리
    """
    from .errors_kr import get_error_message_kr

    # message가 제공되지 않은 경우 한글 메시지 사용
    if not message:
        kr_response = get_error_message_kr(code.value, details)
        # retry_after 추가
        if retry_after:
            kr_response["error"]["retry_after"] = retry_after
        return kr_response

    # 레거시 호환: message가 제공된 경우 기존 방식 사용
    return MCPError(
        code=code,
        message=message,
        details=details,
        retry_after=retry_after,
    ).to_dict()


def handle_api_error(status_code: int, response_text: str = "") -> dict[str, Any]:
    """API 에러 처리."""
    if status_code == 429:
        return error_response(
            code=ErrorCode.RATE_LIMITED,
            message="API 요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요.",
            retry_after=60,
        )
    elif status_code >= 500:
        return error_response(
            code=ErrorCode.API_ERROR,
            message="BigKinds API가 일시적으로 사용 불가능합니다.",
            details={"status_code": status_code},
        )
    elif status_code == 404:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="요청한 리소스를 찾을 수 없습니다.",
        )
    else:
        return error_response(
            code=ErrorCode.API_ERROR,
            message=f"API 요청 실패 (HTTP {status_code})",
            details={"status_code": status_code, "response": response_text[:500]},
        )


def handle_scrape_error(url: str, error: str) -> dict[str, Any]:
    """스크래핑 에러 처리."""
    return error_response(
        code=ErrorCode.SCRAPE_ERROR,
        message="기사 스크래핑에 실패했습니다.",
        details={"url": url, "error": error},
    )


def handle_timeout_error(operation: str = "API 요청") -> dict[str, Any]:
    """타임아웃 에러 처리."""
    return error_response(
        code=ErrorCode.TIMEOUT,
        message=f"{operation} 시간이 초과되었습니다.",
    )


def handle_auth_error(missing_env: bool = True) -> dict[str, Any]:
    """인증 에러 처리."""
    if missing_env:
        return error_response(
            code=ErrorCode.AUTH_REQUIRED,
            message="Login required. Please set BIGKINDS_USER_ID and BIGKINDS_USER_PASSWORD environment variables.",
        )
    else:
        return error_response(
            code=ErrorCode.AUTH_FAILED,
            message="로그인에 실패했습니다. 자격증명을 확인해주세요.",
        )


def handle_validation_error(field: str, message: str) -> dict[str, Any]:
    """파라미터 검증 에러 처리."""
    return error_response(
        code=ErrorCode.INVALID_PARAMS,
        message=message,
        details={"field": field},
    )
