"""한글 에러 메시지 단위 테스트 (AC15)."""

import pytest

from bigkinds_mcp.utils.errors import ErrorCode
from bigkinds_mcp.utils.errors_kr import get_error_message_kr, ERROR_MESSAGES_KR


class TestKoreanErrorMessages:
    """한글 에러 메시지 테스트 (AC15)."""

    def test_all_error_codes_have_korean_message(self):
        """모든 ErrorCode가 한글 메시지를 가지는지 확인."""
        # ErrorCode에 정의된 모든 코드 추출
        error_codes = [
            code.value for code in ErrorCode
        ]

        # 각 에러 코드가 ERROR_MESSAGES_KR에 정의되어 있는지 확인
        for code in error_codes:
            assert code in ERROR_MESSAGES_KR, f"ErrorCode.{code}에 대한 한글 메시지가 없습니다"

            msg_info = ERROR_MESSAGES_KR[code]
            assert "message" in msg_info, f"{code}에 message 필드가 없습니다"
            assert "solution" in msg_info, f"{code}에 solution 필드가 없습니다"

            # message와 solution이 비어있지 않은지 확인
            assert len(msg_info["message"]) > 0, f"{code}의 message가 비어있습니다"
            assert len(msg_info["solution"]) > 0, f"{code}의 solution이 비어있습니다"

    def test_error_message_contains_solution(self):
        """에러 메시지에 해결 방법 포함."""
        msg = get_error_message_kr("INVALID_DATE_FORMAT")

        assert "error" in msg
        assert "message" in msg["error"]
        assert "solution" in msg["error"]
        assert "YYYY-MM-DD" in msg["error"]["solution"]

    def test_error_message_with_docs(self):
        """문서 링크가 포함된 에러 메시지."""
        msg = get_error_message_kr("AUTH_REQUIRED")

        assert "error" in msg
        assert "docs" in msg["error"]
        assert msg["error"]["docs"].startswith("https://")

    def test_error_message_without_docs(self):
        """문서 링크가 없는 에러 메시지."""
        msg = get_error_message_kr("FUTURE_DATE_NOT_ALLOWED")

        assert "error" in msg
        assert "docs" not in msg["error"]  # docs 필드 없음

    def test_error_message_with_details(self):
        """추가 상세 정보가 포함된 에러 메시지."""
        details = {
            "today": "2025-12-17",
            "start_date": "2025-12-20"
        }
        msg = get_error_message_kr("FUTURE_DATE_NOT_ALLOWED", details)

        assert "error" in msg
        assert "details" in msg["error"]
        assert msg["error"]["details"]["today"] == "2025-12-17"

    def test_unknown_error_code_returns_fallback(self):
        """알 수 없는 에러 코드는 기본 메시지 반환."""
        msg = get_error_message_kr("UNKNOWN_ERROR_CODE")

        assert "error" in msg
        assert msg["error"]["message"] == "알 수 없는 오류가 발생했습니다"
        assert msg["error"]["solution"] == "개발자에게 문의하세요"
        assert "docs" in msg["error"]  # 기본 문서 링크 포함

    def test_all_messages_are_korean(self):
        """모든 메시지가 한글인지 확인."""
        for code, info in ERROR_MESSAGES_KR.items():
            # 메시지에 한글이 포함되어 있는지 확인
            has_korean = any('\uac00' <= char <= '\ud7a3' for char in info["message"])
            assert has_korean, f"{code}의 message에 한글이 없습니다: {info['message']}"

            # solution도 한글 확인
            has_korean_solution = any('\uac00' <= char <= '\ud7a3' for char in info["solution"])
            assert has_korean_solution, f"{code}의 solution에 한글이 없습니다: {info['solution']}"

    def test_response_structure(self):
        """응답 구조 검증."""
        msg = get_error_message_kr("INVALID_PARAMS")

        # 기본 구조
        assert msg["success"] is False
        assert "error" in msg
        assert "code" in msg["error"]
        assert "message" in msg["error"]
        assert "solution" in msg["error"]

        # 에러 코드가 올바른지 확인
        assert msg["error"]["code"] == "INVALID_PARAMS"

    def test_specific_error_messages(self):
        """특정 에러 메시지 내용 검증."""
        # 날짜 형식 오류
        msg = get_error_message_kr("INVALID_DATE_FORMAT")
        assert "날짜 형식" in msg["error"]["message"]
        assert "YYYY-MM-DD" in msg["error"]["solution"]

        # 미래 날짜 거부
        msg = get_error_message_kr("FUTURE_DATE_NOT_ALLOWED")
        assert "미래 날짜" in msg["error"]["message"]
        assert "오늘" in msg["error"]["solution"]

        # 인증 필요
        msg = get_error_message_kr("AUTH_REQUIRED")
        assert "로그인" in msg["error"]["message"]
        assert "환경변수" in msg["error"]["solution"]

        # Rate limit
        msg = get_error_message_kr("RATE_LIMITED")
        assert "요청이 너무 많습니다" in msg["error"]["message"]
        assert "3회" in msg["error"]["solution"]

    def test_date_validation_error_codes(self):
        """날짜 검증 관련 에러 코드 (AC12) 확인."""
        date_error_codes = [
            "INVALID_DATE_FORMAT",
            "FUTURE_DATE_NOT_ALLOWED",
            "DATE_TOO_OLD",
            "INVALID_DATE_ORDER",
        ]

        for code in date_error_codes:
            msg = get_error_message_kr(code)
            assert msg["error"]["code"] == code
            assert len(msg["error"]["message"]) > 0
            assert len(msg["error"]["solution"]) > 0

    def test_schema_validation_error_code(self):
        """스키마 검증 에러 코드 (AC13) 확인."""
        msg = get_error_message_kr("SCHEMA_VALIDATION_FAILED")

        assert msg["error"]["code"] == "SCHEMA_VALIDATION_FAILED"
        assert "스키마 검증" in msg["error"]["message"]
        assert "개발자" in msg["error"]["solution"]
        assert "docs" in msg["error"]  # 문서 링크 포함
