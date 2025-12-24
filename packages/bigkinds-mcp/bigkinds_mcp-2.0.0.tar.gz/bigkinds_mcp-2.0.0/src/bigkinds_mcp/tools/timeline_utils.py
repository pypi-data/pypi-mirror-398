"""타임라인 분석 유틸리티 함수.

이벤트 탐지, 키워드 추출, 대표 기사 선정 등의 NLP 기능 제공.
v2.0: kiwipiepy 형태소 분석, 분기별 필수 추출, next_steps 생성
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# kiwipiepy lazy loading (서버 시작 시 초기화 지연)
_kiwi = None


def _get_kiwi():
    """Kiwi 인스턴스를 lazy loading으로 반환."""
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi
        _kiwi = Kiwi()
    return _kiwi


# 품사 태그 라벨
POS_LABELS = {
    "NNP": "고유명사",
    "NNG": "일반명사",
    "NNB": "의존명사",
    "NR": "수사",
    "NP": "대명사",
    "VV": "동사",
    "VA": "형용사",
    "VX": "보조용언",
    "VCP": "긍정지정사",
    "VCN": "부정지정사",
    "MM": "관형사",
    "MAG": "일반부사",
    "MAJ": "접속부사",
}

# 기본 불용어
STOP_WORDS = {
    # 일반 불용어
    "것", "등", "및", "더", "또", "그", "저", "이런", "저런",
    "위해", "대해", "통해", "관련", "대한", "따른", "위한",
    "오늘", "내일", "어제", "올해", "지난해", "작년", "지난",
    "기자", "뉴스", "보도", "취재", "속보", "단독", "종합",
    "사진", "영상", "동영상", "제공", "연합뉴스",
    # 일반 명사
    "경우", "때문", "이후", "이전", "현재", "당시", "최근",
    "가능", "필요", "예정", "계획", "방침", "방안", "전망",
    "주장", "발표", "설명", "지적", "강조", "언급", "요청",
}


def detect_spikes(
    monthly_counts: dict[str, int],
    threshold: float = 1.5,
) -> dict[str, dict]:
    """월별 기사 수에서 급증 시점(스파이크)을 탐지합니다.

    Args:
        monthly_counts: 월별 기사 수 {"2024-01": 100, "2024-02": 500, ...}
        threshold: 평균 대비 배수 기준 (기본값: 1.5 = 평균의 1.5배 이상)

    Returns:
        스파이크 월과 정보 {"2024-02": {"count": 500, "ratio": 3.2, "type": "spike"}, ...}
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
                "type": "spike",
            }

    return spikes


def ensure_quarterly_events(
    monthly_counts: dict[str, int],
    spikes: dict[str, dict],
    max_events: int = 10,
) -> list[dict]:
    """분기별 최소 1개 이벤트를 보장합니다.

    스파이크가 없는 분기에서도 해당 분기의 최대 기사 월을 선택합니다.

    Args:
        monthly_counts: 월별 기사 수
        spikes: detect_spikes 결과
        max_events: 최대 이벤트 수

    Returns:
        이벤트 리스트 (시간순 정렬)
    """
    if not monthly_counts:
        return []

    # 분기별 그룹화
    quarters: dict[str, list[tuple[str, int]]] = {}
    for period, count in monthly_counts.items():
        try:
            year, month = period.split("-")
            quarter = f"{year}-Q{(int(month) - 1) // 3 + 1}"
            if quarter not in quarters:
                quarters[quarter] = []
            quarters[quarter].append((period, count))
        except (ValueError, IndexError):
            continue

    events = []
    avg = sum(monthly_counts.values()) / len(monthly_counts)

    for quarter in sorted(quarters.keys()):
        months = quarters[quarter]

        # 1. 해당 분기에 스파이크가 있으면 가장 큰 것 사용
        quarter_spikes = [
            (period, spikes[period])
            for period, _ in months
            if period in spikes
        ]

        if quarter_spikes:
            # 가장 큰 스파이크 선택
            best = max(quarter_spikes, key=lambda x: x[1]["count"])
            events.append({
                "period": best[0],
                "count": best[1]["count"],
                "ratio": best[1]["ratio"],
                "average": best[1]["average"],
                "type": "spike",
                "quarter": quarter,
            })
        else:
            # 2. 스파이크 없으면 해당 분기에서 가장 기사 많은 월 선택
            best_month = max(months, key=lambda x: x[1])
            events.append({
                "period": best_month[0],
                "count": best_month[1],
                "ratio": round(best_month[1] / avg, 2) if avg > 0 else 1.0,
                "average": round(avg, 1),
                "type": "quarterly_peak",
                "quarter": quarter,
            })

    # max_events 초과 시 우선순위 정렬
    if len(events) > max_events:
        # 스파이크 우선, 그 다음 기사 수 순
        events.sort(key=lambda x: (x["type"] != "spike", -x["count"]))
        events = events[:max_events]

    # 시간순 정렬
    events.sort(key=lambda x: x["period"])

    return events


