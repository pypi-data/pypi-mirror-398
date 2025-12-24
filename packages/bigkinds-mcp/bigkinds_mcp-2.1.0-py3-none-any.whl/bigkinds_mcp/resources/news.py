"""MCP Resources for BigKinds."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.async_client import AsyncBigKindsClient
    from ..core.cache import MCPCache

# 전역 인스턴스 (서버 시작 시 초기화)
_client: AsyncBigKindsClient | None = None
_cache: MCPCache | None = None

# BigKinds 언론사 코드 (주요 언론사)
PROVIDER_CODES = {
    "01100001": "경향신문",
    "01100101": "국민일보",
    "01100201": "내일신문",
    "01100301": "동아일보",
    "01100401": "문화일보",
    "01100501": "서울신문",
    "01100601": "세계일보",
    "01100701": "조선일보",
    "01100801": "중앙일보",
    "01100901": "한겨레",
    "01101001": "한국일보",
    "01101101": "매일경제",
    "01101201": "한국경제",
    "02100101": "YTN",
    "02100201": "MBC",
    "02100301": "KBS",
    "02100401": "SBS",
}

# BigKinds 카테고리 코드
CATEGORY_CODES = {
    "정치": "정치",
    "경제": "경제",
    "사회": "사회",
    "문화": "문화",
    "국제": "국제",
    "지역": "지역",
    "스포츠": "스포츠",
    "IT_과학": "IT/과학",
}


def init_resources(client: AsyncBigKindsClient, cache: MCPCache) -> None:
    """리소스 초기화."""
    global _client, _cache
    _client = client
    _cache = cache


def get_providers_resource() -> str:
    """
    사용 가능한 언론사 코드 목록을 마크다운으로 반환합니다.

    Returns:
        언론사 코드 목록 (마크다운 형식)
    """
    lines = [
        "# BigKinds 언론사 코드",
        "",
        "뉴스 검색 시 `providers` 파라미터에 사용할 수 있는 언론사 목록입니다.",
        "",
        "| 코드 | 언론사명 |",
        "|------|----------|",
    ]

    for code, name in sorted(PROVIDER_CODES.items(), key=lambda x: x[1]):
        lines.append(f"| {code} | {name} |")

    lines.extend([
        "",
        "## 사용 예시",
        "",
        "```python",
        '# 특정 언론사만 검색',
        'search_news(',
        '    keyword="AI",',
        '    start_date="2024-12-01",',
        '    end_date="2024-12-15",',
        '    providers=["경향신문", "한겨레"]',
        ')',
        "```",
    ])

    return "\n".join(lines)


def get_categories_resource() -> str:
    """
    사용 가능한 카테고리 코드 목록을 마크다운으로 반환합니다.

    Returns:
        카테고리 코드 목록 (마크다운 형식)
    """
    lines = [
        "# BigKinds 카테고리 코드",
        "",
        "뉴스 검색 시 `categories` 파라미터에 사용할 수 있는 카테고리 목록입니다.",
        "",
        "| 코드 | 카테고리 |",
        "|------|----------|",
    ]

    for code, name in sorted(CATEGORY_CODES.items()):
        lines.append(f"| {code} | {name} |")

    lines.extend([
        "",
        "## 사용 예시",
        "",
        "```python",
        '# 특정 카테고리만 검색',
        'search_news(',
        '    keyword="AI",',
        '    start_date="2024-12-01",',
        '    end_date="2024-12-15",',
        '    categories=["경제", "IT_과학"]',
        ')',
        "```",
    ])

    return "\n".join(lines)


async def get_news_resource(keyword: str, date: str) -> str:
    """
    특정 날짜의 키워드 검색 결과를 마크다운으로 반환합니다.

    Args:
        keyword: 검색 키워드
        date: 검색 날짜 (YYYY-MM-DD)

    Returns:
        검색 결과 (마크다운 형식)
    """
    if _client is None:
        raise RuntimeError("Resources not initialized")

    from bigkinds.models import SearchRequest

    request = SearchRequest(
        keyword=keyword,
        start_date=date,
        end_date=date,
        start_no=1,
        result_number=20,
        sort_method="date",
    )

    response = await _client.search(request)

    lines = [
        f"# {keyword} - {date} 뉴스",
        "",
        f"총 {response.total_count}건의 기사가 검색되었습니다.",
        "",
        "## 검색 결과 (최신 20건)",
        "",
    ]

    if not response.articles:
        lines.append("검색 결과가 없습니다.")
    else:
        for idx, article in enumerate(response.articles, 1):
            title = article.title
            publisher = article.publisher or "알 수 없음"
            news_date = article.news_date[:10] if article.news_date else date
            news_id = article.news_id or ""

            lines.extend([
                f"### {idx}. {title}",
                "",
                f"- **언론사**: {publisher}",
                f"- **발행일**: {news_date}",
                f"- **기사 ID**: `{news_id}`",
                "",
            ])

    lines.extend([
        "---",
        "",
        "더 많은 결과를 보려면 `search_news` 도구를 사용하세요.",
    ])

    return "\n".join(lines)


async def get_article_resource(news_id: str) -> str:
    """
    개별 기사를 마크다운으로 반환합니다.

    Args:
        news_id: BigKinds 기사 ID

    Returns:
        기사 상세 정보 (마크다운 형식)

    Note:
        현재는 news_id만으로 기사 조회가 제한적입니다.
        전문을 보려면 `get_article` 도구에 URL을 함께 제공해야 합니다.
    """
    lines = [
        f"# 기사 상세 정보",
        "",
        f"**기사 ID**: `{news_id}`",
        "",
        "---",
        "",
        "기사 전문을 보려면 `get_article` 도구를 사용하세요:",
        "",
        "```python",
        f'get_article(news_id="{news_id}", include_full_content=True)',
        "```",
        "",
        "또는 원본 URL이 있다면:",
        "",
        "```python",
        f'get_article(news_id="{news_id}", url="원본 기사 URL")',
        "```",
    ]

    return "\n".join(lines)
