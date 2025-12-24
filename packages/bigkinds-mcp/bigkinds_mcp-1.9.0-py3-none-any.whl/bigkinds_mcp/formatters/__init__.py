"""
Response formatters for basic (markdown) and full (JSON) modes.

PRD AC17: Response Format Management
- basic: 마크다운, 핵심 정보만, 컨텍스트 절약
- full: JSON, 전체 데이터, 상세 분석용
"""

from typing import Literal

ResponseFormat = Literal["basic", "full"]


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """텍스트를 지정된 길이로 자르기."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)].rstrip() + suffix


def format_number(num: int) -> str:
    """숫자를 천 단위 구분 포맷으로."""
    return f"{num:,}"


def create_progress_bar(value: float, max_value: float, width: int = 20) -> str:
    """프로그레스 바 생성 (0.0 ~ max_value)."""
    if max_value == 0:
        return "░" * width

    ratio = min(value / max_value, 1.0)
    filled = int(ratio * width)
    empty = width - filled

    return "█" * filled + "░" * empty


def format_trend_indicator(current: int, previous: int) -> str:
    """트렌드 지표 (📈/📉/➡️)."""
    if previous == 0:
        return "➡️"

    change = ((current - previous) / previous) * 100

    if change > 5:
        return f"📈 +{change:.1f}%"
    elif change < -5:
        return f"📉 {change:.1f}%"
    else:
        return "➡️ 보합"


def add_footer(content: str, hint: str = "전체 데이터가 필요하면 `response_format=\"full\"`을 사용하세요") -> str:
    """마크다운 푸터 추가."""
    return f"{content}\n\n---\n💡 **{hint}**"
