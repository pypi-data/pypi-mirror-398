"""검색 관련 MCP Tools."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal

import httpx
from pydantic import ValidationError

from ..models.schemas import ArticleSummary, SearchParams, ArticleCountParams, SearchResult
from ..utils.errors import ErrorCode, error_response, handle_timeout_error
from ..validation.date_validator import DateValidator
from .utils import PROVIDER_NAME_TO_CODE, CATEGORY_CODES
from ..core.rate_limiter import RateLimiter
from ..formatters.search import format_search_news_basic

if TYPE_CHECKING:
    from ..core.async_client import AsyncBigKindsClient
    from ..core.cache import MCPCache

# 전역 인스턴스 (서버 시작 시 초기화)
_client: AsyncBigKindsClient | None = None
_cache: MCPCache | None = None

# 전역 rate limiter (1초당 3 요청, AC11)
_rate_limiter = RateLimiter(max_requests=3, period=1.0)


def init_search_tools(client: AsyncBigKindsClient, cache: MCPCache) -> None:
    """검색 도구 초기화."""
    global _client, _cache
    _client = client
    _cache = cache


async def search_news(
    keyword: str,
    start_date: str,
    end_date: str,
    page: int = 1,
    page_size: int = 20,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    sort_by: str = "both",
    response_format: Literal["basic", "full"] = "full",
) -> dict | str:
    """
    BigKinds에서 뉴스 기사를 검색합니다.

    Args:
        keyword: 검색 키워드 (AND/OR 연산자 지원)
        start_date: 검색 시작일 (YYYY-MM-DD)
        end_date: 검색 종료일 (YYYY-MM-DD)
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과 수 (기본값: 20, 최대: 100)
        providers: 언론사 필터 (예: ["경향신문", "한겨레"])
        categories: 카테고리 필터 (예: ["경제", "IT_과학"])
        sort_by: 정렬 방식
            - "both" (기본값): date + relevance 두 번 호출 후 병합
            - "date": 날짜순 (최신순)
            - "relevance": 관련도순
        response_format: 응답 형식
            - "basic": 마크다운 문자열, 핵심 정보만, 컨텍스트 절약
            - "full" (기본값): JSON dict, 전체 데이터, 상세 분석용

    Returns:
        - basic: 마크다운 문자열 (상위 10건 요약)
        - full: JSON dict (전체 검색 결과)

    ⚠️ CONTEXT-AWARE WORKFLOW GUIDANCE:
    결과 크기에 따라 적절한 분석 방법을 선택하세요:

    - 결과 < 20건: 컨텍스트 내에서 직접 분석 가능
    - 결과 20-100건: 샘플링 분석 권장 (smart_sample 사용)
    - 결과 > 100건: 로컬 파일 저장 + 코드 생성 분석 필수
      1. export_to_file()로 JSON/CSV 저장
      2. Python 분석 스크립트 생성
      3. 사용자에게 실행 방법 안내

    대용량 분석 예시 워크플로우:
    ```python
    # 1. 데이터 로컬 저장
    result = await export_to_file(keyword="...", output_path="data/articles.json")

    # 2. 분석 스크립트 생성 (Write tool 사용)
    # scripts/analyze.py 작성

    # 3. 실행 안내
    # "uv run python scripts/analyze.py"
    ```
    """
    if _client is None or _cache is None:
        raise RuntimeError("Search tools not initialized")

    # 날짜 검증 (AC12)
    validation_error = DateValidator.validate_date_range(start_date, end_date)
    if validation_error:
        return validation_error

    # 파라미터 검증 (PRD AC1)
    try:
        params = SearchParams(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            providers=providers,
            categories=categories,
            sort_by=sort_by,
        )
    except ValidationError as e:
        # 첫 번째 에러 메시지 추출
        first_error = e.errors()[0]
        field = first_error["loc"][0] if first_error["loc"] else "unknown"
        return error_response(
            code=ErrorCode.INVALID_PARAMS,
            details={"field": str(field), "errors": [err["msg"] for err in e.errors()]},
        )

    # 검증된 값 사용
    keyword = params.keyword
    start_date = params.start_date
    end_date = params.end_date
    page = params.page
    page_size = params.page_size
    sort_by = params.sort_by

    # 언론사 이름 → 코드 변환 (이름 또는 코드 모두 허용)
    providers = None
    if params.providers:
        providers = []
        for p in params.providers:
            if p in PROVIDER_NAME_TO_CODE:
                providers.append(PROVIDER_NAME_TO_CODE[p])
            else:
                # 이미 코드거나 알 수 없는 값은 그대로 사용
                providers.append(p)

    # 카테고리 이름 정규화 (CATEGORY_CODES 딕셔너리 사용)
    categories = None
    if params.categories:
        categories = []
        for c in params.categories:
            # CATEGORY_CODES 매핑 사용 (없으면 그대로)
            normalized = CATEGORY_CODES.get(c, c)
            categories.append(normalized)

    # 캐시 키 파라미터
    cache_params = {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "page": page,
        "page_size": page_size,
        "providers": tuple(providers) if providers else None,
        "categories": tuple(categories) if categories else None,
        "sort_by": sort_by,
    }

    # 캐시 확인
    cached = _cache.get_search(**cache_params)
    if cached:
        return cached

    from bigkinds.models import SearchRequest

    # sort_by에 따른 검색 실행 (PRD AC9 타임아웃 핸들링)
    try:
        if sort_by == "both":
            # 두 번 검색 후 병합
            articles, total_count = await _search_and_merge(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=page_size,
                providers=providers,
                categories=categories,
            )
        else:
            # 단일 정렬 검색
            start_no = (page - 1) * page_size + 1
            request = SearchRequest(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                start_no=start_no,
                result_number=page_size,
                provider_codes=providers or [],
                category_codes=categories or [],
                sort_method=sort_by,
            )

            response = await _client.search(request)

            if not response.success:
                raise ValueError(response.error_message or "Search failed")

            total_count = response.total_count
            articles = _convert_articles(response.articles)
    except httpx.TimeoutException:
        return handle_timeout_error("뉴스 검색")

    # 페이지네이션 계산
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    # 스키마 검증 (PRD AC13)
    try:
        search_result = SearchResult(
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            articles=articles[:page_size],  # page_size만큼만 반환
            keyword=keyword,
            date_range=f"{start_date} to {end_date}",
            sort_by=sort_by,
        )
        result = search_result.model_dump()
        result["success"] = True  # 성공 플래그 추가
    except ValidationError as e:
        # 스키마 검증 실패 (AC13)
        return error_response(
            code=ErrorCode.SCHEMA_VALIDATION_FAILED,
            details={
                "errors": [err["msg"] for err in e.errors()],
                "context": f"search_news(keyword={keyword})"
            }
        )

    # 대용량 결과에 대한 워크플로우 힌트 추가
    result["workflow_hint"] = _get_workflow_hint(total_count)

    # 캐시 저장
    _cache.set_search(result, **cache_params)

    # news_id -> URL 매핑 캐시 (get_article에서 news_id만으로 조회 가능하도록)
    _cache.set_urls_batch(result["articles"])

    # Response format 처리
    if response_format == "basic":
        return format_search_news_basic(result)
    else:
        return result


async def _search_and_merge(
    keyword: str,
    start_date: str,
    end_date: str,
    page: int,
    page_size: int,
    providers: list[str] | None,
    categories: list[str] | None,
) -> tuple[list[ArticleSummary], int]:
    """date와 relevance 두 번 검색 후 병합.

    Returns:
        (병합된 기사 목록, 전체 기사 수)
    """
    from bigkinds.models import SearchRequest

    start_no = (page - 1) * page_size + 1

    # 두 검색을 병렬로 실행
    date_request = SearchRequest(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        start_no=start_no,
        result_number=page_size,
        provider_codes=providers or [],
        category_codes=categories or [],
        sort_method="date",
    )

    relevance_request = SearchRequest(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        start_no=start_no,
        result_number=page_size,
        provider_codes=providers or [],
        category_codes=categories or [],
        sort_method="relevance",
    )

    # 병렬 실행
    date_response, relevance_response = await asyncio.gather(
        _client.search(date_request),
        _client.search(relevance_request),
    )

    # 결과 병합 (news_id로 중복 제거)
    seen_ids: set[str] = set()
    merged: list[ArticleSummary] = []

    # date 결과 먼저 추가
    for article in date_response.articles:
        if article.news_id and article.news_id not in seen_ids:
            seen_ids.add(article.news_id)
            merged.append(_convert_article(article))

    # relevance 결과 추가 (중복 제외)
    for article in relevance_response.articles:
        if article.news_id and article.news_id not in seen_ids:
            seen_ids.add(article.news_id)
            merged.append(_convert_article(article))

    # total_count는 API 응답에서 가져옴 (두 검색 중 큰 값)
    total_count = max(
        date_response.total_count or 0,
        relevance_response.total_count or 0,
    )

    return merged, total_count


def _convert_articles(articles: list) -> list[ArticleSummary]:
    """기사 목록을 ArticleSummary로 변환."""
    return [_convert_article(a) for a in articles]


def _convert_article(article) -> ArticleSummary:
    """단일 기사를 ArticleSummary로 변환."""
    return ArticleSummary(
        news_id=article.news_id or "",
        title=article.title,
        summary=article.content[:200] if article.content else None,
        publisher=article.publisher,
        published_date=article.news_date[:10] if article.news_date else None,
        category=article.category,
        url=article.url,
        provider_code=article.provider_code if hasattr(article, "provider_code") else None,
        category_code=article.category,  # category field contains numeric codes
    )


async def get_article_count(
    keyword: str,
    start_date: str,
    end_date: str,
    group_by: str = "total",
    providers: list[str] | None = None,
) -> dict:
    """
    키워드의 기사 수를 시간대별로 집계합니다.

    Args:
        keyword: 검색 키워드
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        group_by: 집계 단위
            - "total" (기본값): 전체 기간 총합만 반환
            - "day": 일별 집계 (최대 31일 권장)
            - "week": 주별 집계
            - "month": 월별 집계
        providers: 언론사 필터

    Returns:
        기사 수 집계 결과:
            - keyword: 검색 키워드
            - total_count: 전체 기사 수
            - date_range: 검색 기간
            - group_by: 집계 단위
            - counts: 기간별 기사 수 [{date, count}]

    Note:
        group_by가 "day"인 경우 API를 일별로 호출하므로
        기간이 길면 시간이 오래 걸릴 수 있습니다.
        최대 31일 이내 기간을 권장합니다.
    """
    if _client is None or _cache is None:
        raise RuntimeError("Search tools not initialized")

    # 날짜 검증 (AC12)
    validation_error = DateValidator.validate_date_range(start_date, end_date)
    if validation_error:
        return validation_error

    # 파라미터 검증 (PRD AC1)
    try:
        params = ArticleCountParams(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
            providers=providers,
        )
    except ValidationError as e:
        first_error = e.errors()[0]
        field = first_error["loc"][0] if first_error["loc"] else "unknown"
        return error_response(
            code=ErrorCode.INVALID_PARAMS,
            details={"field": str(field), "errors": [err["msg"] for err in e.errors()]},
        )

    # 검증된 값 사용
    keyword = params.keyword
    start_date = params.start_date
    end_date = params.end_date
    group_by = params.group_by
    providers = params.providers

    # 캐시 키 파라미터
    cache_params = {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by,
        "providers": tuple(providers) if providers else None,
    }

    # 캐시 확인
    cached = _cache.get_count(**cache_params)
    if cached:
        return cached

    # API 호출 (PRD AC9 타임아웃 핸들링)
    try:
        # 총 개수 조회
        total = await _client.get_total_count(keyword, start_date, end_date)

        counts = []

        if group_by == "day":
            counts = await _get_daily_counts(keyword, start_date, end_date)
        elif group_by == "week":
            counts = await _get_weekly_counts(keyword, start_date, end_date)
        elif group_by == "month":
            counts = await _get_monthly_counts(keyword, start_date, end_date)
        # "total"인 경우 counts는 빈 리스트
    except httpx.TimeoutException:
        return handle_timeout_error("기사 수 조회")

    result = {
        "success": True,
        "keyword": keyword,
        "total_count": total,
        "date_range": f"{start_date} to {end_date}",
        "group_by": group_by,
        "counts": counts,
    }

    # 캐시 저장
    _cache.set_count(result, **cache_params)

    return result


async def _get_daily_counts(keyword: str, start_date: str, end_date: str) -> list[dict]:
    """일별 기사 수 집계."""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # 최대 31일로 제한 (API 호출 수 제한)
    days = (end - start).days + 1
    if days > 31:
        # 31일 초과 시 샘플링
        step = days // 31 + 1
    else:
        step = 1

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=step)

    # 병렬로 일별 개수 조회
    tasks = [
        _client.get_total_count(keyword, date, date)
        for date in dates
    ]
    results = await asyncio.gather(*tasks)

    return [
        {"date": date, "count": count}
        for date, count in zip(dates, results)
    ]


async def _get_weekly_counts(keyword: str, start_date: str, end_date: str) -> list[dict]:
    """주별 기사 수 집계."""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    weeks = []
    current = start
    while current <= end:
        week_end = min(current + timedelta(days=6), end)
        weeks.append({
            "start": current.strftime("%Y-%m-%d"),
            "end": week_end.strftime("%Y-%m-%d"),
        })
        current = week_end + timedelta(days=1)

    # 병렬로 주별 개수 조회
    tasks = [
        _client.get_total_count(keyword, w["start"], w["end"])
        for w in weeks
    ]
    results = await asyncio.gather(*tasks)

    return [
        {
            "date": f"{w['start']} ~ {w['end']}",
            "week_start": w["start"],
            "week_end": w["end"],
            "count": count,
        }
        for w, count in zip(weeks, results)
    ]


async def _get_monthly_counts(keyword: str, start_date: str, end_date: str) -> list[dict]:
    """월별 기사 수 집계."""
    from datetime import datetime
    from calendar import monthrange

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    months = []
    current = start.replace(day=1)
    while current <= end:
        # 해당 월의 마지막 날
        last_day = monthrange(current.year, current.month)[1]
        month_end = current.replace(day=last_day)

        # 검색 범위 내로 조정
        actual_start = max(current, start.replace(day=1) if current == start.replace(day=1) else current)
        actual_start = start if current.year == start.year and current.month == start.month else current
        actual_end = min(month_end, end)

        months.append({
            "year_month": current.strftime("%Y-%m"),
            "start": actual_start.strftime("%Y-%m-%d"),
            "end": actual_end.strftime("%Y-%m-%d"),
        })

        # 다음 달로 이동
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    # 병렬로 월별 개수 조회
    tasks = [
        _client.get_total_count(keyword, m["start"], m["end"])
        for m in months
    ]
    results = await asyncio.gather(*tasks)

    return [
        {
            "date": m["year_month"],
            "month_start": m["start"],
            "month_end": m["end"],
            "count": count,
        }
        for m, count in zip(months, results)
    ]


def _get_workflow_hint(total_count: int) -> dict:
    """결과 크기에 따른 워크플로우 힌트 생성."""
    if total_count <= 20:
        return {
            "level": "small",
            "recommendation": "direct_analysis",
            "message": "결과가 적어 컨텍스트 내에서 직접 분석 가능합니다.",
        }
    elif total_count <= 100:
        return {
            "level": "medium",
            "recommendation": "sampling",
            "message": f"결과 {total_count}건. smart_sample 도구로 대표 샘플 추출 후 분석을 권장합니다.",
            "suggested_tool": "smart_sample",
        }
    else:
        return {
            "level": "large",
            "recommendation": "local_export",
            "message": f"결과 {total_count}건. 대용량 분석을 위해 로컬 파일 저장 + 코드 생성 워크플로우를 권장합니다.",
            "workflow": [
                "1. export_to_file()로 JSON/CSV 로컬 저장",
                "2. Python 분석 스크립트 생성 (Write tool)",
                "3. 'uv run python scripts/analyze.py' 실행 안내",
            ],
            "suggested_tool": "export_to_file",
            "reason": "컨텍스트 윈도우 제한으로 전체 데이터를 한 번에 처리할 수 없습니다.",
        }


async def search_news_parallel(
    queries: list[dict],
    max_concurrent: int = 5
) -> list[dict]:
    """
    여러 검색 쿼리를 병렬 실행 (AC11).

    Args:
        queries: 검색 파라미터 리스트
            [{"keyword": "AI", "start_date": "2025-12-01", "end_date": "2025-12-15"}, ...]
        max_concurrent: 최대 동시 실행 수 (기본 5)

    Returns:
        검색 결과 리스트

    Example:
        >>> results = await search_news_parallel([
        ...     {"keyword": "AI", "start_date": "2025-12-01", "end_date": "2025-12-15"},
        ...     {"keyword": "블록체인", "start_date": "2025-12-01", "end_date": "2025-12-15"},
        ... ])
    """
    async def _search_with_rate_limit(query: dict) -> dict:
        """Rate limiting 적용하여 검색."""
        await _rate_limiter.acquire()
        return await search_news(**query)

    # Semaphore로 동시 실행 수 제한
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _bounded_search(query: dict) -> dict:
        async with semaphore:
            return await _search_with_rate_limit(query)

    # 병렬 실행
    tasks = [_bounded_search(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 예외 처리
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append({
                "success": False,
                "error": "PARALLEL_SEARCH_FAILED",
                "message": f"쿼리 {i+1}번 실패: {str(result)}",
                "query": queries[i]
            })
        else:
            final_results.append(result)

    return final_results