def extract_keywords(
    titles: list[str],
    top_n: int = 5,
    exclude_words: set[str] | None = None,
) -> list[str]:
    """제목 목록에서 핵심 키워드를 추출합니다 (하위 호환용).

    Args:
        titles: 기사 제목 리스트
        top_n: 추출할 키워드 수
        exclude_words: 제외할 단어 세트

    Returns:
        핵심 키워드 리스트 (빈도순)
    """
    result = extract_keywords_nlp(titles, top_n, exclude_words)
    return [item["word"] for item in result]


def extract_keywords_nlp(
    titles: list[str],
    top_n: int = 5,
    exclude_words: set[str] | None = None,
    pos_filter: set[str] | None = None,
) -> list[dict]:
    """형태소 분석 기반 키워드 추출.

    kiwipiepy를 사용하여 명사, 동사, 형용사 등을 정확하게 추출합니다.

    Args:
        titles: 기사 제목 리스트
        top_n: 추출할 키워드 수
        exclude_words: 제외할 단어 세트
        pos_filter: 추출할 품사 태그 (기본: 고유명사, 일반명사, 동사, 형용사)

    Returns:
        [{"word": "한동훈", "pos": "NNP", "pos_label": "고유명사", "count": 45}, ...]
    """
    if not titles:
        return []

    # 기본 품사 필터: 고유명사, 일반명사, 동사, 형용사
    if pos_filter is None:
        pos_filter = {"NNP", "NNG", "VV", "VA"}

    # 불용어 세트 구성
    stop_words = STOP_WORDS.copy()
    if exclude_words:
        stop_words.update(exclude_words)

    kiwi = _get_kiwi()
    word_counts: Counter = Counter()
    word_pos: dict[str, str] = {}

    for title in titles:
        try:
            tokens = kiwi.tokenize(title)
            for token in tokens:
                word = token.form
                pos = token.tag

                # 품사 필터링
                if pos not in pos_filter:
                    continue

                # 길이 필터 (2글자 이상)
                if len(word) < 2:
                    continue

                # 불용어 제외
                if word in stop_words:
                    continue

                # 숫자만으로 구성된 단어 제외
                if word.isdigit():
                    continue

                word_counts[word] += 1
                word_pos[word] = pos

        except Exception:
            # 토큰화 실패 시 정규식 fallback
            matches = re.findall(r"[가-힣]{2,}", title)
            for word in matches:
                if word not in stop_words and len(word) >= 2:
                    word_counts[word] += 1
                    if word not in word_pos:
                        word_pos[word] = "NNG"  # 기본값

    # 상위 N개 반환
    result = []
    for word, count in word_counts.most_common(top_n):
        pos = word_pos.get(word, "NNG")
        result.append({
            "word": word,
            "pos": pos,
            "pos_label": POS_LABELS.get(pos, "기타"),
            "count": count,
        })

    return result


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
            selected.append(pub_articles[0])
            publishers_used.add(publisher)

    # 2. 부족하면 날짜순으로 채우기
    if len(selected) < max_count:
        remaining = [a for a in articles if a not in selected]
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
        count = event.get("article_count", event.get("count", 0))
        ratio = event.get("spike_ratio", event.get("ratio", 1.0))
        event_type = event.get("type", "spike")

        # 키워드 처리 (구버전 호환)
        keywords = event.get("top_keywords", [])
        if keywords and isinstance(keywords[0], dict):
            keyword_str = ", ".join(k["word"] for k in keywords[:3])
        elif keywords:
            keyword_str = ", ".join(keywords[:3])
        else:
            keyword_str = ""

        # 월 형식 변환 (2024-03 -> 2024년 3월)
        if "-" in period:
            year, month = period.split("-")
            period_display = f"{year}년 {int(month)}월"
        else:
            period_display = period

        # 이벤트 타입 표시
        type_marker = "🔥" if event_type == "spike" else "📊"

        lines.append(f"### {type_marker} {period_display}")
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


