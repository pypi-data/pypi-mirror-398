"""분석 관련 MCP Tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.async_client import AsyncBigKindsClient
    from ..core.cache import MCPCache

# 전역 인스턴스
_client: AsyncBigKindsClient | None = None
_cache: MCPCache | None = None


def init_analysis_tools(client: AsyncBigKindsClient, cache: MCPCache) -> None:
    """분석 도구 초기화."""
    global _client, _cache
    _client = client
    _cache = cache


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
        group_by: 집계 단위
            - "total": 전체 기간 총합
            - "day": 일별 집계 (최대 31일 권장)
            - "week": 주별 집계
            - "month": 월별 집계

    Returns:
        키워드 비교 결과:
            - keywords: 비교 키워드 목록
            - date_range: 분석 기간
            - comparisons: 키워드별 결과
                - keyword: 키워드
                - total_count: 총 기사 수
                - counts: 기간별 기사 수 (group_by != "total"인 경우)
                - rank: 순위 (기사 수 기준)
            - summary: 분석 요약
                - most_popular: 가장 많은 키워드
                - least_popular: 가장 적은 키워드
                - total_articles: 전체 기사 수

    Example:
        >>> result = await compare_keywords(
        ...     keywords=["AI", "반도체", "전기차"],
        ...     start_date="2025-12-01",
        ...     end_date="2025-12-15",
        ...     group_by="day"
        ... )
        >>> print(result["summary"]["most_popular"])
        {"keyword": "AI", "count": 15432}
    """
    if _client is None or _cache is None:
        raise RuntimeError("Analysis tools not initialized")

    # 입력 검증
    if not keywords or len(keywords) < 2:
        return {
            "success": False,
            "error": "INVALID_PARAMS",
            "message": "최소 2개 이상의 키워드가 필요합니다.",
        }

    if len(keywords) > 10:
        return {
            "success": False,
            "error": "INVALID_PARAMS",
            "message": "키워드는 최대 10개까지 지원합니다.",
        }

    # 각 키워드별로 get_article_count 호출
    from .search import get_article_count

    results = []
    for keyword in keywords:
        result = await get_article_count(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
        )

        if result.get("success", False):
            results.append({
                "keyword": keyword,
                "total_count": result["total_count"],
                "counts": result.get("counts", []),
            })
        else:
            # 에러가 발생한 키워드는 0건으로 처리
            results.append({
                "keyword": keyword,
                "total_count": 0,
                "counts": [],
                "error": result.get("message", "조회 실패"),
            })

    # 기사 수 기준 정렬 및 순위 부여
    results.sort(key=lambda x: x["total_count"], reverse=True)
    for i, result in enumerate(results, 1):
        result["rank"] = i

    # 요약 정보
    total_articles = sum(r["total_count"] for r in results)
    most_popular = results[0] if results else None
    least_popular = results[-1] if results else None

    return {
        "success": True,
        "keywords": keywords,
        "date_range": f"{start_date} to {end_date}",
        "group_by": group_by,
        "comparisons": results,
        "summary": {
            "most_popular": {
                "keyword": most_popular["keyword"],
                "count": most_popular["total_count"],
            } if most_popular else None,
            "least_popular": {
                "keyword": least_popular["keyword"],
                "count": least_popular["total_count"],
            } if least_popular else None,
            "total_articles": total_articles,
            "average_count": total_articles // len(results) if results else 0,
        },
    }


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
        strategy: 샘플링 전략
            - "stratified": 기간별 균등 분포 (기본값)
            - "latest": 최신 기사 우선
            - "random": 무작위 샘플링

    Returns:
        샘플링 결과:
            - success: 성공 여부
            - keyword: 검색 키워드
            - total_count: 전체 기사 수
            - sample_size: 추출된 샘플 수
            - strategy: 사용된 전략
            - articles: 샘플 기사 목록
            - coverage: 샘플링 커버리지 정보

    Example:
        대용량 데이터(112만 건)에서 대표 100건 추출:
        >>> result = await smart_sample(
        ...     keyword="이재명",
        ...     start_date="2005-01-01",
        ...     end_date="2025-12-15",
        ...     sample_size=100,
        ...     strategy="stratified"
        ... )
        >>> print(f"{result['total_count']}건 → {result['sample_size']}건")
    """
    if _client is None or _cache is None:
        raise RuntimeError("Analysis tools not initialized")

    # 입력 검증
    if sample_size > 500:
        return {
            "success": False,
            "error": "INVALID_PARAMS",
            "message": "sample_size는 최대 500까지 지원합니다.",
        }

    from .search import search_news, get_article_count

    # 1단계: 전체 기사 수 확인
    count_result = await get_article_count(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        group_by="total",
    )

    if not count_result.get("success", False):
        return count_result  # 에러 반환

    total_count = count_result["total_count"]

    # 2단계: 전략별 샘플링
    if strategy == "stratified":
        # 기간을 균등 분할하여 샘플링
        from datetime import datetime, timedelta

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (end - start).days + 1

        # 샘플 구간 수 (최대 20개 구간)
        num_intervals = min(20, sample_size // 5)
        samples_per_interval = sample_size // num_intervals

        articles = []
        for i in range(num_intervals):
            # 구간 계산
            interval_days = total_days // num_intervals
            interval_start = start + timedelta(days=i * interval_days)
            interval_end = start + timedelta(days=(i + 1) * interval_days - 1)
            if i == num_intervals - 1:
                interval_end = end  # 마지막 구간은 끝까지

            # 구간별 검색
            result = await search_news(
                keyword=keyword,
                start_date=interval_start.strftime("%Y-%m-%d"),
                end_date=interval_end.strftime("%Y-%m-%d"),
                page_size=samples_per_interval,
                sort_by="date",
            )

            if result.get("success", False):
                articles.extend(result["articles"])

    elif strategy == "latest":
        # 최신 기사 우선
        result = await search_news(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            page_size=sample_size,
            sort_by="date",
        )

        if not result.get("success", False):
            return result

        articles = result["articles"]

    elif strategy == "random":
        # 무작위 페이지에서 샘플링
        import random

        page_size = 20
        # BigKinds API는 최대 약 15-17페이지까지만 페이지네이션 지원
        # 보수적으로 15페이지로 제한 (약 300건)
        api_max_pages = 15
        max_pages = min(total_count // page_size, api_max_pages)

        # max_pages가 0이면 샘플링 불가
        if max_pages < 1:
            return {
                "success": False,
                "error": "INSUFFICIENT_DATA",
                "message": f"전체 기사 수({total_count})가 너무 적어 random 샘플링이 불가합니다.",
            }

        articles = []
        # 최소 1페이지는 샘플링하도록 보장
        num_pages_to_sample = max(1, min(sample_size // page_size, max_pages))
        pages_to_sample = random.sample(range(1, max_pages + 1), num_pages_to_sample)

        for page in pages_to_sample:
            result = await search_news(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=page_size,
                sort_by="date",
            )

            if result.get("success", False):
                articles.extend(result["articles"])

    else:
        return {
            "success": False,
            "error": "INVALID_PARAMS",
            "message": f"지원하지 않는 전략: {strategy}",
        }

    # 중복 제거 (news_id 기준)
    seen_ids = set()
    unique_articles = []
    for article in articles:
        news_id = article.get("news_id")
        if news_id and news_id not in seen_ids:
            seen_ids.add(news_id)
            unique_articles.append(article)

    return {
        "success": True,
        "keyword": keyword,
        "date_range": f"{start_date} to {end_date}",
        "total_count": total_count,
        "sample_size": len(unique_articles),
        "strategy": strategy,
        "articles": unique_articles[:sample_size],  # 요청 크기만큼만 반환
        "coverage": {
            "ratio": len(unique_articles) / total_count if total_count > 0 else 0,
            "description": f"{total_count:,}건 중 {len(unique_articles):,}건 샘플링",
        },
    }


def cache_stats() -> dict:
    """
    캐시 통계 정보를 조회합니다.

    Returns:
        캐시 통계:
            - search: 검색 캐시 통계
                - size: 현재 크기
                - maxsize: 최대 크기
                - usage_percent: 사용률
            - article: 기사 캐시 통계
            - count: 카운트 캐시 통계
            - generic: 일반 캐시 통계
            - url: URL 매핑 캐시 통계

    Example:
        >>> stats = cache_stats()
        >>> print(f"검색 캐시 사용률: {stats['search']['usage_percent']:.1f}%")
    """
    if _cache is None:
        raise RuntimeError("Analysis tools not initialized")

    raw_stats = _cache.stats()

    # 사용률 계산
    def add_usage(stat):
        size = stat["size"]
        maxsize = stat["maxsize"]
        stat["usage_percent"] = (size / maxsize * 100) if maxsize > 0 else 0
        return stat

    return {
        "search": add_usage(raw_stats["search"]),
        "article": add_usage(raw_stats["article"]),
        "count": add_usage(raw_stats["count"]),
        "generic": add_usage(raw_stats["generic"]),
    }


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
        output_format: 출력 형식
            - "json": JSON 파일 (기본값, 분석에 적합)
            - "csv": CSV 파일 (스프레드시트 호환)
            - "jsonl": JSON Lines 파일 (스트리밍 처리에 적합)
        output_path: 저장할 파일 경로 (None이면 자동 생성)
        max_articles: 최대 다운로드 수 (기본값: 10000, 최대: 50000)
        providers: 언론사 필터 (예: ["경향신문", "한겨레"])
        categories: 카테고리 필터 (예: ["경제", "IT_과학"])
        include_content: 기사 본문 포함 여부
            - False: 제목, 요약, 메타데이터만 (빠름)
            - True: 전문 포함 (느림, 언론사당 1건씩 수집 권장)

    Returns:
        내보내기 결과:
            - success: 성공 여부
            - output_path: 저장된 파일 경로 (절대 경로)
            - exported_count: 내보낸 기사 수
            - total_count: 전체 기사 수
            - file_size_human: 파일 크기 (읽기 쉬운 형식)
            - analysis_code: 분석 코드 템플릿 (Python)

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📊 대용량 분석 워크플로우 (100건 이상일 때 필수)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Step 1: 데이터 저장
        result = export_all_articles(
            keyword="분석 주제",
            start_date="2025-01-01",
            end_date="2025-12-15",
            output_path="data/articles.json"
        )

    Step 2: 반환된 analysis_code를 파일로 저장
        - result["analysis_code"]에 Python 분석 템플릿 포함
        - 이 코드를 scripts/analyze.py로 저장

    Step 3: 분석 실행 안내
        - "uv run python scripts/analyze.py" 또는
        - "python scripts/analyze.py" 실행

    ⚠️ 주의: 컨텍스트 윈도우 제한으로 대용량 데이터를 직접 분석하면
    정보 손실이 발생합니다. 반드시 로컬 파일로 저장 후 코드로 분석하세요.
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    import json
    import csv
    import os
    from datetime import datetime

    if _client is None or _cache is None:
        raise RuntimeError("Analysis tools not initialized")

    # 입력 검증
    if output_format not in ("json", "csv", "jsonl"):
        return {
            "success": False,
            "error": "INVALID_PARAMS",
            "message": f"지원하지 않는 형식: {output_format}. json, csv, jsonl 중 선택하세요.",
        }

    if max_articles > 50000:
        return {
            "success": False,
            "error": "INVALID_PARAMS",
            "message": "max_articles는 최대 50000까지 지원합니다.",
        }

    from .search import search_news, get_article_count
    from ..core.progress import ProgressTracker

    # 1단계: 전체 기사 수 확인
    count_result = await get_article_count(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        group_by="total",
    )

    if not count_result.get("success", False):
        return count_result

    total_count = count_result["total_count"]
    articles_to_fetch = min(total_count, max_articles)
    truncated = total_count > max_articles

    # 2단계: ProgressTracker 생성 (5000건 이상일 때만 활성화)
    progress = ProgressTracker(
        total=articles_to_fetch,
        description=f"'{keyword}' 기사 내보내기",
        threshold=5000,
        interval=10,
    )

    # 3단계: 페이지네이션으로 전체 수집
    all_articles = []
    page = 1
    page_size = 100  # 최대 페이지 크기

    while len(all_articles) < articles_to_fetch:
        result = await search_news(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            providers=providers,
            categories=categories,
            sort_by="date",
        )

        if not result.get("success", False):
            break

        articles = result.get("articles", [])
        if not articles:
            break

        all_articles.extend(articles)
        progress.update(len(articles))  # 진행률 업데이트
        page += 1

    # max_articles만큼만 유지
    all_articles = all_articles[:articles_to_fetch]

    # 중복 제거
    seen_ids = set()
    unique_articles = []
    for article in all_articles:
        news_id = article.get("news_id")
        if news_id and news_id not in seen_ids:
            seen_ids.add(news_id)
            unique_articles.append(article)

    # 3단계 (선택): 기사 본문 스크래핑
    if include_content:
        from .article import scrape_article_url

        for i, article in enumerate(unique_articles):
            url = article.get("url")
            if url:
                try:
                    scraped = await scrape_article_url(url=url, extract_images=False)
                    if scraped.get("success", False):
                        article["full_content"] = scraped.get("content", "")
                except Exception:
                    article["full_content"] = ""

    # 4단계: 파일 저장
    # safe_keyword는 파일명 및 분석 스크립트명에 사용
    safe_keyword = keyword.replace(" ", "_").replace("/", "_")[:20]
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"bigkinds_export_{safe_keyword}_{timestamp}.{output_format}"

    try:
        if output_format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "metadata": {
                        "keyword": keyword,
                        "date_range": f"{start_date} to {end_date}",
                        "total_count": total_count,
                        "exported_count": len(unique_articles),
                        "exported_at": datetime.now().isoformat(),
                        "truncated": truncated,
                    },
                    "articles": unique_articles,
                }, f, ensure_ascii=False, indent=2)

        elif output_format == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for article in unique_articles:
                    f.write(json.dumps(article, ensure_ascii=False) + "\n")

        elif output_format == "csv":
            if unique_articles:
                # CSV 필드 정의
                fieldnames = [
                    "news_id", "title", "summary", "publisher",
                    "published_date", "category", "url"
                ]
                if include_content:
                    fieldnames.append("full_content")

                with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(unique_articles)

        file_size = os.path.getsize(output_path)

    except Exception as e:
        return {
            "success": False,
            "error": "FILE_ERROR",
            "message": f"파일 저장 실패: {str(e)}",
        }

    # 진행률 완료 로깅
    progress.complete()

    # 분석 코드 템플릿 생성
    analysis_code = _generate_analysis_code(
        output_path=os.path.abspath(output_path),
        keyword=keyword,
        output_format=output_format,
    )

    return {
        "success": True,
        "keyword": keyword,
        "date_range": f"{start_date} to {end_date}",
        "total_count": total_count,
        "exported_count": len(unique_articles),
        "output_path": os.path.abspath(output_path),
        "format": output_format,
        "file_size_bytes": file_size,
        "file_size_human": _format_file_size(file_size),
        "truncated": truncated,
        "truncated_message": f"max_articles({max_articles})로 제한됨. 전체: {total_count:,}건" if truncated else None,
        "analysis_code": analysis_code,
        "next_steps": [
            f"1. 분석 코드를 파일로 저장: scripts/analyze_{safe_keyword}.py",
            "2. 코드 실행: python scripts/analyze_*.py",
            "3. 결과 확인 및 추가 분석 수행",
        ],
    }


def _format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형식으로 변환."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _generate_analysis_code(output_path: str, keyword: str, output_format: str) -> str:
    """분석 코드 템플릿 생성."""
    if output_format == "csv":
        load_code = (
            "import pandas as pd\n"
            "    data = pd.read_csv(DATA_FILE)\n"
            "    articles = data.to_dict('records')"
        )
    else:  # json or jsonl
        load_code = (
            'with open(DATA_FILE, "r", encoding="utf-8") as f:\n'
            "        data = json.load(f)\n"
            '    articles = data.get("articles", data) if isinstance(data, dict) else data'
        )

    return f'''"""BigKinds 데이터 분석 스크립트.

