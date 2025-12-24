"""한국어 에러 메시지 및 해결 방법 (AC15).

모든 ErrorCode에 대해 한글 메시지, 해결 방법, 문서 링크를 제공합니다.
"""

from typing import Any


# 모든 에러 코드에 대한 한글 메시지 매핑
ERROR_MESSAGES_KR: dict[str, dict[str, str]] = {
    # 인증 관련
    "AUTH_REQUIRED": {
        "message": "로그인이 필요합니다",
        "solution": "BIGKINDS_USER_ID와 BIGKINDS_USER_PASSWORD 환경변수를 설정하세요",
        "docs": "https://github.com/seolcoding/bigkinds-mcp#환경변수-설정",
    },
    "AUTH_FAILED": {
        "message": "로그인에 실패했습니다",
        "solution": "사용자 ID와 비밀번호를 확인하세요",
        "docs": "https://github.com/seolcoding/bigkinds-mcp#환경변수-설정",
    },
    # 파라미터 검증 관련
    "INVALID_PARAMS": {
        "message": "유효하지 않은 파라미터입니다",
        "solution": "입력값을 확인하고 올바른 형식으로 다시 시도하세요",
    },
    # 날짜 검증 관련 (AC12)
    "INVALID_DATE_FORMAT": {
        "message": "날짜 형식이 올바르지 않습니다",
        "solution": "YYYY-MM-DD 형식으로 입력하세요 (예: 2025-12-16)",
        "docs": "https://github.com/seolcoding/bigkinds-mcp#날짜-형식",
    },
    "FUTURE_DATE_NOT_ALLOWED": {
        "message": "미래 날짜는 검색할 수 없습니다",
        "solution": "오늘 날짜 이하로 검색하세요",
    },
    "DATE_TOO_OLD": {
        "message": "검색 가능한 날짜 범위를 벗어났습니다",
        "solution": "1990-01-01부터 오늘까지만 검색 가능합니다",
    },
    "INVALID_DATE_ORDER": {
        "message": "종료일이 시작일보다 빠릅니다",
        "solution": "시작일 ≤ 종료일로 입력하세요",
    },
    # API 관련
    "API_ERROR": {
        "message": "BigKinds API 호출에 실패했습니다",
        "solution": "네트워크 연결을 확인하거나 잠시 후 재시도하세요",
    },
    "RATE_LIMITED": {
        "message": "요청이 너무 많습니다",
        "solution": "잠시 후 다시 시도하세요 (초당 최대 3회 제한)",
    },
    "TIMEOUT": {
        "message": "요청 시간이 초과되었습니다",
        "solution": "네트워크 연결을 확인하거나 잠시 후 재시도하세요",
    },
    # 스키마 검증 관련 (AC13)
    "SCHEMA_VALIDATION_FAILED": {
        "message": "API 응답 스키마 검증에 실패했습니다",
        "solution": "API 응답 형식이 예상과 다릅니다. 개발자에게 문의하세요",
        "docs": "https://github.com/seolcoding/bigkinds-mcp/issues",
    },
    # 스크래핑 관련
    "SCRAPE_ERROR": {
        "message": "기사 스크래핑에 실패했습니다",
        "solution": "URL이 유효한지 확인하거나 잠시 후 재시도하세요",
    },
    # 레거시 호환
    "NO_RESULTS": {
        "message": "검색 결과가 없습니다",
        "solution": "검색 기간을 늘리거나 다른 키워드를 시도해보세요",
    },
    "NOT_FOUND": {
        "message": "요청한 리소스를 찾을 수 없습니다",
        "solution": "요청 정보를 확인하고 다시 시도하세요",
    },
    "INTERNAL_ERROR": {
        "message": "내부 서버 오류가 발생했습니다",
        "solution": "잠시 후 다시 시도하거나 개발자에게 문의하세요",
        "docs": "https://github.com/seolcoding/bigkinds-mcp/issues",
    },
}


def get_error_message_kr(
    error_code: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    한글 에러 메시지 반환 (AC15).

    Args:
        error_code: ErrorCode 문자열
        details: 추가 상세 정보

    Returns:
        에러 응답 딕셔너리 (error, message, solution, docs(선택), details(선택) 포함)
    """
    error_info = ERROR_MESSAGES_KR.get(
        error_code,
        {
            "message": "알 수 없는 오류가 발생했습니다",
            "solution": "개발자에게 문의하세요",
            "docs": "https://github.com/seolcoding/bigkinds-mcp/issues",
        },
    )

    result = {
        "success": False,
        "error": {
            "code": error_code,
            "message": error_info["message"],
            "solution": error_info["solution"],
        },
    }

    # 문서 링크 추가 (선택사항)
    if "docs" in error_info:
        result["error"]["docs"] = error_info["docs"]

    # 추가 상세 정보 (선택사항)
    if details:
        result["error"]["details"] = details

    return result
