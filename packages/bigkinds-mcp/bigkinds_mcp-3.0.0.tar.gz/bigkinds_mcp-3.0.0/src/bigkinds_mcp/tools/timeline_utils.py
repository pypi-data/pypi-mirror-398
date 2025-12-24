"""타임라인 분석 유틸리티 함수.

이벤트 탐지, 키워드 추출, 대표 기사 선정 등의 NLP 기능 제공.
v2.0: kiwipiepy 형태소 분석, 분기별 필수 추출, next_steps 생성
v2.1: 유즈케이스별 next_steps 확장, 전체 도구 커버리지
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Literal


# =============================================================================
# 유즈케이스 타입 정의
# =============================================================================

UsecaseType = Literal[
    "news_monitoring",    # 실시간 뉴스 추적
    "deep_research",      # 인물/사건 심층 분석
    "trend_analysis",     # 트렌드/비교 분석
    "data_collection",    # 대용량 수집
    "article_detail",     # 개별 기사 분석
]


def detect_usecase(
    tool_name: str,
    result: dict,
    context: dict | None = None,
) -> UsecaseType:
    """결과와 컨텍스트를 기반으로 유즈케이스를 감지합니다.

    Args:
        tool_name: 도구 이름
        result: 도구 실행 결과
        context: 추가 컨텍스트

    Returns:
        감지된 유즈케이스 타입
    """
    context = context or {}
    total_count = result.get("total_count", 0)

    # 1. 데이터 수집 패턴: 100건 이상 + export 관련
    if tool_name == "export_all_articles":
        return "data_collection"

    if total_count >= 100:
        return "data_collection"

    # 2. 뉴스 모니터링 패턴: 오늘 이슈, 당일 검색
    if tool_name == "get_today_issues":
        return "news_monitoring"

    start_date = context.get("start_date", "")
    end_date = context.get("end_date", "")
    if start_date and end_date and start_date == end_date:
        return "news_monitoring"

    # 3. 트렌드 분석 패턴: 비교, 트렌드 도구
    if tool_name in ("compare_keywords", "get_keyword_trends"):
        return "trend_analysis"

    # 4. 개별 기사 분석 패턴
    if tool_name in ("get_article", "scrape_article_url", "get_article_thumbnail"):
        return "article_detail"

    # 5. 심층 리서치 패턴: 장기간, 타임라인 분석
    if tool_name == "analyze_timeline":
        return "deep_research"

    # 6. 기본값: 기간이 길면 심층 리서치
    if start_date and end_date:
        from datetime import datetime
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            if (end - start).days >= 90:
                return "deep_research"
        except ValueError:
            pass

    # 기본값
    return "news_monitoring"

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

    v2.1: 유즈케이스 감지 및 전체 도구 커버리지

    Args:
        tool_name: 도구 이름
        result: 도구 실행 결과
        context: 추가 컨텍스트 (keyword, start_date, end_date 등)

    Returns:
        next_steps 리스트 (확장된 스키마):
            - usecase: 현재 유즈케이스 컨텍스트
            - priority: high/medium/low
            - action: 호출할 도구명
            - reason: 권장 이유
            - params: 도구 호출 파라미터
            - depends_on: 선행 조건 (이미 실행된 도구)
            - requires_auth: 로그인 필요 여부
            - context_hint: LLM 힌트
    """
    if context is None:
        context = {}

    # 유즈케이스 감지
    usecase = detect_usecase(tool_name, result, context)

    generators = {
        "search_news": _generate_next_steps_search,
        "analyze_timeline": _generate_next_steps_timeline,
        "compare_keywords": _generate_next_steps_compare,
        "get_today_issues": _generate_next_steps_issues,
        "export_all_articles": _generate_next_steps_export,
        # v2.1 추가
        "get_article": _generate_next_steps_article,
        "get_article_count": _generate_next_steps_article_count,
        "get_keyword_trends": _generate_next_steps_trends,
        "get_related_keywords": _generate_next_steps_related,
        "smart_sample": _generate_next_steps_sample,
        "scrape_article_url": _generate_next_steps_scrape,
    }

    generator = generators.get(tool_name)
    if generator:
        steps = generator(result, context)
        # 모든 step에 usecase 추가
        for step in steps:
            step["usecase"] = usecase
        return steps

    return []


