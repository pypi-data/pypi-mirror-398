"""기사 관련 MCP Tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import httpx
from pydantic import ValidationError

from ..models.schemas import ArticleDetail, ScrapedArticleResult
from ..utils.errors import ErrorCode, error_response, handle_timeout_error
from ..utils.image_filter import filter_meaningful_images, get_main_image
from ..utils.markdown import article_to_context, html_to_markdown
from ..formatters.article import format_article_basic

if TYPE_CHECKING:
    from ..core.async_client import AsyncBigKindsClient
    from ..core.async_scraper import AsyncArticleScraper
    from ..core.cache import MCPCache

# 전역 인스턴스 (서버 시작 시 초기화)
_client: AsyncBigKindsClient | None = None
_scraper: AsyncArticleScraper | None = None
_cache: MCPCache | None = None


def init_article_tools(
    client: AsyncBigKindsClient,
    scraper: AsyncArticleScraper,
    cache: MCPCache,
) -> None:
    """기사 도구 초기화."""
    global _client, _scraper, _cache
    _client = client
    _scraper = scraper
    _cache = cache


async def get_article(
    news_id: str | None = None,
    url: str | None = None,
    include_full_content: bool = True,
    include_images: bool = False,
    include_markdown: bool = True,
    response_format: Literal["basic", "full"] = "full",
) -> dict | str:
    """
    기사의 상세 정보를 가져옵니다.

    Args:
        news_id: BigKinds 기사 ID (news_id 또는 url 중 하나 필수)
        url: 원본 기사 URL
        include_full_content: 원본 기사 전문 포함 여부 (기본값: True)
        include_images: 이미지 URL 목록 포함 여부 (기본값: False)
        include_markdown: LLM-friendly 마크다운 포함 여부 (기본값: True)
        response_format: 응답 형식
            - "basic": 마크다운 문자열, 제목/언론사/본문 발췌
            - "full" (기본값): JSON dict, 전체 메타데이터 + 본문

    Returns:
        - basic: 마크다운 문자열 (500자 발췌)
        - full: JSON dict (전체 기사 정보)
    """
    if _client is None or _scraper is None or _cache is None:
        raise RuntimeError("Article tools not initialized")

    if not news_id and not url:
        raise ValueError("news_id 또는 url 중 하나는 필수입니다")

    # 캐시 확인 (news_id가 있는 경우)
    if news_id:
        cached = _cache.get_article(news_id)
        if cached:
            return cached

    article_detail: ArticleDetail | None = None
    content_markdown: str | None = None

    # 1. news_id가 있으면 BigKinds detailView API 먼저 시도 (더 빠르고 안정적)
    if news_id and include_full_content:
        try:
            detail_result = await _client.get_article_detail(news_id)

            if detail_result.get("success"):
                detail = detail_result.get("detail", {})
                content = detail.get("CONTENT", "")

                # HTML 태그 정리 (BigKinds 본문에 <br/> 등 포함)
                if content:
                    # 간단한 HTML 태그 정리
                    content = content.replace("<br/>", "\n").replace("<br>", "\n")
                    content = content.replace("&nbsp;", " ")

                # 마크다운 생성
                if include_markdown and content:
                    content_markdown = content

                # 스키마 검증 (PRD AC13)
                try:
                    article_detail = ArticleDetail(
                        news_id=news_id,
                        title=detail.get("TITLE", ""),
                        summary=detail.get("CONTENT", "")[:200] if detail.get("CONTENT") else None,
                        full_content=content,
                        publisher=detail.get("PROVIDER", ""),
                        author=detail.get("BYLINE", ""),
                        published_date=detail.get("DATE", ""),
                        url=detail.get("PROVIDER_LINK_PAGE", "") or url,
                        images=[],  # BigKinds API는 이미지 미제공
                        keywords=detail.get("KEYWORD", "").split(",") if detail.get("KEYWORD") else [],
                        scrape_status="success",
                        content_length=len(content) if content else 0,
                        source="bigkinds_api",  # 출처 표시
                    )
                except ValidationError as e:
                    # 스키마 검증 실패 (AC13)
                    return error_response(
                        code=ErrorCode.SCHEMA_VALIDATION_FAILED,
                        details={
                            "errors": [err["msg"] for err in e.errors()],
                            "context": f"get_article(news_id={news_id})"
                        }
                    )
        except Exception:
            # BigKinds API 실패 시 URL 스크래핑으로 폴백
            pass

    # 2. BigKinds API 실패 시 URL 스크래핑 시도
    if article_detail is None:
        # URL이 없고 news_id만 있는 경우, 캐시에서 URL 조회
        if not url and news_id:
            cached_url = _cache.get_url(news_id)
            if cached_url:
                url = cached_url

        # URL이 있고 전문 포함 요청인 경우 스크래핑 (PRD AC9 타임아웃 핸들링)
        if url and include_full_content:
            try:
                scraped = await _scraper.scrape(url)
            except httpx.TimeoutException:
                return handle_timeout_error("기사 스크래핑")

            if scraped.success:
                # 이미지 필터링 (공격적 필터)
                filtered_images = []
                if include_images and scraped.images:
                    filtered_images = filter_meaningful_images(scraped.images, max_images=3)

                # LLM-friendly 마크다운 생성
                if include_markdown and scraped.content_html:
                    content_markdown = html_to_markdown(scraped.content_html)

                article_detail = ArticleDetail(
                    news_id=news_id or "",
                    title=scraped.title or "",
                    summary=scraped.description,
                    full_content=scraped.content,
                    publisher=scraped.publisher,
                    author=scraped.author,
                    published_date=scraped.published_date,
                    url=url,
                    images=filtered_images,
                    keywords=scraped.keywords,
                    scrape_status="success",
                    content_length=len(scraped.content) if scraped.content else 0,
                    source="url_scraping",  # 출처 표시
                )
            else:
                article_detail = ArticleDetail(
                    news_id=news_id or "",
                    title="",
                    url=url,
                    scrape_status=f"failed: {scraped.error}",
                )
        elif news_id:
            # URL 없이 news_id만 있는 경우 (캐시에도 URL 없음)
            article_detail = ArticleDetail(
                news_id=news_id,
                title="",
                scrape_status="url_not_found",
            )
            # 힌트 메시지 추가
            return {
                **article_detail.model_dump(),
                "error": "URL을 찾을 수 없습니다. search_news로 먼저 검색하거나, url 파라미터를 직접 제공해주세요.",
                "hint": "search_news 결과의 url 필드를 함께 전달하면 기사 전문을 가져올 수 있습니다.",
            }

    if article_detail is None:
        raise ValueError("Failed to get article")

    result = article_detail.model_dump()

    # 마크다운 추가
    if content_markdown:
        result["content_markdown"] = content_markdown

    # LLM context 형식 추가
    if include_markdown and article_detail.scrape_status == "success":
        result["llm_context"] = article_to_context(result, max_content_length=3000)

    # 캐시 저장 (news_id가 있고 성공한 경우)
    if news_id and article_detail.scrape_status == "success":
        _cache.set_article(news_id, result)

    # next_steps 생성 (Agentic Pipeline v2.1)
    from .timeline_utils import generate_next_steps
    result["next_steps"] = generate_next_steps(
        "get_article",
        result,
        context={"news_id": news_id, "url": url},
    )

    # Response format 처리
    if response_format == "basic":
        return format_article_basic(result)
    else:
        return result


async def scrape_article_url(
    url: str,
    extract_images: bool = False,
    include_markdown: bool = True,
) -> dict:
    """
    URL에서 기사 내용을 스크래핑합니다.

    Args:
        url: 스크래핑할 기사 URL
        extract_images: 이미지 추출 여부 (기본값: False)
        include_markdown: LLM-friendly 마크다운 포함 여부 (기본값: True)

    Returns:
        스크래핑된 기사 정보 (마크다운 포함)

    Note:
        이 도구는 BigKinds 검색 결과의 원본 URL에서 전문을 가져올 때 사용합니다.
        언론사 이용약관을 준수하여 사용해주세요.
    """
    if _scraper is None:
        raise RuntimeError("Article tools not initialized")

    # PRD AC9 타임아웃 핸들링
    try:
        scraped = await _scraper.scrape(url)
    except httpx.TimeoutException:
        return handle_timeout_error("기사 스크래핑")

    # 이미지 필터링
    filtered_images = []
    if extract_images and scraped.images:
        filtered_images = filter_meaningful_images(scraped.images, max_images=3)

    # 마크다운 변환
    content_markdown = None
    if include_markdown and scraped.content_html:
        content_markdown = html_to_markdown(scraped.content_html)

    result = ScrapedArticleResult(
        url=url,
        final_url=scraped.final_url,
        success=scraped.success,
        title=scraped.title,
        content=scraped.content,
        author=scraped.author,
        published_date=scraped.published_date,
        publisher=scraped.publisher,
        images=filtered_images,
        keywords=scraped.keywords,
        error=scraped.error,
    )

    result_dict = result.model_dump()

    # 마크다운 추가
    if content_markdown:
        result_dict["content_markdown"] = content_markdown

    # LLM context 형식 추가
    if include_markdown and scraped.success:
        result_dict["llm_context"] = article_to_context(
            {
                "title": scraped.title,
                "content": scraped.content,
                "publisher": scraped.publisher,
                "published_date": scraped.published_date,
                "author": scraped.author,
                "url": url,
                "keywords": scraped.keywords,
                "summary": scraped.description,
            },
            max_content_length=3000,
        )

    # next_steps 생성 (Agentic Pipeline v2.1)
    from .timeline_utils import generate_next_steps
    result_dict["next_steps"] = generate_next_steps(
        "scrape_article_url",
        result_dict,
        context={"url": url},
    )

    return result_dict


async def get_article_thumbnail(
    url: str,
) -> dict:
    """
    기사 URL에서 대표 이미지(썸네일)를 추출합니다.

    Args:
        url: 기사 URL

    Returns:
        대표 이미지 정보:
        - success: 추출 성공 여부
        - thumbnail_url: 대표 이미지 URL (og:image 우선, 없으면 본문 첫 이미지)
        - caption: 이미지 캡션 (있는 경우)
        - source: 이미지 출처 (og:image / article_body)
        - title: 기사 제목
        - publisher: 언론사

    Note:
        og:image 메타태그를 우선 사용하고, 없는 경우 본문에서
        광고/로고를 제외한 첫 번째 의미있는 이미지를 추출합니다.
    """
    if _scraper is None:
        raise RuntimeError("Article tools not initialized")

    try:
        scraped = await _scraper.scrape(url)
    except httpx.TimeoutException:
        return {
            "success": False,
            "url": url,
            "error": "요청 시간 초과 (15초)",
            "thumbnail_url": None,
        }

    if not scraped.success:
        return {
            "success": False,
            "url": url,
            "error": scraped.error,
            "thumbnail_url": None,
        }

    # 1. og:image (main_image) 우선
    if scraped.main_image:
        return {
            "success": True,
            "url": url,
            "thumbnail_url": scraped.main_image,
            "caption": None,
            "source": "og:image",
            "title": scraped.title,
            "publisher": scraped.publisher,
        }

    # 2. og:image 없으면 본문 이미지에서 추출
    if scraped.images:
        main_img = get_main_image(scraped.images)
        if main_img:
            return {
                "success": True,
                "url": url,
                "thumbnail_url": main_img.get("url"),
                "caption": main_img.get("caption"),
                "source": "article_body",
                "title": scraped.title,
                "publisher": scraped.publisher,
            }

    # 3. 이미지 없음
    return {
        "success": False,
        "url": url,
        "error": "대표 이미지를 찾을 수 없습니다",
        "thumbnail_url": None,
        "title": scraped.title,
        "publisher": scraped.publisher,
    }