자동 생성됨 - 필요에 따라 수정하세요.

Usage:
    python scripts/analyze.py
"""

import json
from collections import Counter
from pathlib import Path

DATA_FILE = "{output_path}"


def load_data():
    """데이터 로드."""
    {load_code}
    return articles


def analyze_publishers(articles):
    """언론사별 기사 수 분석."""
    publishers = Counter(a.get("publisher", "Unknown") for a in articles)
    print("\\n📰 언론사별 기사 수:")
    for pub, count in publishers.most_common(10):
        print(f"  {{pub}}: {{count}}건")
    return publishers


def analyze_timeline(articles):
    """시간대별 기사 분포."""
    dates = Counter(a.get("published_date", "")[:10] for a in articles if a.get("published_date"))
    print("\\n📅 날짜별 기사 수:")
    for date, count in sorted(dates.items())[-10:]:
        print(f"  {{date}}: {{count}}건")
    return dates


def analyze_keywords(articles, top_n=20):
    """키워드 빈도 분석."""
    # 제목에서 키워드 추출 (간단한 방식)
    import re
    words = []
    for a in articles:
        title = a.get("title", "")
        # 한글 단어 추출
        words.extend(re.findall(r"[가-힣]{{2,}}", title))

    word_counts = Counter(words)
    print("\\n🔑 주요 키워드 (제목 기준):")
    for word, count in word_counts.most_common(top_n):
        print(f"  {{word}}: {{count}}회")
    return word_counts


def generate_summary(articles):
    """분석 요약."""
    print("\\n" + "=" * 50)
    print(f"📊 분석 요약: {keyword}")
    print("=" * 50)
    print(f"총 기사 수: {{len(articles):,}}건")

    publishers = set(a.get("publisher") for a in articles if a.get("publisher"))
    print(f"언론사 수: {{len(publishers)}}개")

    dates = [a.get("published_date", "")[:10] for a in articles if a.get("published_date")]
    if dates:
        print(f"기간: {{min(dates)}} ~ {{max(dates)}}")


def main():
    """메인 분석."""
    print(f"데이터 로드 중: {{DATA_FILE}}")
    articles = load_data()

    generate_summary(articles)
    analyze_publishers(articles)
    analyze_timeline(articles)
    analyze_keywords(articles)

    print("\\n✅ 분석 완료!")
    print("\\n💡 추가 분석이 필요하면 이 스크립트를 수정하세요.")


if __name__ == "__main__":
    main()
'''


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
        keyword: 분석할 키워드
        start_date: 분석 시작일 (YYYY-MM-DD)
        end_date: 분석 종료일 (YYYY-MM-DD)
        max_events: 추출할 최대 이벤트 수 (기본값: 10)
        articles_per_event: 이벤트당 대표 기사 수 (기본값: 3)

    Returns:
        타임라인 분석 결과:
            - keyword: 분석 키워드
            - period: 분석 기간 정보
            - total_articles: 전체 기사 수
            - events: 주요 이벤트 리스트
                - period: 월 (YYYY-MM)
                - article_count: 기사 수
                - spike_ratio: 평균 대비 비율
                - top_keywords: 핵심 키워드
                - representative_articles: 대표 기사
            - timeline_summary: 타임라인 요약 (마크다운)

    Example:
        >>> result = await analyze_timeline(
        ...     keyword="한동훈",
        ...     start_date="2015-01-01",
        ...     end_date="2025-12-20",
        ...     max_events=20
        ... )
        >>> print(result["timeline_summary"])
    """
    from datetime import datetime
    from .search import search_news, get_article_count
    from .timeline_utils import (
        detect_spikes,
        extract_keywords,
        select_representative_articles,
        generate_timeline_summary,
        parse_period_to_dates,
    )

    if _client is None or _cache is None:
        raise RuntimeError("Analysis tools not initialized")

    # 입력 검증
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.")

    days_diff = (end_dt - start_dt).days
    if days_diff < 30:
        raise ValueError("분석 기간이 너무 짧습니다. 최소 1개월 이상이 필요합니다.")

    # 1단계: 월별 기사 수 집계
    count_result = await get_article_count(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        group_by="month",
    )

    if not count_result.get("success", False):
        return {
            "success": False,
            "error": count_result.get("error", "UNKNOWN"),
            "message": count_result.get("message", "기사 수 집계 실패"),
        }

    total_count = count_result["total_count"]
    monthly_counts = {
        item["date"]: item["count"]
        for item in count_result.get("counts", [])
    }

    if total_count == 0:
        return {
            "success": True,
            "keyword": keyword,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "months": len(monthly_counts),
            },
            "total_articles": 0,
            "events": [],
            "timeline_summary": f"'{keyword}' 관련 기사가 없습니다.",
        }

    # 2단계: 스파이크(급증) 탐지
    spikes = detect_spikes(monthly_counts, threshold=1.5)

    # 스파이크를 기사 수 기준으로 정렬
    sorted_spikes = sorted(
        spikes.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )[:max_events]

    # 3단계: 각 스파이크 기간의 상세 분석
    events = []
    for period, spike_info in sorted_spikes:
        period_start, period_end = parse_period_to_dates(period)

        # 해당 기간의 기사 검색
        search_result = await search_news(
            keyword=keyword,
            start_date=period_start,
            end_date=period_end,
            page_size=50,  # 키워드 추출용
            sort_by="date",
        )

        if not search_result.get("success", False):
            continue

        articles = search_result.get("articles", [])

        # 키워드 추출 (검색 키워드는 제외)
        titles = [a.get("title", "") for a in articles]
        top_keywords = extract_keywords(
            titles,
            top_n=5,
            exclude_words={keyword} | set(keyword.split())
        )

        # 대표 기사 선정
        representative = select_representative_articles(
            [
                {
                    "title": a.get("title", ""),
                    "date": a.get("published_date", ""),
                    "url": a.get("url", ""),
                    "publisher": a.get("publisher", ""),
                    "news_id": a.get("news_id", ""),
                }
                for a in articles
            ],
            max_count=articles_per_event,
        )

        events.append({
            "period": period,
            "article_count": spike_info["count"],
            "spike_ratio": spike_info["ratio"],
            "average_count": spike_info["average"],
            "top_keywords": top_keywords,
            "representative_articles": representative,
        })

    # 시간순 정렬
    events.sort(key=lambda x: x["period"])

    # 4단계: 요약 생성
    timeline_summary = generate_timeline_summary(keyword, events)

    return {
        "success": True,
        "keyword": keyword,
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "months": len(monthly_counts),
        },
        "total_articles": total_count,
        "events": events,
        "event_count": len(events),
        "timeline_summary": timeline_summary,
    }