def _generate_next_steps_search(result: dict, context: dict) -> list[dict]:
    """search_news 결과에 대한 next_steps 생성."""
    steps = []
    total = result.get("total_count", 0)
    keyword = context.get("keyword", result.get("keyword", ""))
    start_date = context.get("start_date", "")
    end_date = context.get("end_date", "")

    # 대용량 데이터 (100건 이상): 로컬 저장 필수
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
            "depends_on": [],
            "requires_auth": False,
            "context_hint": "대용량 분석 워크플로우: 로컬 저장 → Python 스크립트 분석",
        })

    # 500건 이상: 타임라인 분석 권장
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
            "depends_on": [],
            "requires_auth": False,
            "context_hint": "심층 리서치: 스파이크 탐지 → 이벤트별 분석",
        })

    # 중간 규모 (20-100건): 샘플링 권장
    if 20 <= total < 100:
        steps.append({
            "priority": "medium",
            "action": "smart_sample",
            "reason": f"{total:,}건에서 대표 샘플 추출",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "sample_size": min(50, total),
                "strategy": "stratified",
            },
            "depends_on": [],
            "requires_auth": False,
            "context_hint": "효율적 분석을 위한 샘플링",
        })

    # 소규모 (100건 미만): 개별 기사 상세 조회
    if 0 < total < 100:
        articles = result.get("articles", [])[:3]
        for i, article in enumerate(articles):
            if article.get("news_id"):
                steps.append({
                    "priority": "medium" if i == 0 else "low",
                    "action": "get_article",
                    "reason": f"'{article.get('title', '')[:30]}...' 상세 조회",
                    "params": {"news_id": article["news_id"]},
                    "depends_on": ["search_news"],
                    "requires_auth": False,
                    "context_hint": "개별 기사 심층 분석",
                })

    # 키워드 트렌드 분석 권장 (로그인 필요)
    if total >= 50 and start_date and end_date:
        steps.append({
            "priority": "low",
            "action": "get_keyword_trends",
            "reason": "시간축 트렌드 시각화",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
            },
            "depends_on": [],
            "requires_auth": True,
            "context_hint": "트렌드 분석: 시계열 그래프",
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
    total_articles = result.get("total_articles", 0)

    if events:
        # 가장 큰 이벤트 심층 분석
        top_event = max(events, key=lambda e: e.get("article_count", e.get("count", 0)))
        period_start, period_end = parse_period_to_dates(top_event["period"])

        steps.append({
            "priority": "high",
            "action": "search_news",
            "reason": f"{top_event['period']} 이벤트 심층 분석 ({top_event.get('article_count', 0):,}건)",
            "params": {
                "keyword": keyword,
                "start_date": period_start,
                "end_date": period_end,
                "page_size": 50,
            },
            "depends_on": ["analyze_timeline"],
            "requires_auth": False,
            "context_hint": "심층 리서치: 피크 기간 집중 분석",
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
                "reason": f"발견된 키워드 간 관계 분석: {', '.join(list(all_keywords)[:3])}",
                "params": {
                    "keywords": list(all_keywords)[:5],
                    "start_date": start_date,
                    "end_date": end_date,
                    "group_by": "month",
                },
                "depends_on": ["analyze_timeline"],
                "requires_auth": False,
                "context_hint": "트렌드 분석: 연관 키워드 비교",
            })

    # 대용량 데이터 수집 권장
    if total_articles >= 1000:
        steps.append({
            "priority": "medium",
            "action": "export_all_articles",
            "reason": f"{total_articles:,}건 전체 데이터 수집",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "output_format": "json",
            },
            "depends_on": [],
            "requires_auth": False,
            "context_hint": "데이터 수집: 전체 기사 로컬 저장",
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
        "depends_on": [],
        "requires_auth": True,
        "context_hint": "심층 리서치: TF-IDF 기반 연관어",
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

    # 가장 인기 있는 키워드 분석
    if comparisons:
        top_keyword = comparisons[0]
        if top_keyword.get("total_count", 0) >= 100:
            steps.append({
                "priority": "high",
                "action": "analyze_timeline",
                "reason": f"'{top_keyword['keyword']}' (1위) 주요 이벤트 파악",
                "params": {
                    "keyword": top_keyword["keyword"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "max_events": 10,
                },
                "depends_on": ["compare_keywords"],
                "requires_auth": False,
                "context_hint": "트렌드 분석: 상위 키워드 심층 분석",
            })

    # 각 키워드별 타임라인 분석 (500건 이상)
    for comp in comparisons[1:3]:
        if comp.get("total_count", 0) >= 500:
            steps.append({
                "priority": "medium",
                "action": "analyze_timeline",
                "reason": f"'{comp['keyword']}' ({comp['rank']}위) 주요 이벤트 파악",
                "params": {
                    "keyword": comp["keyword"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "max_events": 5,
                },
                "depends_on": ["compare_keywords"],
                "requires_auth": False,
                "context_hint": "트렌드 분석: 개별 키워드 분석",
            })

    # 시계열 트렌드 시각화 권장
    keywords = [c["keyword"] for c in comparisons[:3] if c.get("total_count", 0) > 0]
    if len(keywords) >= 2:
        steps.append({
            "priority": "medium",
            "action": "get_keyword_trends",
            "reason": f"시계열 트렌드 비교: {', '.join(keywords)}",
            "params": {
                "keyword": ",".join(keywords),
                "start_date": start_date,
                "end_date": end_date,
            },
            "depends_on": [],
            "requires_auth": True,
            "context_hint": "트렌드 분석: 시계열 그래프 비교",
        })

    return steps


def _generate_next_steps_issues(result: dict, context: dict) -> list[dict]:
    """get_today_issues 결과에 대한 next_steps 생성."""
    steps = []
    results = result.get("results", {})

    for date_key, date_data in results.items():
        top_issues = date_data.get("issues", [])[:2]
        for i, issue in enumerate(top_issues):
            # 관련 기사 검색 (높은 우선순위)
            steps.append({
                "priority": "high" if i == 0 else "medium",
                "action": "search_news",
                "reason": f"'{issue['title']}' 관련 기사 검색 ({issue.get('news_count', 0)}건)",
                "params": {
                    "keyword": issue["title"],
                    "start_date": date_key,
                    "end_date": date_key,
                    "page_size": 20,
                },
                "depends_on": ["get_today_issues"],
                "requires_auth": False,
                "context_hint": "뉴스 모니터링: 오늘 주요 이슈 상세",
            })
            # 이슈 배경 분석 (1년 전부터)
            if i == 0:  # 첫 번째 이슈만 배경 분석
                steps.append({
                    "priority": "low",
                    "action": "analyze_timeline",
                    "reason": f"'{issue['title']}' 이슈 배경 분석 (1년)",
                    "params": {
                        "keyword": issue["title"],
                        "start_date": (
                            f"{int(date_key[:4]) - 1}-{date_key[5:7]}-{date_key[8:10]}"
                            if len(date_key) >= 10 else date_key
                        ),
                        "end_date": date_key,
                        "max_events": 5,
                    },
                    "depends_on": ["get_today_issues"],
                    "requires_auth": False,
                    "context_hint": "심층 리서치: 이슈 발생 배경",
                })

    return steps[:6]  # 최대 6개


def _generate_next_steps_export(result: dict, context: dict) -> list[dict]:
    """export_all_articles 결과에 대한 next_steps 생성."""
    steps = []

    if result.get("success"):
        output_path = result.get("output_path", "")
        keyword = result.get("keyword", "")
        safe_keyword = keyword.replace(" ", "_").replace("/", "_")[:20]
        exported_count = result.get("exported_count", 0)

        # Python 분석 스크립트 실행 안내
        steps.append({
            "priority": "high",
            "action": "execute_code",
            "reason": f"저장된 {exported_count:,}건 데이터로 Python 분석 실행",
            "params": {
                "script_path": f"scripts/analyze_{safe_keyword}.py",
                "data_path": output_path,
            },
            "depends_on": ["export_all_articles"],
            "requires_auth": False,
            "context_hint": "데이터 수집: 분석 코드 실행 안내",
            "instruction": (
                "1. result['analysis_code']를 파일로 저장\n"
                f"2. python scripts/analyze_{safe_keyword}.py 실행"
            ),
        })

        # 타임라인 분석 권장 (아직 안 했다면)
        date_range = result.get("date_range", "")
        if " to " in date_range and exported_count >= 500:
            start_date, end_date = date_range.split(" to ")
            steps.append({
                "priority": "medium",
                "action": "analyze_timeline",
                "reason": f"'{keyword}' 주요 이벤트 파악",
                "params": {
                    "keyword": keyword,
                    "start_date": start_date,
                    "end_date": end_date,
                    "max_events": 10,
                },
                "depends_on": [],
                "requires_auth": False,
                "context_hint": "심층 리서치: 이벤트 탐지",
            })

        # 샘플 기사 상세 조회
        articles = result.get("articles", [])[:2]
        for article in articles:
            if article.get("news_id"):
                steps.append({
                    "priority": "low",
                    "action": "get_article",
                    "reason": f"샘플 기사 '{article.get('title', '')[:20]}...' 상세 확인",
                    "params": {"news_id": article["news_id"]},
                    "depends_on": ["export_all_articles"],
                    "requires_auth": False,
                    "context_hint": "데이터 검증: 샘플 확인",
                })

    return steps


# =============================================================================
# v2.1 신규 도구 next_steps 생성 함수
# =============================================================================


def _generate_next_steps_article(result: dict, context: dict) -> list[dict]:
    """get_article 결과에 대한 next_steps 생성."""
    steps = []

    if result.get("scrape_status") != "success":
        return steps

    title = result.get("title", "")
    publisher = result.get("publisher", "")
    keywords = result.get("keywords", [])
    published_date = result.get("published_date", "")

    # 제목에서 주요 키워드 추출
    if title:
        # 간단한 키워드 추출 (2글자 이상 한글)
        import re
        title_keywords = re.findall(r"[가-힣]{2,}", title)[:3]

        if title_keywords:
            main_keyword = title_keywords[0]
            steps.append({
                "priority": "medium",
                "action": "search_news",
                "reason": f"'{main_keyword}' 관련 기사 검색",
                "params": {
                    "keyword": main_keyword,
                    "start_date": published_date[:10] if published_date else "",
                    "end_date": published_date[:10] if published_date else "",
                    "page_size": 20,
                },
                "depends_on": ["get_article"],
                "requires_auth": False,
                "context_hint": "기사 분석: 관련 기사 탐색",
            })

    # 동일 언론사의 다른 기사 검색
    if publisher and title:
        steps.append({
            "priority": "low",
            "action": "search_news",
            "reason": f"{publisher}의 관련 보도 검색",
            "params": {
                "keyword": title[:20],
                "providers": [publisher],
                "start_date": published_date[:10] if published_date else "",
                "end_date": published_date[:10] if published_date else "",
                "page_size": 10,
            },
            "depends_on": ["get_article"],
            "requires_auth": False,
            "context_hint": "기사 분석: 동일 언론사 보도",
        })

    # 키워드가 있으면 연관어 분석 권장
    if keywords and len(keywords) >= 2:
        steps.append({
            "priority": "low",
            "action": "compare_keywords",
            "reason": f"기사 키워드 비교: {', '.join(keywords[:3])}",
            "params": {
                "keywords": keywords[:5],
                "start_date": published_date[:10] if published_date else "",
                "end_date": published_date[:10] if published_date else "",
            },
            "depends_on": ["get_article"],
            "requires_auth": False,
            "context_hint": "트렌드 분석: 키워드 비교",
        })

    return steps


def _generate_next_steps_article_count(result: dict, context: dict) -> list[dict]:
    """get_article_count 결과에 대한 next_steps 생성."""
    steps = []

    if not result.get("success"):
        return steps

    keyword = result.get("keyword", "")
    total_count = result.get("total_count", 0)
    date_range = result.get("date_range", "")
    counts = result.get("counts", [])

    if " to " in date_range:
        start_date, end_date = date_range.split(" to ")
    else:
        start_date = context.get("start_date", "")
        end_date = context.get("end_date", "")

    # 대용량 데이터: 타임라인 분석 권장
    if total_count >= 500:
        steps.append({
            "priority": "high",
            "action": "analyze_timeline",
            "reason": f"{total_count:,}건 데이터의 시간별 주요 이벤트 파악",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "max_events": 10,
            },
            "depends_on": ["get_article_count"],
            "requires_auth": False,
            "context_hint": "심층 리서치: 스파이크 탐지",
        })

    # 기사 수 데이터가 있으면 피크 기간 검색 권장
    if counts:
        # 가장 많은 기간 찾기
        peak = max(counts, key=lambda x: x.get("count", 0))
        if peak.get("count", 0) > 0:
            peak_date = peak.get("date", "")
            # 월별/주별 기간인 경우 처리
            if "month_start" in peak:
                peak_start = peak["month_start"]
                peak_end = peak["month_end"]
            elif "week_start" in peak:
                peak_start = peak["week_start"]
                peak_end = peak["week_end"]
            else:
                peak_start = peak_date
                peak_end = peak_date

            steps.append({
                "priority": "medium",
                "action": "search_news",
                "reason": f"피크 기간({peak_date}) 기사 검색 ({peak.get('count', 0)}건)",
                "params": {
                    "keyword": keyword,
                    "start_date": peak_start,
                    "end_date": peak_end,
                    "page_size": 50,
                },
                "depends_on": ["get_article_count"],
                "requires_auth": False,
                "context_hint": "트렌드 분석: 피크 기간 집중",
            })

    # 시계열 트렌드 시각화 권장
    if total_count >= 50:
        steps.append({
            "priority": "low",
            "action": "get_keyword_trends",
            "reason": "시계열 트렌드 시각화",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
            },
            "depends_on": [],
            "requires_auth": True,
            "context_hint": "트렌드 분석: 시계열 그래프",
        })

    return steps


def _generate_next_steps_trends(result: dict, context: dict) -> list[dict]:
    """get_keyword_trends 결과에 대한 next_steps 생성."""
    steps = []

    if not result.get("success"):
        return steps

    keyword = result.get("keyword", "")
    trends = result.get("trends", [])
    date_range = result.get("date_range", "")

    if " to " in date_range:
        start_date, end_date = date_range.split(" to ")
    else:
        start_date = context.get("start_date", "")
        end_date = context.get("end_date", "")

    # 트렌드에서 피크 찾기
    for trend in trends[:2]:
        data = trend.get("data", [])
        if data:
            # 가장 높은 데이터 포인트 찾기
            peak = max(data, key=lambda x: x.get("count", 0))
            if peak.get("count", 0) > 0:
                peak_date = peak.get("date", "")
                steps.append({
                    "priority": "high",
                    "action": "search_news",
                    "reason": f"'{trend.get('keyword', keyword)}' 피크 시점({peak_date}) 기사 검색",
                    "params": {
                        "keyword": trend.get("keyword", keyword),
                        "start_date": peak_date,
                        "end_date": peak_date,
                        "page_size": 50,
                    },
                    "depends_on": ["get_keyword_trends"],
                    "requires_auth": False,
                    "context_hint": "트렌드 분석: 피크 시점 심층 분석",
                })

    # 여러 키워드인 경우 비교 분석 권장
    if len(trends) >= 2:
        keywords = [t.get("keyword") for t in trends[:5] if t.get("keyword")]
        steps.append({
            "priority": "medium",
            "action": "compare_keywords",
            "reason": f"키워드 비교 분석: {', '.join(keywords[:3])}",
            "params": {
                "keywords": keywords,
                "start_date": start_date,
                "end_date": end_date,
                "group_by": "month",
            },
            "depends_on": ["get_keyword_trends"],
            "requires_auth": False,
            "context_hint": "트렌드 분석: 키워드 비교",
        })

    return steps


def _generate_next_steps_related(result: dict, context: dict) -> list[dict]:
    """get_related_keywords 결과에 대한 next_steps 생성."""
    steps = []

    if not result.get("success"):
        return steps

    keyword = result.get("keyword", "")
    top_words = result.get("top_words", [])
    date_range = result.get("date_range", "")

    if " to " in date_range:
        start_date, end_date = date_range.split(" to ")
    else:
        start_date = context.get("start_date", "")
        end_date = context.get("end_date", "")

    # 상위 연관어로 비교 분석
    if len(top_words) >= 3:
        related_keywords = [w.get("name") for w in top_words[:5] if w.get("name")]
        steps.append({
            "priority": "high",
            "action": "compare_keywords",
            "reason": f"연관어 비교 분석: {', '.join(related_keywords[:3])}",
            "params": {
                "keywords": related_keywords,
                "start_date": start_date,
                "end_date": end_date,
                "group_by": "month",
            },
            "depends_on": ["get_related_keywords"],
            "requires_auth": False,
            "context_hint": "심층 리서치: 연관어 네트워크 확장",
        })

    # 가장 관련 높은 키워드로 검색
    if top_words:
        top_related = top_words[0].get("name", "")
        if top_related and top_related != keyword:
            steps.append({
                "priority": "medium",
                "action": "search_news",
                "reason": f"최상위 연관어 '{top_related}' 기사 검색",
                "params": {
                    "keyword": f"{keyword} {top_related}",
                    "start_date": start_date,
                    "end_date": end_date,
                    "page_size": 30,
                },
                "depends_on": ["get_related_keywords"],
                "requires_auth": False,
                "context_hint": "심층 리서치: 연관 키워드 조합 검색",
            })

    # 타임라인 분석 권장
    steps.append({
        "priority": "low",
        "action": "analyze_timeline",
        "reason": f"'{keyword}' 주요 이벤트 파악",
        "params": {
            "keyword": keyword,
            "start_date": start_date,
            "end_date": end_date,
            "max_events": 10,
        },
        "depends_on": [],
        "requires_auth": False,
        "context_hint": "심층 리서치: 이벤트 탐지",
    })

    return steps


def _generate_next_steps_sample(result: dict, context: dict) -> list[dict]:
    """smart_sample 결과에 대한 next_steps 생성."""
    steps = []

    if not result.get("success"):
        return steps

    keyword = result.get("keyword", "")
    total_count = result.get("total_count", 0)
    sample_size = result.get("sample_size", 0)
    articles = result.get("articles", [])
    date_range = result.get("date_range", "")

    if " to " in date_range:
        start_date, end_date = date_range.split(" to ")
    else:
        start_date = context.get("start_date", "")
        end_date = context.get("end_date", "")

    # 전체 데이터 내보내기 권장
    if total_count >= 100:
        steps.append({
            "priority": "high",
            "action": "export_all_articles",
            "reason": f"전체 {total_count:,}건 로컬 저장 (샘플: {sample_size}건)",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "output_format": "json",
            },
            "depends_on": [],
            "requires_auth": False,
            "context_hint": "데이터 수집: 전체 기사 저장",
        })

    # 샘플 기사 상세 조회
    for i, article in enumerate(articles[:3]):
        if article.get("news_id"):
            steps.append({
                "priority": "medium" if i == 0 else "low",
                "action": "get_article",
                "reason": f"샘플 기사 '{article.get('title', '')[:25]}...' 상세 조회",
                "params": {"news_id": article["news_id"]},
                "depends_on": ["smart_sample"],
                "requires_auth": False,
                "context_hint": "데이터 검증: 샘플 확인",
            })

    # 타임라인 분석 권장
    if total_count >= 500:
        steps.append({
            "priority": "medium",
            "action": "analyze_timeline",
            "reason": f"{total_count:,}건 데이터의 주요 이벤트 파악",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "max_events": 10,
            },
            "depends_on": [],
            "requires_auth": False,
            "context_hint": "심층 리서치: 이벤트 탐지",
        })

    return steps


