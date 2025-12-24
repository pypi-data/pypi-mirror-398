"""
Visualization tools formatters (get_keyword_trends, get_related_keywords).
"""

from typing import Any
from . import (
    format_number,
    create_progress_bar,
    add_footer,
)


def format_keyword_trends_basic(result: dict[str, Any]) -> str:
    """
    get_keyword_trends 결과를 마크다운으로 포맷.

    Args:
        result: get_keyword_trends의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    keyword = result.get("keyword", "검색어")
    trends = result.get("trends", [])
    summary = result.get("summary", {})

    # 헤더
    md = f"# 📈 \"{keyword}\" 트렌드 분석\n\n"
    md += f"**기간**: {result.get('date_range', 'N/A')}  \n"
    md += f"**키워드 수**: {len(trends)}개\n\n"

    if not trends:
        md += "트렌드 데이터가 없습니다.\n"
        return add_footer(md)

    # 각 키워드별로 처리
    for trend_item in trends:
        kw = trend_item.get("keyword", "")
        data_points = trend_item.get("data", [])
        total_count = trend_item.get("total_count", 0)

        md += f"## {kw} ({format_number(total_count)}건)\n\n"

        if not data_points:
            md += "데이터 포인트가 없습니다.\n\n"
            continue

        # 시각화 (ASCII 그래프) - 30개 이하만
        if len(data_points) <= 30:
            md += "```\n"

            # 최대값 찾기
            max_count = max(d.get("count", 0) for d in data_points)

            for point in data_points:
                date = point.get("date", "")
                count = point.get("count", 0)

                # 프로그레스 바
                bar = create_progress_bar(count, max_count, width=20)

                # 피크 표시
                indicator = " ⬆️ Peak" if count == max_count else ""

                md += f"{date[:10]}: {bar} {format_number(count)}건{indicator}\n"

            md += "```\n\n"
        else:
            # 너무 많으면 최근 7개만
            md += "### 최근 7일\n"
            recent = data_points[-7:]

            for point in recent:
                date = point.get("date", "")
                count = point.get("count", 0)
                md += f"- {date}: {format_number(count)}건\n"

            md += "\n"

    return add_footer(md, "전체 시계열 데이터는 `response_format=\"full\"` 사용")


def format_related_keywords_basic(result: dict[str, Any]) -> str:
    """
    get_related_keywords 결과를 마크다운으로 포맷.

    Args:
        result: get_related_keywords의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    keyword = result.get("keyword", "검색어")
    related_words = result.get("related_words", [])[:20]  # 상위 20개만

    # 헤더
    md = f"# 🔗 \"{keyword}\" 연관어 분석\n\n"
    md += f"**기간**: {result.get('start_date')} ~ {result.get('end_date')}  \n"
    md += f"**발견된 연관어**: {len(related_words)}개\n\n"

    if not related_words:
        md += "연관어를 찾을 수 없습니다.\n"
        return add_footer(md)

    # 연관어 목록 (TF-IDF 기반)
    md += "## 주요 연관어 (Top 20)\n\n"

    # 최대 점수
    max_score = max(w.get("score", 0) for w in related_words) if related_words else 1

    for idx, word_data in enumerate(related_words, 1):
        word = word_data.get("word", "")
        score = word_data.get("score", 0)

        # 점수를 프로그레스 바로
        bar = create_progress_bar(score, max_score, width=15)

        # 순위 이모지
        if idx == 1:
            rank = "🥇"
        elif idx == 2:
            rank = "🥈"
        elif idx == 3:
            rank = "🥉"
        else:
            rank = f"{idx}."

        md += f"{rank} **{word}** {bar} ({score:.2f})\n"

    return add_footer(md, "전체 연관어 및 TF-IDF 점수는 `response_format=\"full\"` 사용")
