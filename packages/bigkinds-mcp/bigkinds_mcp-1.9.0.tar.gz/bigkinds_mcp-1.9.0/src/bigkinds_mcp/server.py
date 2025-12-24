"""BigKinds MCP Server - Korean news search and article scraping."""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp.server.fastmcp import FastMCP

from .core.async_client import AsyncBigKindsClient
from .core.async_scraper import AsyncArticleScraper
from .core.cache import MCPCache
from .prompts import analysis as prompt_analysis
from .resources import news as news_resources
from .tools import analysis, article, search, utils, visualization

# 전역 리소스
_client: AsyncBigKindsClient | None = None
_scraper: AsyncArticleScraper | None = None
_cache: MCPCache | None = None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """서버 생명주기 관리."""
    global _client, _scraper, _cache

    # Startup
    _client = AsyncBigKindsClient()
    _scraper = AsyncArticleScraper()
    _cache = MCPCache()

    # Tools 초기화
    search.init_search_tools(_client, _cache)
    article.init_article_tools(_client, _scraper, _cache)
    visualization.init_visualization_tools(_client, _cache)
    analysis.init_analysis_tools(_client, _cache)

    # Resources 초기화
    news_resources.init_resources(_client, _cache)

    yield {"client": _client, "scraper": _scraper, "cache": _cache}

    # Shutdown
    if _client:
        _client.close()
    if _scraper:
        _scraper.close()


# FastMCP 서버 생성
mcp = FastMCP(
    name="bigkinds-news",
    lifespan=lifespan,
)


# ============================================================
# MCP Tools 등록
# ============================================================


