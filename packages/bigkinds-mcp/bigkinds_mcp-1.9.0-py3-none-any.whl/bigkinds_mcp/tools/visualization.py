"""분석 API 관련 MCP Tools.

로그인이 필요한 시각화/분석 도구들:
- get_keyword_trends: 키워드 트렌드 (시계열 기사 수)
- get_related_keywords: 연관어 분석 (TF-IDF)

NOTE: get_network_analysis (관계도 분석)은 제거됨
      사유: /news/getNetworkDataAnalysis.do API는 브라우저 전용
            httpx 직접 호출 시 302 → /err/error400.do 리다이렉트
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import httpx
from pydantic import ValidationError

from ..models.schemas import TrendParams, RelatedKeywordsParams
from ..utils.errors import ErrorCode, error_response, handle_timeout_error
from ..validation.date_validator import DateValidator
from ..formatters.visualization import format_keyword_trends_basic

if TYPE_CHECKING:
    from ..core.async_client import AsyncBigKindsClient
    from ..core.cache import MCPCache

# 전역 인스턴스 (서버 시작 시 초기화)
_client: AsyncBigKindsClient | None = None
_cache: MCPCache | None = None


def init_visualization_tools(client: AsyncBigKindsClient, cache: MCPCache) -> None:
    """분석 도구 초기화."""
    global _client, _cache
    _client = client
    _cache = cache


async def get_keyword_trends(
    keyword: str,
    start_date: str,
    end_date: str,
    interval: int = 1,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    response_format: Literal["basic", "full"] = "full",
) -> dict | str:
    """
    키워드 트렌드 데이터를 조회합니다 (로그인 필수).

    키워드별 기사 수 추이를 시간축 그래프로 분석합니다.

    Args:
        keyword: 검색 키워드 (콤마로 여러 키워드 구분 가능, 예: "AI,인공지능")
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        interval: 시간 단위 힌트 (기본: 1)
            - 1: 일간
            - 2: 주간
            - 3: 월간
            - 4: 연간
        providers: 언론사 필터 (예: ["경향신문", "한겨레"])
        categories: 카테고리 필터 (예: ["정치", "경제"])
        response_format: 응답 형식
            - "basic": 마크다운 문자열, ASCII 그래프 + 요약
            - "full" (기본값): JSON dict, 전체 시계열 데이터

    Returns:
        - basic: 마크다운 문자열 (ASCII 그래프)
        - full: JSON dict (전체 트렌드 데이터)
        키워드 트렌드 데이터:
            - trends: 키워드별 트렌드 [{keyword, data: [{date, count}]}]
            - total_keywords: 분석한 키워드 수
            - total_data_points: 전체 데이터 포인트 수
            - interval_name: 시간 단위 이름

    Note:
        이 API는 로그인이 필요합니다.
        BIGKINDS_USER_ID, BIGKINDS_USER_PASSWORD 환경변수를 설정해야 합니다.

        **중요: interval 파라미터 동작 특이사항**
        BigKinds API는 날짜 범위에 따라 자동으로 데이터 granularity를 조정합니다.
        interval 값은 힌트로만 사용되며, 실제 반환되는 데이터의 시간 단위는
        조회 기간에 따라 달라질 수 있습니다:
        - 짧은 기간 (2주 이하): 연도별 또는 월별 집계로 반환될 수 있음
        - 중간 기간 (1-3개월): 월별 집계로 반환될 수 있음
        - 긴 기간 (1년 이상): 일별 데이터로 반환될 수 있음

        현재 알려진 이슈:
        - API가 빈 결과를 반환하는 경우가 있습니다
        - 계정 권한이나 데이터 기간에 따라 결과가 다를 수 있습니다

    Example:
        - 단일 키워드: get_keyword_trends("AI", "2024-12-01", "2024-12-15")
        - 여러 키워드: get_keyword_trends("AI,인공지능", ...)
        - 월간 힌트: get_keyword_trends("AI", ..., interval=3)
    """
    if _client is None or _cache is None:
        raise RuntimeError("Visualization tools not initialized")

    # 날짜 검증 (AC12)
    validation_error = DateValidator.validate_date_range(start_date, end_date)
    if validation_error:
        return validation_error

    # 파라미터 검증 (PRD AC1)
    try:
        params = TrendParams(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            providers=providers,
            categories=categories,
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
    interval = params.interval
    providers = params.providers
    categories = params.categories

    # 캐시 키 파라미터
    cache_params = {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "interval": interval,
        "providers": tuple(providers) if providers else None,
        "categories": tuple(categories) if categories else None,
    }

    # 캐시 확인
    cache_key = f"trends_{hash(str(cache_params))}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    # 언론사/카테고리 코드 변환
    provider_code = ",".join(providers) if providers else ""
    category_code = ",".join(categories) if categories else ""

    # API 호출 (PRD AC9 타임아웃 핸들링)
    try:
        response = await _client.get_keyword_trends(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            provider_code=provider_code,
            category_code=category_code,
        )
    except httpx.TimeoutException:
        return handle_timeout_error("키워드 트렌드 조회")

    # 응답 처리
    if "error" in response:
        return {
            "success": False,
            "error": response["error"],
            "trends": [],
            "total_keywords": 0,
            "total_data_points": 0,
        }

    root = response.get("root", [])

    # 데이터 가공
    trends = []
    total_data_points = 0

    for item in root:
        keyword_name = item.get("keyword", "")
        data_points = item.get("data", [])

        # 날짜/카운트 형식으로 변환
        formatted_data = [
            {"date": point.get("d"), "count": point.get("c", 0)}
            for point in data_points
        ]

        trends.append({
            "keyword": keyword_name,
            "data": formatted_data,
            "total_count": sum(point.get("c", 0) for point in data_points),
        })

        total_data_points += len(data_points)

    # 시간 단위 이름
    interval_names = {1: "일간", 2: "주간", 3: "월간", 4: "연간"}

    result = {
        "success": True,
        "keyword": keyword,
        "date_range": f"{start_date} to {end_date}",
        "interval": interval,
        "interval_name": interval_names.get(interval, "일간"),
        "trends": trends,
        "total_keywords": len(trends),
        "total_data_points": total_data_points,
        "summary": {
            "keywords_analyzed": [t["keyword"] for t in trends],
            "total_articles_sum": sum(t["total_count"] for t in trends),
        },
    }

    # 캐시 저장 (10분)
    _cache.set(cache_key, result, ttl=600)

    # Response format 처리
    if response_format == "basic":
        return format_keyword_trends_basic(result)
    else:
        return result


async def get_related_keywords(
    keyword: str,
    start_date: str,
    end_date: str,
    max_news_count: int = 100,
    result_number: int = 50,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict:
    """
    연관어 분석 데이터를 조회합니다 (로그인 필수).

    검색 키워드와 연관된 키워드를 TF-IDF 기반으로 분석합니다.

    Args:
        keyword: 검색 키워드
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        max_news_count: 최대 뉴스 수 (기본: 100)
            - 50, 100, 200, 500, 1000 중 선택 권장
        result_number: 연관어 결과 수 (기본: 50)
        providers: 언론사 필터 (예: ["경향신문", "한겨레"])
        categories: 카테고리 필터 (예: ["정치", "경제"])

    Returns:
        연관어 분석 결과:
            - related_words: 연관 키워드 목록 [{name, weight, tf}]
            - news_count: 분석한 뉴스 수
            - top_words: 상위 10개 연관어

    Note:
        비회원의 경우 최대 3개월 기간 제한이 있을 수 있습니다.
        이 API는 로그인이 필요합니다.

    Example:
        - 기본 사용: get_related_keywords("AI", "2024-12-01", "2024-12-15")
        - 더 많은 뉴스 분석: get_related_keywords("AI", ..., max_news_count=500)
    """
    if _client is None or _cache is None:
        raise RuntimeError("Visualization tools not initialized")

    # 날짜 검증 (AC12)
    validation_error = DateValidator.validate_date_range(start_date, end_date)
    if validation_error:
        return validation_error

    # 파라미터 검증 (PRD AC1)
    try:
        params = RelatedKeywordsParams(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            max_news_count=max_news_count,
            result_number=result_number,
            providers=providers,
            categories=categories,
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
    max_news_count = params.max_news_count
    result_number = params.result_number
    providers = params.providers
    categories = params.categories

    # 캐시 키 파라미터
    cache_params = {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "max_news_count": max_news_count,
        "result_number": result_number,
        "providers": tuple(providers) if providers else None,
        "categories": tuple(categories) if categories else None,
    }

    # 캐시 확인
    cache_key = f"related_{hash(str(cache_params))}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    # 언론사/카테고리 코드 변환
    provider_code = ",".join(providers) if providers else ""
    category_code = ",".join(categories) if categories else ""

    # API 호출 (PRD AC9 타임아웃 핸들링)
    try:
        response = await _client.get_related_keywords(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            max_news_count=max_news_count,
            result_number=result_number,
            provider_code=provider_code,
            category_code=category_code,
        )
    except httpx.TimeoutException:
        return handle_timeout_error("연관어 분석 조회")

    # 응답 처리
    if "error" in response:
        return {
            "success": False,
            "error": response["error"],
            "related_words": [],
            "news_count": 0,
        }

    topics = response.get("topics", {}).get("data", [])
    news = response.get("news", {})
    document_count = news.get("documentCount", 0)

    # 가중치 기준 정렬
    sorted_words = sorted(topics, key=lambda x: x.get("weight", 0), reverse=True)

    result = {
        "success": True,
        "keyword": keyword,
        "date_range": f"{start_date} to {end_date}",
        "related_words": sorted_words,
        "news_count": document_count,
        "total_related_words": len(sorted_words),
        "top_words": [
            {"name": w.get("name"), "weight": w.get("weight"), "tf": w.get("tf")}
            for w in sorted_words[:10]
        ],
        "summary": {
            "analyzed_articles": document_count,
            "max_news_count": max_news_count,
            "found_keywords": len(sorted_words),
        },
    }

    # 캐시 저장 (10분)
    _cache.set(cache_key, result, ttl=600)

    return result