def generate_next_steps(
    tool_name: str,
    result: dict,
    context: dict | None = None,
) -> list[dict]:
    """도구 결과에 기반한 다음 단계를 생성합니다.

    Args:
        tool_name: 도구 이름
        result: 도구 실행 결과
        context: 추가 컨텍스트 (keyword, start_date, end_date 등)

    Returns:
        next_steps 리스트
    """
    if context is None:
        context = {}

    generators = {
        "search_news": _generate_next_steps_search,
        "analyze_timeline": _generate_next_steps_timeline,
        "compare_keywords": _generate_next_steps_compare,
        "get_today_issues": _generate_next_steps_issues,
        "export_all_articles": _generate_next_steps_export,
    }

    generator = generators.get(tool_name)
    if generator:
        return generator(result, context)

    return []


def _generate_next_steps_search(result: dict, context: dict) -> list[dict]:
    """search_news 결과에 대한 next_steps 생성."""
    steps = []
    total = result.get("total_count", 0)
    keyword = context.get("keyword", result.get("keyword", ""))
    start_date = context.get("start_date", "")
    end_date = context.get("end_date", "")

    if total >= 100:
        steps.append({
            "priority": "high",
            "action": "export_all_articles",
            "reason": f"{total:,}건은 컨텍스트 제한 초과. 로컬 저장 후 분석 필수",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "output_format": "json",
            },
        })

    if total >= 500:
        steps.append({
            "priority": "high",
            "action": "analyze_timeline",
            "reason": "대용량 데이터의 시간별 주요 이벤트 파악",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "max_events": 10,
            },
        })

    if 0 < total < 100:
        articles = result.get("articles", [])[:3]
        for article in articles:
            if article.get("news_id"):
                steps.append({
                    "priority": "medium",
                    "action": "get_article",
                    "reason": f"'{article.get('title', '')[:30]}...' 상세 조회",
                    "params": {"news_id": article["news_id"]},
                })

    return steps


def _generate_next_steps_timeline(result: dict, context: dict) -> list[dict]:
    """analyze_timeline 결과에 대한 next_steps 생성."""
    steps = []
    events = result.get("events", [])
    keyword = result.get("keyword", context.get("keyword", ""))
    period = result.get("period", {})
    start_date = period.get("start_date", context.get("start_date", ""))
    end_date = period.get("end_date", context.get("end_date", ""))

    if events:
        # 가장 큰 이벤트 심층 분석
        top_event = max(events, key=lambda e: e.get("article_count", e.get("count", 0)))
        period_start, period_end = parse_period_to_dates(top_event["period"])

        steps.append({
            "priority": "high",
            "action": "search_news",
            "reason": f"{top_event['period']} 이벤트 심층 분석",
            "params": {
                "keyword": keyword,
                "start_date": period_start,
                "end_date": period_end,
                "page_size": 50,
            },
        })

        # 발견된 키워드로 비교 분석
        all_keywords = set()
        for event in events[:3]:
            top_kw = event.get("top_keywords", [])
            if top_kw:
                if isinstance(top_kw[0], dict):
                    all_keywords.update(k["word"] for k in top_kw[:2])
                else:
                    all_keywords.update(top_kw[:2])

        if len(all_keywords) >= 2:
            steps.append({
                "priority": "medium",
                "action": "compare_keywords",
                "reason": "발견된 키워드 간 관계 분석",
                "params": {
                    "keywords": list(all_keywords)[:5],
                    "start_date": start_date,
                    "end_date": end_date,
                    "group_by": "month",
                },
            })

    # 연관어 분석 권장 (로그인 필요)
    steps.append({
        "priority": "low",
        "action": "get_related_keywords",
        "reason": "연관어 네트워크로 숨겨진 연결고리 발견",
        "params": {
            "keyword": keyword,
            "start_date": start_date,
            "end_date": end_date,
        },
        "requires_auth": True,
    })

    return steps


