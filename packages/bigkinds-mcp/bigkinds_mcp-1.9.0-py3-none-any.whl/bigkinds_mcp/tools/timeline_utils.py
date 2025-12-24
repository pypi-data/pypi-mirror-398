"""타임라인 분석 유틸리티 함수.

이벤트 탐지, 키워드 추출, 대표 기사 선정 등의 NLP 기능 제공.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


def detect_spikes(
    monthly_counts: dict[str, int],
    threshold: float = 2.0,
) -> dict[str, dict]:
    """월별 기사 수에서 급증 시점(스파이크)을 탐지합니다.

    Args:
        monthly_counts: 월별 기사 수 {"2024-01": 100, "2024-02": 500, ...}
        threshold: 평균 대비 배수 기준 (기본값: 2.0 = 평균의 2배 이상)

    Returns:
        스파이크 월과 정보 {"2024-02": {"count": 500, "ratio": 3.2}, ...}
    """
    if not monthly_counts:
        return {}

    counts = list(monthly_counts.values())
    avg = sum(counts) / len(counts)

    if avg == 0:
        return {}

    spikes = {}
    for period, count in monthly_counts.items():
        ratio = count / avg
        if ratio >= threshold:
            spikes[period] = {
                "count": count,
                "ratio": round(ratio, 2),
                "average": round(avg, 1),
            }

    return spikes


def extract_keywords(
    titles: list[str],
    top_n: int = 5,
    exclude_words: set[str] | None = None,
) -> list[str]:
    """제목 목록에서 핵심 키워드를 추출합니다.

    Args:
        titles: 기사 제목 리스트
        top_n: 추출할 키워드 수
        exclude_words: 제외할 단어 세트

    Returns:
        핵심 키워드 리스트 (빈도순)
    """
    if not titles:
        return []

    # 기본 불용어
    stop_words = {
        "의", "가", "이", "은", "는", "을", "를", "에", "에서", "로", "으로",
        "와", "과", "도", "만", "부터", "까지", "에게", "한테", "께",
        "하다", "있다", "되다", "하는", "있는", "된", "한", "할", "함",
        "것", "등", "및", "더", "또", "그", "저", "이런", "저런",
        "위해", "대해", "통해", "관련", "대한", "따른",
        "오늘", "내일", "어제", "올해", "지난해", "작년",
        "기자", "뉴스", "보도", "취재", "속보", "단독",
    }

    if exclude_words:
        stop_words.update(exclude_words)

    # 모든 제목에서 명사 추출 (간단한 정규식 기반)
    words = []
    for title in titles:
        # 한글 2글자 이상 단어 추출
        matches = re.findall(r"[가-힣]{2,}", title)
        words.extend(matches)

    # 불용어 제거 및 빈도 계산
    filtered = [w for w in words if w not in stop_words and len(w) >= 2]
    counter = Counter(filtered)

    # 상위 N개 반환
    return [word for word, _ in counter.most_common(top_n)]


def select_representative_articles(
    articles: list[dict],
    max_count: int = 3,
) -> list[dict]:
    """대표 기사를 선정합니다.

    선정 기준:
    1. 다양한 언론사에서 선택 (다양성)
    2. 시간순 분산 (초반, 중반, 후반)

    Args:
        articles: 기사 목록 [{"title", "date", "publisher", "url"}, ...]
        max_count: 선정할 기사 수

    Returns:
        대표 기사 리스트
    """
    if not articles:
        return []

    if len(articles) <= max_count:
        return articles

    # 언론사별 그룹화
    by_publisher: dict[str, list] = {}
    for article in articles:
        publisher = article.get("publisher", "unknown")
        if publisher not in by_publisher:
            by_publisher[publisher] = []
        by_publisher[publisher].append(article)

    selected = []
    publishers_used = set()

    # 1. 다양한 언론사에서 선택
    for publisher, pub_articles in sorted(by_publisher.items(), key=lambda x: -len(x[1])):
        if len(selected) >= max_count:
            break
        if publisher not in publishers_used and pub_articles:
            # 해당 언론사에서 첫 번째 기사 선택
            selected.append(pub_articles[0])
            publishers_used.add(publisher)

    # 2. 부족하면 날짜순으로 채우기
    if len(selected) < max_count:
        remaining = [a for a in articles if a not in selected]
        # 날짜순 정렬 후 균등 분산 선택
        remaining.sort(key=lambda x: x.get("date", ""))
        step = max(1, len(remaining) // (max_count - len(selected)))
        for i in range(0, len(remaining), step):
            if len(selected) >= max_count:
                break
            if remaining[i] not in selected:
                selected.append(remaining[i])

    # 날짜순 정렬 후 반환
    selected.sort(key=lambda x: x.get("date", ""))
    return selected[:max_count]


def generate_timeline_summary(
    keyword: str,
    events: list[dict],
) -> str:
    """타임라인 요약을 생성합니다.

    Args:
        keyword: 검색 키워드
        events: 이벤트 리스트

    Returns:
        마크다운 형식의 요약 문자열
    """
    if not events:
        return f"'{keyword}' 관련 주요 이벤트가 탐지되지 않았습니다."

    lines = [f"## '{keyword}' 주요 타임라인\n"]

    for event in events:
        period = event.get("period", "")
        count = event.get("article_count", 0)
        keywords = event.get("top_keywords", [])
        ratio = event.get("spike_ratio", 1.0)

        # 월 형식 변환 (2024-03 -> 2024년 3월)
        if "-" in period:
            year, month = period.split("-")
            period_display = f"{year}년 {int(month)}월"
        else:
            period_display = period

        keyword_str = ", ".join(keywords[:3]) if keywords else ""

        lines.append(f"### {period_display}")
        lines.append(f"- 기사 수: {count:,}건 (평균 대비 {ratio:.1f}배)")
        if keyword_str:
            lines.append(f"- 핵심 키워드: {keyword_str}")
        lines.append("")

    return "\n".join(lines)


def parse_period_to_dates(period: str) -> tuple[str, str]:
    """월 기간을 시작일/종료일로 변환합니다.

    Args:
        period: "2024-03" 형식

    Returns:
        (시작일, 종료일) 튜플 ("2024-03-01", "2024-03-31")
    """
    import calendar

    year, month = period.split("-")
    year, month = int(year), int(month)

    _, last_day = calendar.monthrange(year, month)

    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

    return start_date, end_date
