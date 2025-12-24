"""MCP 응답용 Pydantic 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================
# Strict Base Model (PRD AC13: API 스키마 strict 검증)
# ============================================================


class StrictBaseModel(BaseModel):
    """Strict 검증이 적용된 Base Model.

    PRD AC13 충족:
    - Pydantic strict mode: 타입 강제 변환 금지
    - extra='forbid': 정의되지 않은 필드 거부
    """
    model_config = ConfigDict(strict=True, extra='forbid')


# ============================================================
# 입력 파라미터 검증 스키마 (PRD AC1 충족)
# ============================================================


class SearchParams(BaseModel):
    """search_news 파라미터 검증."""

    keyword: str = Field(..., min_length=1, description="검색 키워드 (필수)")
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
    page: int = Field(default=1, ge=1, description="페이지 번호")
    page_size: int = Field(default=20, ge=1, le=100, description="페이지당 결과 수 (최대 100)")
    providers: list[str] | None = Field(default=None, description="언론사 필터")
    categories: list[str] | None = Field(default=None, description="카테고리 필터")
    sort_by: str = Field(default="both", description="정렬 방식")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """YYYY-MM-DD 형식 검증."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"날짜는 YYYY-MM-DD 형식이어야 합니다: {v}")
        return v

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """정렬 방식 검증."""
        valid = {"both", "date", "relevance"}
        if v not in valid:
            raise ValueError(f"sort_by는 {valid} 중 하나여야 합니다: {v}")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "SearchParams":
        """날짜 범위 검증 (start <= end)."""
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        if start > end:
            raise ValueError("start_date는 end_date보다 이전이어야 합니다")
        return self


class ArticleCountParams(BaseModel):
    """get_article_count 파라미터 검증."""

    keyword: str = Field(..., min_length=1, description="검색 키워드 (필수)")
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
    group_by: str = Field(default="total", description="집계 단위")
    providers: list[str] | None = Field(default=None, description="언론사 필터")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """YYYY-MM-DD 형식 검증."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"날짜는 YYYY-MM-DD 형식이어야 합니다: {v}")
        return v

    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, v: str) -> str:
        """집계 단위 검증."""
        valid = {"total", "day", "week", "month"}
        if v not in valid:
            raise ValueError(f"group_by는 {valid} 중 하나여야 합니다: {v}")
        return v


class TrendParams(BaseModel):
    """get_keyword_trends 파라미터 검증."""

    keyword: str = Field(..., min_length=1, description="검색 키워드 (필수)")
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
    interval: int = Field(default=1, ge=1, le=4, description="시간 단위 (1:일, 2:주, 3:월, 4:연)")
    providers: list[str] | None = Field(default=None, description="언론사 필터")
    categories: list[str] | None = Field(default=None, description="카테고리 필터")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"날짜는 YYYY-MM-DD 형식이어야 합니다: {v}")
        return v


class RelatedKeywordsParams(BaseModel):
    """get_related_keywords 파라미터 검증."""

    keyword: str = Field(..., min_length=1, description="검색 키워드 (필수)")
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
    max_news_count: int = Field(default=100, description="최대 뉴스 수")
    result_number: int = Field(default=50, ge=1, le=100, description="결과 수")
    providers: list[str] | None = Field(default=None, description="언론사 필터")
    categories: list[str] | None = Field(default=None, description="카테고리 필터")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"날짜는 YYYY-MM-DD 형식이어야 합니다: {v}")
        return v

    @field_validator("max_news_count")
    @classmethod
    def validate_max_news_count(cls, v: int) -> int:
        """max_news_count 유효값 검증."""
        valid = {50, 100, 200, 500, 1000}
        if v not in valid:
            # 가장 가까운 유효값으로 조정
            v = min(valid, key=lambda x: abs(x - v))
        return v


# ============================================================
# 응답 스키마 (StrictBaseModel 적용)
# ============================================================


class ArticleSummary(StrictBaseModel):
    """검색 결과용 기사 요약 (컨텍스트 최적화)."""

    news_id: str = Field(..., description="BigKinds 기사 ID")
    title: str = Field(..., description="기사 제목")
    summary: str | None = Field(None, max_length=300, description="요약 (200자 내외)")
    publisher: str | None = Field(None, description="언론사")
    published_date: str | None = Field(None, description="발행일 (YYYY-MM-DD)")
    category: str | None = Field(None, description="카테고리")
    url: str | None = Field(None, description="원본 기사 URL")
    # 필터 검증용 (2025-12-15 추가)
    provider_code: str | None = Field(None, description="언론사 코드 (8-digit)")
    category_code: str | None = Field(None, description="카테고리 코드 (9-digit)")


class ArticleDetail(StrictBaseModel):
    """기사 상세 정보 (전문 포함)."""

    news_id: str = Field(..., description="BigKinds 기사 ID")
    title: str = Field(..., description="기사 제목")
    summary: str | None = Field(None, description="요약")
    full_content: str | None = Field(None, description="기사 전문")
    publisher: str | None = Field(None, description="언론사")
    author: str | None = Field(None, description="기자/작성자")
    published_date: str | None = Field(None, description="발행일")
    category: str | None = Field(None, description="카테고리")
    url: str | None = Field(None, description="원본 기사 URL")
    images: list[dict] = Field(default_factory=list, description="이미지 목록")
    keywords: list[str] = Field(default_factory=list, description="키워드")
    scrape_status: str | None = Field(None, description="스크래핑 상태")
    content_length: int = Field(0, description="본문 길이 (자)")
    source: str | None = Field(None, description="데이터 출처 (bigkinds_api/url_scraping)")


class SearchResult(StrictBaseModel):
    """검색 결과 (페이지네이션 포함)."""

    # Pagination
    total_count: int = Field(..., description="전체 결과 수")
    page: int = Field(..., ge=1, description="현재 페이지")
    page_size: int = Field(..., ge=1, le=100, description="페이지당 결과 수")
    total_pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")

    # Results
    articles: list[ArticleSummary] = Field(
        default_factory=list, description="기사 목록"
    )

    # Query info
    keyword: str = Field(..., description="검색 키워드")
    date_range: str = Field(..., description="검색 기간")
    sort_by: str = Field("both", description="정렬 방식")

    def get_next_page_hint(self) -> str | None:
        """LLM에게 다음 페이지 힌트 제공."""
        if self.has_next:
            return f"More results available. Call search_news with page={self.page + 1}"
        return None


class ArticleCountResult(StrictBaseModel):
    """기사 수 집계 결과."""

    keyword: str = Field(..., description="검색 키워드")
    total_count: int = Field(..., description="전체 기사 수")
    date_range: str = Field(..., description="검색 기간")
    counts: list[dict] = Field(
        default_factory=list, description="시간대별 기사 수"
    )
    top_providers: list[dict] = Field(
        default_factory=list, description="상위 언론사"
    )


class ScrapedArticleResult(StrictBaseModel):
    """스크래핑 결과."""

    url: str = Field(..., description="요청 URL")
    final_url: str | None = Field(None, description="최종 URL (리다이렉트 후)")
    success: bool = Field(..., description="스크래핑 성공 여부")
    title: str | None = Field(None, description="기사 제목")
    content: str | None = Field(None, description="기사 본문")
    author: str | None = Field(None, description="기자")
    published_date: str | None = Field(None, description="발행일")
    publisher: str | None = Field(None, description="언론사")
    images: list[dict] = Field(default_factory=list, description="이미지 목록")
    keywords: list[str] = Field(default_factory=list, description="키워드")
    error: str | None = Field(None, description="에러 메시지")