def _generate_next_steps_compare(result: dict, context: dict) -> list[dict]:
    """compare_keywords 결과에 대한 next_steps 생성."""
    steps = []
    comparisons = result.get("comparisons", [])
    date_range = result.get("date_range", "")

    if " to " in date_range:
        start_date, end_date = date_range.split(" to ")
    else:
        start_date = context.get("start_date", "")
        end_date = context.get("end_date", "")

    # 각 키워드별 타임라인 분석
    for comp in comparisons[:3]:
        if comp.get("total_count", 0) >= 500:
            steps.append({
                "priority": "medium",
                "action": "analyze_timeline",
                "reason": f"'{comp['keyword']}' 주요 이벤트 파악",
                "params": {
                    "keyword": comp["keyword"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "max_events": 5,
                },
            })

    return steps


def _generate_next_steps_issues(result: dict, context: dict) -> list[dict]:
    """get_today_issues 결과에 대한 next_steps 생성."""
    steps = []
    results = result.get("results", {})

    for date_key, date_data in results.items():
        top_issues = date_data.get("issues", [])[:2]
        for issue in top_issues:
            steps.append({
                "priority": "medium",
                "action": "search_news",
                "reason": f"'{issue['title']}' 관련 기사 검색",
                "params": {
                    "keyword": issue["title"],
                    "start_date": date_key,
                    "end_date": date_key,
                    "page_size": 20,
                },
            })
            steps.append({
                "priority": "low",
                "action": "analyze_timeline",
                "reason": f"'{issue['title']}' 이슈 배경 분석",
                "params": {
                    "keyword": issue["title"],
                    "start_date": (
                        f"{int(date_key[:4]) - 1}-{date_key[5:7]}-{date_key[8:10]}"
                        if len(date_key) >= 10 else date_key
                    ),
                    "end_date": date_key,
                },
            })

    return steps[:6]  # 최대 6개


def _generate_next_steps_export(result: dict, context: dict) -> list[dict]:
    """export_all_articles 결과에 대한 next_steps 생성."""
    steps = []

    if result.get("success"):
        output_path = result.get("output_path", "")
        keyword = result.get("keyword", "")
        safe_keyword = keyword.replace(" ", "_").replace("/", "_")[:20]

        steps.append({
            "priority": "high",
            "action": "execute_code",
            "reason": "저장된 데이터로 Python 분석 실행",
            "params": {
                "script_path": f"scripts/analyze_{safe_keyword}.py",
                "data_path": output_path,
            },
            "instruction": (
                "1. result['analysis_code']를 파일로 저장\n"
                f"2. python scripts/analyze_{safe_keyword}.py 실행"
            ),
        })

        # 샘플 기사 상세 조회
        articles = result.get("articles", [])[:2]
        for article in articles:
            if article.get("news_id"):
                steps.append({
                    "priority": "low",
                    "action": "get_article",
                    "reason": "샘플 기사 상세 내용 확인",
                    "params": {"news_id": article["news_id"]},
                })

    return steps
