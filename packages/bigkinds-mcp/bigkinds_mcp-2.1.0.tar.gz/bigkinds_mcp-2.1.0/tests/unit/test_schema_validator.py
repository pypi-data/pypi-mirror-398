"""Schema Validator 단위 테스트 (PRD AC13).

Pydantic strict mode 검증 및 에러 로깅 테스트.
"""

import pytest
from pydantic import ValidationError

from bigkinds_mcp.core.schema_validator import validate_api_response
from bigkinds_mcp.models.schemas import ArticleSummary, ArticleDetail, SearchResult


class TestSchemaValidator:
    """Schema Validator 테스트."""

    def test_valid_article_summary_passes(self):
        """유효한 ArticleSummary 데이터 통과."""
        data = {
            "news_id": "02100101.20251215174513002",
            "title": "테스트 기사",
            "summary": "이것은 테스트 요약입니다.",
            "publisher": "경향신문",
            "published_date": "2025-12-15",
            "category": "정치",
            "url": "https://example.com/article",
            "provider_code": "08100401",
            "category_code": "001000000",
        }

        result = validate_api_response(data, ArticleSummary, context="test")

        assert result.news_id == "02100101.20251215174513002"
        assert result.title == "테스트 기사"
        assert result.publisher == "경향신문"

    def test_missing_required_field_raises(self):
        """필수 필드 누락 시 ValidationError."""
        data = {
            "news_id": "02100101.20251215174513002",
            # title 누락 (필수 필드)
            "summary": "요약"
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_api_response(data, ArticleSummary, context="test")

        errors = exc_info.value.errors()
        assert any(err["loc"] == ("title",) for err in errors)

    def test_wrong_type_raises_strict_mode(self):
        """타입 불일치 시 strict mode로 에러 (PRD AC13)."""
        data = {
            "news_id": 123,  # str이어야 하는데 int
            "title": "테스트",
            "summary": "요약",
            "publisher": "경향신문",
            "published_date": "2025-12-15",
            "category": "정치",
            "url": "https://example.com",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_api_response(data, ArticleSummary, context="test")

        # strict mode에서는 int를 str로 자동 변환하지 않음
        errors = exc_info.value.errors()
        assert any("news_id" in str(err["loc"]) for err in errors)

    def test_extra_field_forbidden(self):
        """정의되지 않은 필드는 extra='forbid'로 거부 (PRD AC13)."""
        data = {
            "news_id": "123",
            "title": "테스트",
            "summary": "요약",
            "publisher": "경향신문",
            "published_date": "2025-12-15",
            "category": "정치",
            "url": "https://example.com",
            "undefined_field": "This should be rejected",  # 정의되지 않은 필드
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_api_response(data, ArticleSummary, context="test")

        # extra='forbid'로 추가 필드 감지
        errors = exc_info.value.errors()
        assert any("extra_forbidden" in err["type"] or "undefined_field" in str(err["loc"]) for err in errors)

    def test_valid_search_result_passes(self):
        """유효한 SearchResult 데이터 통과."""
        data = {
            "total_count": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5,
            "has_next": True,
            "has_prev": False,
            "articles": [
                {
                    "news_id": "123",
                    "title": "기사1",
                    "summary": "요약1",
                    "publisher": "경향신문",
                    "published_date": "2025-12-15",
                    "category": "정치",
                    "url": "https://example.com/1",
                }
            ],
            "keyword": "테스트",
            "date_range": "2025-12-01 to 2025-12-15",
            "sort_by": "both",
        }

        result = validate_api_response(data, SearchResult, context="search_news")

        assert result.total_count == 100
        assert result.page == 1
        assert len(result.articles) == 1

    def test_negative_page_rejected(self):
        """page < 1 거부 (ge=1 제약조건)."""
        data = {
            "total_count": 100,
            "page": 0,  # page는 1 이상이어야 함
            "page_size": 20,
            "total_pages": 5,
            "has_next": True,
            "has_prev": False,
            "articles": [],
            "keyword": "테스트",
            "date_range": "2025-12-01 to 2025-12-15",
            "sort_by": "both",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_api_response(data, SearchResult, context="test")

        errors = exc_info.value.errors()
        assert any("page" in str(err["loc"]) for err in errors)

    def test_validation_error_logged(self, caplog):
        """검증 실패 시 로깅 확인 (PRD AC13)."""
        import logging
        caplog.set_level(logging.ERROR)

        data = {
            "news_id": 123,  # 타입 오류
            "title": "테스트",
        }

        with pytest.raises(ValidationError):
            validate_api_response(data, ArticleSummary, context="test_context")

        # 로그에 컨텍스트와 에러 정보 포함 확인
        assert "Schema Validation Failed" in caplog.text
        assert "test_context" in caplog.text
        assert "ArticleSummary" in caplog.text

    def test_valid_article_detail_with_optional_fields(self):
        """선택 필드가 있는 ArticleDetail 검증."""
        data = {
            "news_id": "123",
            "title": "테스트 기사",
            "summary": None,  # 선택 필드
            "full_content": "전체 본문입니다.",
            "publisher": "경향신문",
            "author": None,  # 선택 필드
            "published_date": "2025-12-15",
            "category": "정치",
            "url": "https://example.com",
            "images": [],
            "keywords": ["AI", "기술"],
            "scrape_status": "success",
            "content_length": 100,
            "source": "bigkinds_api",
        }

        result = validate_api_response(data, ArticleDetail, context="get_article")

        assert result.news_id == "123"
        assert result.summary is None
        assert result.author is None
        assert result.content_length == 100
