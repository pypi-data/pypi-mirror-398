"""
Article tools formatters (get_article, scrape_article_url).
"""

from typing import Any
from . import truncate_text, add_footer


def format_article_basic(result: dict[str, Any]) -> str:
    """
    get_article 결과를 마크다운으로 포맷.

    Args:
        result: get_article의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    # get_article returns the article data directly (not nested in "article" key)
    title = result.get("title", "제목 없음")
    provider = result.get("publisher", "언론사 미상")
    date = result.get("published_date", "날짜 미상")
    reporter = result.get("author", "")
    content = result.get("full_content", "")
    category = result.get("category", "")

    # 헤더
    md = f"# 📰 {title}\n\n"
    md += f"**언론사**: {provider}  \n"
    md += f"**날짜**: {date}  \n"

    if reporter:
        md += f"**기자**: {reporter}  \n"

    if category:
        md += f"**카테고리**: {category}  \n"

    md += "\n"

    # 본문 (500자 발췌)
    if content:
        # 요약 여부 확인
        is_summary = len(content) < 300  # 200자 요약인 경우

        if is_summary:
            md += "## 요약\n"
            md += f"{content}\n\n"
            hint = "전체 본문은 `include_full_content=True` 또는 `response_format=\"full\"` 사용"
        else:
            md += "## 본문 (발췌)\n"
            excerpt = truncate_text(content, max_length=500)
            md += f"{excerpt}\n\n"
            hint = "전체 본문은 `response_format=\"full\"` 사용"
    else:
        md += "본문을 가져올 수 없습니다.\n"
        hint = "URL 스크래핑을 시도하거나 나중에 다시 시도하세요"

    return add_footer(md, hint)


def format_scrape_article_basic(result: dict[str, Any]) -> str:
    """
    scrape_article_url 결과를 마크다운으로 포맷.

    Args:
        result: scrape_article_url의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    title = result.get("title", "제목 없음")
    content = result.get("content", "")
    author = result.get("author", "")
    published_date = result.get("published_date", "")

    # 헤더
    md = f"# 📰 {title}\n\n"

    if published_date:
        md += f"**날짜**: {published_date}  \n"

    if author:
        md += f"**작성자**: {author}  \n"

    md += "\n"

    # 본문 (500자 발췌)
    if content:
        excerpt = truncate_text(content, max_length=500)
        md += "## 본문 (발췌)\n"
        md += f"{excerpt}\n\n"
        hint = "전체 본문은 `response_format=\"full\"` 사용"
    else:
        md += "본문을 가져올 수 없습니다.\n"
        hint = "URL이 유효하지 않거나 스크래핑이 차단되었습니다"

    return add_footer(md, hint)
