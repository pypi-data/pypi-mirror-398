"""
Search tools formatters (search_news, get_article_count).
"""

from typing import Any
from . import (
    format_number,
    truncate_text,
    add_footer,
    format_trend_indicator,
    create_progress_bar,
)


def format_search_news_basic(result: dict[str, Any]) -> str:
    """
    search_news 결과를 마크다운으로 포맷.

    Args:
        result: search_news의 전체 결과 (success, total_count, articles, ...)

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        # 에러 응답은 그대로 반환 (이미 한글화됨)
        return str(result)

    keyword = result.get("keyword", "검색어")
    total_count = result.get("total_count", 0)
    articles = result.get("articles", [])[:10]  # 상위 10건만

    # 메타데이터
    start_date = result.get("start_date", "")
    end_date = result.get("end_date", "")
    page = result.get("page", 1)
    page_size = result.get("page_size", 10)

    # 헤더
    md = f"# 🔍 \"{keyword}\" 검색 결과\n\n"
    md += f"**📅 기간**: {start_date} ~ {end_date}  \n"
    md += f"**📊 총 건수**: {format_number(total_count)}건  \n"
    md += f"**📄 표시**: 상위 {len(articles)}건 (페이지 {page})\n\n"

    if not articles:
        md += "검색 결과가 없습니다.\n"
        return add_footer(md, "다른 검색어나 기간을 시도해보세요")

    # 기사 목록
    md += "## 주요 기사\n\n"

    for idx, article in enumerate(articles, 1):
        title = article.get("title", "제목 없음")
        provider = article.get("publisher", "언론사 미상")
        date = article.get("published_date", "날짜 미상")
        summary = article.get("summary", "")

        # 요약 (100자)
        summary_short = truncate_text(summary, max_length=100)

        md += f"### {idx}. {title} - {provider} ({date})\n"
        md += f"> {summary_short}\n\n"

    # 페이지네이션 힌트
    if total_count > page_size:
        next_page = page + 1
        md += f"---\n📌 **다음 페이지**: `page={next_page}`로 추가 기사 조회  \n"

    return add_footer(md)


def format_article_count_basic(result: dict[str, Any]) -> str:
    """
    get_article_count 결과를 마크다운으로 포맷.

    Args:
        result: get_article_count의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    keyword = result.get("keyword", "검색어")
    total_count = result.get("total_count", 0)
    counts = result.get("counts", [])

    # 헤더
    md = f"# 📊 \"{keyword}\" 기사 수\n\n"
    md += f"**기간**: {result.get('start_date')} ~ {result.get('end_date')}  \n"
    md += f"**총 건수**: {format_number(total_count)}건\n\n"

    if not counts:
        md += "집계 데이터가 없습니다.\n"
        return add_footer(md)

    # 최근 7일 또는 전체 표시
    display_counts = counts[-7:] if len(counts) > 7 else counts

    md += f"## {'일별 추이 (최근 7일)' if len(counts) > 7 else '추이'}\n"

    for item in display_counts:
        period = item.get("period", "날짜 미상")
        count = item.get("count", 0)
        md += f"- {period}: {format_number(count)}건\n"

    # 통계
    if counts:
        avg_count = sum(c.get("count", 0) for c in counts) / len(counts)
        md += f"\n**평균**: {avg_count:.1f}건/일  \n"

        # 트렌드 (최근 vs 이전)
        if len(counts) >= 2:
            recent_avg = sum(c.get("count", 0) for c in counts[-3:]) / 3
            prev_avg = sum(c.get("count", 0) for c in counts[-6:-3]) / 3
            trend = format_trend_indicator(int(recent_avg), int(prev_avg))
            md += f"**추세**: {trend}\n"

    return add_footer(md, "일별 상세 데이터는 `response_format=\"full\"` 사용")
