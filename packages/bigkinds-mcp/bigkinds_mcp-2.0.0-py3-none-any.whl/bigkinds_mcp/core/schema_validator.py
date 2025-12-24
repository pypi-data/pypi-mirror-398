"""API 응답 스키마 검증 모듈.

PRD AC13: API 스키마 strict 검증
"""

import logging
from typing import Any, Type, TypeVar

from pydantic import ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def validate_api_response(
    data: dict[str, Any],
    schema: Type[T],
    context: str = ""
) -> T:
    """
    API 응답을 Pydantic 스키마로 검증.

    PRD AC13 충족:
    - Pydantic strict mode를 통해 타입 불일치 감지
    - extra='forbid'로 정의되지 않은 필드 감지
    - 검증 실패 시 상세 로깅

    Args:
        data: 검증할 데이터
        schema: Pydantic 스키마 클래스 (StrictBaseModel 상속)
        context: 에러 로그용 컨텍스트 (예: "search(keyword=AI)")

    Returns:
        검증된 스키마 인스턴스

    Raises:
        ValidationError: 스키마 불일치 시 (타입 오류, 누락 필드, 추가 필드 등)

    Example:
        >>> from bigkinds_mcp.models.schemas import ArticleSummary
        >>> data = {"news_id": "123", "title": "Test", ...}
        >>> article = validate_api_response(data, ArticleSummary, context="get_article")
    """
    try:
        return schema.model_validate(data)
    except ValidationError as e:
        # 상세 로깅 (PRD AC13: 검증 실패 원인 추적)
        logger.error(
            f"[Schema Validation Failed] {context}\n"
            f"Schema: {schema.__name__}\n"
            f"Errors: {e.errors()}\n"
            f"Raw data (first 500 chars): {str(data)[:500]}"
        )
        raise