@mcp.tool()
async def search_news(
    keyword: str,
    start_date: str,
    end_date: str,
    page: int = 1,
    page_size: int = 20,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    sort_by: str = "both",
) -> dict:
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

    Returns:
        검색 결과 (페이지네이션 메타데이터 + 기사 요약 목록)
    """
    return await search.search_news(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        providers=providers,
        categories=categories,
        sort_by=sort_by,
    )


@mcp.tool()
async def search_news_batch(
    queries: list[dict],
) -> dict:
    """
    여러 뉴스 검색을 동시에 실행합니다 (AC11: 병렬 API 호출).

    Rate limiting(1초당 3개)과 동시 실행 제한(최대 5개)을 자동으로 적용합니다.

    Args:
        queries: 검색 조건 목록 (최대 5개)
            각 항목은 search_news의 파라미터를 포함해야 합니다:
            [
                {"keyword": "AI", "start_date": "2025-12-01", "end_date": "2025-12-15"},
                {"keyword": "블록체인", "start_date": "2025-12-01", "end_date": "2025-12-15"}
            ]

    Returns:
        병렬 검색 결과:
        - total_queries: 총 쿼리 수
        - successful: 성공한 검색 수
        - failed: 실패한 검색 수
        - results: 각 검색 결과 목록

    Example:
        >>> result = await search_news_batch([
        ...     {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ...     {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        ...     {"keyword": "메타버스", "start_date": "2025-12-10", "end_date": "2025-12-15"}
        ... ])
        >>> print(f"3개 검색 완료: {result['successful']}개 성공")

    Performance:
        - 순차 실행 대비 약 55% 시간 단축
        - 3개 검색: ~9초 → ~4초
    """
    if len(queries) > 5:
        from .utils.errors import ErrorCode, error_response
        return error_response(
            code=ErrorCode.INVALID_PARAMS,
            details={"max_queries": 5, "provided": len(queries)},
        )

    results = await search.search_news_parallel(queries)

    return {
        "success": True,
        "total_queries": len(queries),
        "results": results,
        "successful": sum(1 for r in results if r.get("success", False)),
        "failed": sum(1 for r in results if not r.get("success", False)),
    }


@mcp.tool()
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
        기사 수 집계 결과 (total_count, counts 배열)

    Example:
        - 총합만: get_article_count(keyword="AI", start_date="2024-12-01", end_date="2024-12-15")
        - 일별: get_article_count(..., group_by="day")
        - 월별: get_article_count(..., group_by="month")
    """
    return await search.get_article_count(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
        providers=providers,
    )


@mcp.tool()
async def get_article(
    news_id: str | None = None,
    url: str | None = None,
    include_full_content: bool = True,
    include_images: bool = False,
) -> dict:
    """
    기사의 상세 정보를 가져옵니다.

    Args:
        news_id: BigKinds 기사 ID (news_id 또는 url 중 하나 필수)
        url: 원본 기사 URL
        include_full_content: 원본 기사 전문 포함 여부 (기본값: True)
        include_images: 이미지 URL 목록 포함 여부 (기본값: False)

    Returns:
        기사 상세 정보 (제목, 전문, 발행일, 기자, 이미지 등)
    """
    return await article.get_article(
        news_id=news_id,
        url=url,
        include_full_content=include_full_content,
        include_images=include_images,
    )


@mcp.tool()
async def scrape_article_url(
    url: str,
    extract_images: bool = False,
) -> dict:
    """
    URL에서 기사 내용을 스크래핑합니다.

    Args:
        url: 스크래핑할 기사 URL
        extract_images: 이미지 추출 여부 (기본값: False)

    Returns:
        스크래핑된 기사 정보

    Note:
        이 도구는 BigKinds 검색 결과의 원본 URL에서 전문을 가져올 때 사용합니다.
        언론사 이용약관을 준수하여 사용해주세요.
    """
    return await article.scrape_article_url(
        url=url,
        extract_images=extract_images,
    )


@mcp.tool()
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
        - thumbnail_url: 대표 이미지 URL
        - caption: 이미지 캡션 (있는 경우)
        - source: 이미지 출처 (og:image / article_body)
        - title: 기사 제목
        - publisher: 언론사

    Note:
        og:image 메타태그를 우선 사용하고, 없으면 본문에서
        광고/로고를 제외한 첫 번째 의미있는 이미지를 추출합니다.
    """
    return await article.get_article_thumbnail(url=url)


@mcp.tool()
async def get_today_issues(
    date: str | None = None,
    category: str = "전체",
) -> dict:
    """
    오늘/특정 날짜의 인기 이슈(Top 뉴스)를 조회합니다.

    키워드 없이 당일 핫이슈를 확인할 수 있습니다.

    Args:
        date: 조회할 날짜 (YYYY-MM-DD). 생략하면 오늘
        category: 카테고리 필터
            - "전체" (기본값): 모든 이슈
            - "AI": AI가 선정한 이슈

    Returns:
        인기 이슈 목록 (제목, 기사 수, 날짜별)

    Example:
        - 오늘 인기 이슈: get_today_issues()
        - 특정 날짜: get_today_issues(date="2025-12-10")
        - AI 선정 이슈: get_today_issues(category="AI")
    """
    if _client is None:
        raise RuntimeError("Client not initialized")

    # 유효한 카테고리만 허용
    valid_categories = {"전체", "AI"}
    if category not in valid_categories:
        raise ValueError(f"지원하지 않는 카테고리입니다: '{category}'. 사용 가능: {', '.join(valid_categories)}")

    # API는 category=전체만 지원, 클라이언트 측에서 필터링
    raw_data = await _client.get_today_issues(date=date)

    # 응답 데이터 가공 및 카테고리 필터링
    issues_by_date = {}
    for item in raw_data.get("trendList", []):
        # 카테고리 필터링: "전체"가 아니면 해당 카테고리만 포함
        item_category = item.get("topic_category", "전체")
        if category != "전체" and item_category != category:
            continue

        date_key = item.get("date", "")
        topic_list = item.get("topic_list", [])

        if topic_list:
            issues_by_date[date_key] = {
                "date": date_key,
                "date_display": f"{item.get('topic_year', '')} {item.get('topic_day', '')}",
                "category": item_category,
                "issues": [
                    {
                        "rank": idx + 1,
                        "title": t.get("topic_text", ""),
                        "article_count": int(t.get("topic_count", 0)),
                        "topic_id": t.get("topic_sn", ""),
                    }
                    for idx, t in enumerate(topic_list)
                ],
            }

    return {
        "query_date": raw_data.get("currentDate"),
        "category": category,
        "results": list(issues_by_date.values()),
        "total_dates": len(issues_by_date),
    }


@mcp.tool()
def get_current_korean_time() -> dict:
    """
    현재 한국 시간(KST)을 조회합니다.

    날짜/시간 기반 검색 시 참조용으로 사용합니다.
    BigKinds API는 한국 시간대(KST, UTC+9) 기준으로 동작합니다.

    Returns:
        현재 한국 시간 정보 (datetime, date, time, weekday 등)

    Example:
        검색 기간 설정 시 오늘 날짜 확인:
        - 오늘 날짜: get_current_korean_time() → date 필드 사용
        - 최근 1주일 검색: 오늘 date에서 7일 전까지
    """
    return utils.get_current_korean_time()


@mcp.tool()
def find_category(
    query: str,
    category_type: str = "all",
) -> dict:
    """
    언론사 또는 카테고리 코드를 검색합니다.

    BigKinds 검색 시 providers나 categories 파라미터에 사용할 값을 찾습니다.

    Args:
        query: 검색어 (예: "경향", "한겨레", "경제", "IT")
        category_type: 검색 대상
            - "all" (기본값): 언론사와 카테고리 모두 검색
            - "provider": 언론사만 검색
            - "category": 카테고리만 검색

    Returns:
        검색 결과 (매칭된 언론사/카테고리 목록)

    Example:
        - find_category("한겨레") → 한겨레 언론사 정보
        - find_category("경제") → 경제 관련 언론사 + 경제 카테고리
    """
    return utils.find_category(query=query, category_type=category_type)


@mcp.tool()
def list_providers() -> dict:
    """
    사용 가능한 모든 언론사 코드 목록을 반환합니다.

    search_news의 providers 파라미터에 사용할 수 있는 언론사 목록입니다.

    Returns:
        언론사 목록 (그룹별 분류 포함)

    Example:
        >>> providers = list_providers()
        >>> search_news(keyword="AI", providers=["경향신문", "한겨레"], ...)
    """
    return utils.list_providers()


@mcp.tool()
def list_categories() -> dict:
    """
    사용 가능한 모든 카테고리 코드 목록을 반환합니다.

    search_news의 categories 파라미터에 사용할 수 있는 카테고리 목록입니다.

    Returns:
        카테고리 목록

    Example:
        >>> categories = list_categories()
        >>> search_news(keyword="AI", categories=["경제", "IT_과학"], ...)
    """
    return utils.list_categories()


@mcp.tool()
async def get_keyword_trends(
    keyword: str,
    start_date: str,
    end_date: str,
    interval: int = 1,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict:
    """
    키워드 트렌드 데이터를 조회합니다 (로그인 필수).

    키워드별 기사 수 추이를 시간축 그래프로 분석합니다.

    Args:
        keyword: 검색 키워드 (콤마로 여러 키워드 구분 가능, 예: "AI,인공지능")
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        interval: 시간 단위 (기본: 1)
            - 1: 일간
            - 2: 주간
            - 3: 월간
            - 4: 연간
        providers: 언론사 필터 (예: ["경향신문", "한겨레"])
        categories: 카테고리 필터 (예: ["정치", "경제"])

    Returns:
        키워드 트렌드 데이터 (trends, total_data_points, summary 등)

    Note:
        이 API는 로그인이 필요합니다.
        BIGKINDS_USER_ID, BIGKINDS_USER_PASSWORD 환경변수를 설정해야 합니다.

        현재 알려진 이슈:
        - API가 빈 결과를 반환하는 경우가 있습니다
        - 계정 권한이나 데이터 기간에 따라 결과가 다를 수 있습니다

    Example:
        - 단일 키워드: get_keyword_trends("AI", "2024-12-01", "2024-12-15")
        - 여러 키워드: get_keyword_trends("AI,인공지능", ...)
        - 주간 단위: get_keyword_trends("AI", ..., interval=2)
    """
    return await visualization.get_keyword_trends(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        providers=providers,
        categories=categories,
    )


@mcp.tool()
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
        연관어 분석 결과 (related_words, top_words, summary 등)

    Note:
        비회원의 경우 최대 3개월 기간 제한이 있을 수 있습니다.
        이 API는 로그인이 필요합니다.

    Example:
        - 기본 사용: get_related_keywords("AI", "2024-12-01", "2024-12-15")
        - 더 많은 뉴스 분석: get_related_keywords("AI", ..., max_news_count=500)
    """
    return await visualization.get_related_keywords(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        max_news_count=max_news_count,
        result_number=result_number,
        providers=providers,
        categories=categories,
    )


@mcp.tool()
async def compare_keywords(
    keywords: list[str],
    start_date: str,
    end_date: str,
    group_by: str = "day",
) -> dict:
    """
    여러 키워드의 뉴스 트렌드를 비교 분석합니다.

    Args:
        keywords: 비교할 키워드 목록 (2-5개 권장)
        start_date: 검색 시작일 (YYYY-MM-DD)
        end_date: 검색 종료일 (YYYY-MM-DD)
        group_by: 집계 단위 (total/day/week/month)

    Returns:
        키워드 비교 결과 (키워드별 기사 수, 순위, 요약)

    Example:
        >>> result = await compare_keywords(
        ...     keywords=["AI", "반도체", "전기차"],
        ...     start_date="2025-12-01",
        ...     end_date="2025-12-15"
        ... )
    """
    return await analysis.compare_keywords(
        keywords=keywords,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
    )


@mcp.tool()
async def smart_sample(
    keyword: str,
    start_date: str,
    end_date: str,
    sample_size: int = 100,
    strategy: str = "stratified",
) -> dict:
    """
    대용량 검색 결과에서 대표 샘플을 추출합니다.

    Args:
        keyword: 검색 키워드
        start_date: 검색 시작일 (YYYY-MM-DD)
        end_date: 검색 종료일 (YYYY-MM-DD)
        sample_size: 추출할 샘플 수 (기본값: 100, 최대: 500)
        strategy: 샘플링 전략 (stratified/latest/random)

    Returns:
        샘플링 결과 (총 기사 수, 샘플 기사 목록, 커버리지 정보)

    Example:
        대용량 데이터에서 대표 100건 추출:
        >>> result = await smart_sample(
        ...     keyword="이재명",
        ...     start_date="2005-01-01",
        ...     end_date="2025-12-15",
        ...     sample_size=100
        ... )
    """
    return await analysis.smart_sample(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        sample_size=sample_size,
        strategy=strategy,
    )


@mcp.tool()
def cache_stats() -> dict:
    """
    캐시 통계 정보를 조회합니다.

    Returns:
        캐시 통계 (각 캐시의 크기, 사용률)

    Example:
        >>> stats = cache_stats()
        >>> print(f"검색 캐시 사용률: {stats['search']['usage_percent']:.1f}%")
    """
    return analysis.cache_stats()


@mcp.tool()
async def export_all_articles(
    keyword: str,
    start_date: str,
    end_date: str,
    output_format: str = "json",
    output_path: str | None = None,
    max_articles: int = 10000,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    include_content: bool = False,
) -> dict:
    """
    검색 결과 전체를 일괄 다운로드합니다.

    ⚠️ 대용량 데이터 분석의 핵심 도구입니다.
    search_news 결과가 100건 이상일 때 반드시 이 도구를 사용하세요.

    Args:
        keyword: 검색 키워드
        start_date: 검색 시작일 (YYYY-MM-DD)
        end_date: 검색 종료일 (YYYY-MM-DD)
        output_format: 출력 형식 (json, csv, jsonl)
        output_path: 저장할 파일 경로 (None이면 자동 생성)
        max_articles: 최대 다운로드 수 (기본값: 10000, 최대: 50000)
        providers: 언론사 필터 (예: ["경향신문", "한겨레"])
        categories: 카테고리 필터 (예: ["경제", "IT_과학"])
        include_content: 기사 본문 포함 여부 (True면 스크래핑, 시간 오래 걸림)

    Returns:
        내보내기 결과:
        - output_path: 저장된 파일 경로
        - exported_count: 내보낸 기사 수
        - analysis_code: Python 분석 코드 템플릿
        - next_steps: 다음 단계 안내

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📊 대용량 분석 워크플로우
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. 이 도구로 데이터를 로컬 파일로 저장
    2. 반환된 analysis_code를 scripts/*.py로 저장
    3. 사용자에게 "python scripts/*.py" 실행 안내
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    return await analysis.export_all_articles(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        output_format=output_format,
        output_path=output_path,
        max_articles=max_articles,
        providers=providers,
        categories=categories,
        include_content=include_content,
    )


@mcp.tool()
async def analyze_timeline(
    keyword: str,
    start_date: str,
    end_date: str,
    max_events: int = 10,
    articles_per_event: int = 3,
) -> dict:
    """
    키워드의 타임라인을 분석하여 주요 이벤트를 자동 탐지합니다.

    25만건 이상의 대용량 기사에서 시간별 주요 사건을 자동으로 추출합니다.
    NLP 기반으로 급증 시점 탐지, 키워드 추출, 대표 기사 선정을 수행합니다.

    Args:
        keyword: 분석할 키워드 (예: "한동훈", "AI", "비트코인")
        start_date: 분석 시작일 (YYYY-MM-DD)
        end_date: 분석 종료일 (YYYY-MM-DD)
        max_events: 추출할 최대 이벤트 수 (기본값: 10, 최대: 50)
        articles_per_event: 이벤트당 대표 기사 수 (기본값: 3)

    Returns:
        타임라인 분석 결과:
        - keyword: 분석 키워드
        - period: 분석 기간 정보 (start_date, end_date, months)
        - total_articles: 전체 기사 수
        - events: 주요 이벤트 리스트
            - period: 월 (YYYY-MM)
            - article_count: 기사 수
            - spike_ratio: 평균 대비 비율
            - top_keywords: 핵심 키워드 (최대 5개)
            - representative_articles: 대표 기사 (제목, 날짜, URL, 언론사)
        - event_count: 탐지된 이벤트 수
        - timeline_summary: 타임라인 요약 (마크다운)

    Example:
        10년간 인물의 주요 사건 자동 추출:
        >>> result = await analyze_timeline(
        ...     keyword="한동훈",
        ...     start_date="2015-01-01",
        ...     end_date="2025-12-20",
        ...     max_events=20
        ... )
        >>> print(result["timeline_summary"])

    Note:
        - 최소 1개월 이상의 기간이 필요합니다
        - 월별 기사 수가 평균의 1.5배 이상인 시점을 이벤트로 탐지합니다
        - 대표 기사는 다양한 언론사에서 시간순으로 선정됩니다
    """
    return await analysis.analyze_timeline(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        max_events=max_events,
        articles_per_event=articles_per_event,
    )


# ============================================================
# NOTE: get_network_analysis 제거됨
# 사유: /news/getNetworkDataAnalysis.do API는 브라우저 전용
#       httpx 직접 호출 시 302 → /err/error400.do 리다이렉트
# ============================================================


# ============================================================
# MCP Resources 등록
# ============================================================


@mcp.resource("stats://providers")
def providers_resource() -> str:
    """BigKinds에서 사용 가능한 언론사 코드 목록을 제공합니다."""
    return news_resources.get_providers_resource()


@mcp.resource("stats://categories")
def categories_resource() -> str:
    """BigKinds에서 사용 가능한 카테고리 코드 목록을 제공합니다."""
    return news_resources.get_categories_resource()


@mcp.resource("news://{keyword}/{date}")
async def news_resource(keyword: str, date: str) -> str:
    """
    특정 날짜의 키워드 검색 결과를 제공합니다.

    URI 예시: news://AI/2024-12-15
    """
    return await news_resources.get_news_resource(keyword, date)


@mcp.resource("article://{news_id}")
async def article_resource(news_id: str) -> str:
    """
    개별 기사 정보를 제공합니다.

    URI 예시: article://01100901.20241215...
    """
    return await news_resources.get_article_resource(news_id)


# ============================================================
# MCP Prompts 등록
# ============================================================


@mcp.prompt()
def news_analysis(
    keyword: str,
    start_date: str,
    end_date: str,
    analysis_type: str = "summary",
) -> str:
    """
    뉴스 분석을 위한 프롬프트를 생성합니다.

    Args:
        keyword: 분석할 키워드
        start_date: 분석 시작일 (YYYY-MM-DD)
        end_date: 분석 종료일 (YYYY-MM-DD)
        analysis_type: 분석 유형
            - summary: 주요 내용 요약
            - sentiment: 감성 분석
            - trend: 트렌드 분석
            - comparison: 언론사별 보도 비교
    """
    return prompt_analysis.news_analysis_prompt(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        analysis_type=analysis_type,
    )


@mcp.prompt()
def trend_report(
    keyword: str,
    days: int = 7,
) -> str:
    """
    트렌드 리포트 생성을 위한 프롬프트를 생성합니다.

    Args:
        keyword: 분석할 키워드
        days: 분석 기간 (일 단위, 기본 7일)
    """
    return prompt_analysis.trend_report_prompt(keyword=keyword, days=days)


@mcp.prompt()
def issue_briefing(
    date: str | None = None,
) -> str:
    """
    일일 이슈 브리핑을 위한 프롬프트를 생성합니다.

    Args:
        date: 브리핑 날짜 (YYYY-MM-DD). 생략하면 오늘
    """
    return prompt_analysis.issue_briefing_prompt(date=date)


@mcp.prompt()
def large_scale_analysis(
    keyword: str,
    start_date: str,
    end_date: str,
    analysis_goal: str = "general",
) -> str:
    """
    대용량 데이터 분석을 위한 워크플로우 프롬프트.

    100건 이상의 기사를 분석할 때 사용합니다.
    컨텍스트 윈도우 제한을 우회하여 정확한 분석을 수행합니다.

    Args:
        keyword: 분석할 키워드
        start_date: 분석 시작일 (YYYY-MM-DD)
        end_date: 분석 종료일 (YYYY-MM-DD)
        analysis_goal: 분석 목표
            - general: 일반 분석 (언론사별, 시간대별, 키워드 빈도)
            - tone: 논조 분석 (긍정/부정/중립)
            - comparison: 언론사별 보도 비교
            - timeline: 시계열 트렌드 분석
    """
    return prompt_analysis.large_scale_analysis_prompt(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        analysis_goal=analysis_goal,
    )


def main():
    """CLI 엔트리포인트."""
    mcp.run()


if __name__ == "__main__":
    main()