def _generate_next_steps_scrape(result: dict, context: dict) -> list[dict]:
    """scrape_article_url 결과에 대한 next_steps 생성."""
    steps = []

    if not result.get("success"):
        return steps

    title = result.get("title", "")
    publisher = result.get("publisher", "")
    keywords = result.get("keywords", [])
    published_date = result.get("published_date", "")

    # 제목에서 주요 키워드 추출
    if title:
        import re
        title_keywords = re.findall(r"[가-힣]{2,}", title)[:3]

        if title_keywords:
            main_keyword = title_keywords[0]
            steps.append({
                "priority": "medium",
                "action": "search_news",
                "reason": f"'{main_keyword}' 관련 기사 검색",
                "params": {
                    "keyword": main_keyword,
                    "start_date": published_date[:10] if published_date else "",
                    "end_date": published_date[:10] if published_date else "",
                    "page_size": 20,
                },
                "depends_on": ["scrape_article_url"],
                "requires_auth": False,
                "context_hint": "기사 분석: 관련 기사 탐색",
            })

    # 동일 언론사 검색
    if publisher and title:
        steps.append({
            "priority": "low",
            "action": "search_news",
            "reason": f"{publisher}의 관련 보도 검색",
            "params": {
                "keyword": title[:20],
                "providers": [publisher],
                "start_date": published_date[:10] if published_date else "",
                "end_date": published_date[:10] if published_date else "",
                "page_size": 10,
            },
            "depends_on": ["scrape_article_url"],
            "requires_auth": False,
            "context_hint": "기사 분석: 동일 언론사 보도",
        })

    return steps
