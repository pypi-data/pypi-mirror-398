# Agentic Pipeline Design

> **Version**: 2.1 (2025-12-21)
> **Status**: Production

## 개요

BigKinds MCP 도구들을 유기적으로 연결하여 LLM이 자율적으로 분석 워크플로우를 수행할 수 있게 합니다.

## 핵심 원칙

### 1. Context-Aware Next Steps
도구 결과에 따라 동적으로 다음 단계 제안

### 2. Actionable Suggestions
실제 호출 가능한 파라미터 포함

### 3. Threshold-Based Branching
결과 크기에 따른 분기 (100건 이상 → 로컬 저장 권장)

### 4. Quarterly Guarantee
스파이크가 없어도 분기당 최소 1개 이벤트 보장

### 5. Usecase-Driven (v2.1 신규)
유즈케이스별 최적화된 next_steps 제안

---

## 지원 유즈케이스 (v2.1)

| 유즈케이스 | 설명 | 주요 진입점 |
|-----------|------|------------|
| `news_monitoring` | 실시간 뉴스 추적 | `get_today_issues`, 당일 검색 |
| `deep_research` | 인물/사건 심층 분석 | `analyze_timeline`, 장기간 검색 |
| `trend_analysis` | 트렌드/비교 분석 | `compare_keywords`, `get_keyword_trends` |
| `data_collection` | 대용량 수집 | 100건+, `export_all_articles` |
| `article_detail` | 개별 기사 분석 | `get_article`, `scrape_article_url` |

---

## next_steps 스키마 (v2.1)

```python
{
    "usecase": "deep_research",        # 감지된 유즈케이스
    "priority": "high",                # high/medium/low
    "action": "analyze_timeline",      # 도구 이름
    "reason": "장기간 데이터의 시간별 주요 이벤트 파악",
    "params": {                        # 호출 파라미터
        "keyword": "한동훈",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    },
    "depends_on": ["search_news"],     # 선행 도구 (v2.1)
    "requires_auth": False,            # 로그인 필요 여부
    "context_hint": "타임라인으로 주요 사건 파악 → 스파이크 기간 심층 분석"
}

---

## 도구 연결 맵

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ENTRY POINTS                                    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │get_today_    │  │search_news   │  │analyze_      │  │compare_      │     │
│  │issues        │  │              │  │timeline      │  │keywords      │     │
│  │"오늘 이슈"   │  │"검색"        │  │"분석"        │  │"비교"        │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │                 │              │
└─────────┼─────────────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DEEP DIVE LAYER                                 │
│                                                                              │
│  search_news (N건) ─────┬──────────────────────────────────────────────────  │
│                         │                                                    │
│    N < 100:             │    N >= 100:                                       │
│    • get_article()      │    • export_all_articles() [필수]                  │
│    • analyze_timeline() │    • smart_sample()                                │
│                         │    • analyze_timeline()                            │
│                                                                              │
│  analyze_timeline ──────┬──────────────────────────────────────────────────  │
│                         │                                                    │
│    • search_news(이벤트 기간) - 특정 이벤트 심층 분석                        │
│    • get_related_keywords() - 연관어 네트워크 확장                           │
│    • compare_keywords(관련 인물/키워드) - 비교 분석                          │
│    • export_all_articles() - 대량 데이터 수집                                │
│                                                                              │
│  compare_keywords ──────┬──────────────────────────────────────────────────  │
│                         │                                                    │
│    • analyze_timeline(각 키워드) - 개별 타임라인                             │
│    • get_keyword_trends() - 트렌드 시각화 (로그인 필요)                      │
│                                                                              │
│  get_today_issues ──────┬──────────────────────────────────────────────────  │
│                         │                                                    │
│    • search_news(이슈 키워드) - 관련 기사 검색                               │
│    • analyze_timeline(이슈 키워드) - 이슈 배경 분석                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARTICLE DETAIL LAYER                               │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │get_article   │  │scrape_       │  │export_all_   │                       │
│  │(BigKinds)    │  │article_url   │  │articles      │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
│                                                                              │
│  → 로컬 Python 분석 스크립트 실행                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ADVANCED ANALYSIS (로그인 필요)                      │
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │get_keyword_trends    │  │get_related_keywords  │                         │
│  │(시계열 트렌드)       │  │(연관어 분석)         │                         │
│  └──────────────────────┘  └──────────────────────┘                         │
│                                                                              │
│  → 추가 키워드 발견 시 다시 Entry Points로 순환                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## next_steps 생성 규칙

### 1. search_news

```python
def generate_next_steps_for_search(result, keyword, start_date, end_date):
    total = result["total_count"]
    steps = []

    if total >= 100:
        # 대용량 데이터 - 로컬 저장 필수
        steps.append({
            "priority": "high",
            "action": "export_all_articles",
            "reason": f"{total:,}건은 컨텍스트 제한 초과. 로컬 저장 후 분석 필수",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "output_format": "json"
            }
        })

    if total >= 1000:
        # 타임라인 분석 권장
        steps.append({
            "priority": "high",
            "action": "analyze_timeline",
            "reason": "대용량 데이터의 시간별 주요 이벤트 파악",
            "params": {
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "max_events": 10
            }
        })

    if total > 0 and total < 100:
        # 개별 기사 상세 조회 가능
        top_articles = result["articles"][:3]
        for article in top_articles:
            steps.append({
                "priority": "medium",
                "action": "get_article",
                "reason": "주요 기사 상세 내용 확인",
                "params": {"news_id": article["news_id"]}
            })

    return steps
```

### 2. analyze_timeline

```python
def generate_next_steps_for_timeline(result, keyword):
    steps = []
    events = result.get("events", [])

    if events:
        # 가장 큰 이벤트 심층 분석
        top_event = max(events, key=lambda e: e["article_count"])
        period_start, period_end = parse_period_to_dates(top_event["period"])

        steps.append({
            "priority": "high",
            "action": "search_news",
            "reason": f"{top_event['period']} 이벤트 심층 분석 ({top_event['article_count']:,}건)",
            "params": {
                "keyword": keyword,
                "start_date": period_start,
                "end_date": period_end,
                "page_size": 50
            }
        })

        # 이벤트에서 발견된 키워드로 비교 분석
        all_keywords = set()
        for event in events[:3]:
            all_keywords.update(event.get("top_keywords", [])[:2])

        if len(all_keywords) >= 2:
            steps.append({
                "priority": "medium",
                "action": "compare_keywords",
                "reason": "발견된 키워드 간 관계 분석",
                "params": {
                    "keywords": list(all_keywords)[:5],
                    "start_date": result["period"]["start_date"],
                    "end_date": result["period"]["end_date"],
                    "group_by": "month"
                }
            })

    # 연관어 분석 (로그인 필요)
    steps.append({
        "priority": "low",
        "action": "get_related_keywords",
        "reason": "연관어 네트워크로 숨겨진 연결고리 발견",
        "params": {
            "keyword": keyword,
            "start_date": result["period"]["start_date"],
            "end_date": result["period"]["end_date"]
        },
        "requires_auth": True
    })

    return steps
```

### 3. compare_keywords

```python
def generate_next_steps_for_compare(result):
    steps = []
    comparisons = result.get("comparisons", [])

    # 각 키워드별 타임라인 분석
    for comp in comparisons[:3]:
        if comp["total_count"] >= 1000:
            steps.append({
                "priority": "medium",
                "action": "analyze_timeline",
                "reason": f"'{comp['keyword']}' 주요 이벤트 파악",
                "params": {
                    "keyword": comp["keyword"],
                    "start_date": result["date_range"].split(" to ")[0],
                    "end_date": result["date_range"].split(" to ")[1]
                }
            })

    return steps
```

### 4. get_today_issues

```python
def generate_next_steps_for_issues(result):
    steps = []

    for date_key, date_data in result.get("results", {}).items():
        top_issues = date_data.get("issues", [])[:3]
        for issue in top_issues:
            steps.append({
                "priority": "medium",
                "action": "search_news",
                "reason": f"'{issue['title']}' 관련 기사 검색",
                "params": {
                    "keyword": issue["title"],
                    "start_date": date_key,
                    "end_date": date_key
                }
            })

    return steps
```

---

## 분기별 필수 추출 로직

### 현재 문제
스파이크(평균의 1.5배 이상)만 탐지하면 조용한 시기의 이벤트를 놓침

### 해결책
분기별로 최소 1개 이벤트 보장

```python
def ensure_quarterly_events(
    monthly_counts: dict[str, int],
    spikes: dict[str, dict],
    max_events: int
) -> list[dict]:
    """분기별 최소 1개 이벤트 보장."""

    # 분기별 그룹화
    quarters = {}  # {"2024-Q1": [("2024-01", 100), ...], ...}
    for period, count in monthly_counts.items():
        year, month = period.split("-")
        quarter = f"{year}-Q{(int(month) - 1) // 3 + 1}"
        if quarter not in quarters:
            quarters[quarter] = []
        quarters[quarter].append((period, count))

    events = []

    for quarter in sorted(quarters.keys()):
        months = quarters[quarter]

        # 1. 해당 분기에 스파이크가 있으면 사용
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
                "type": "spike",
                **best[1]
            })
        else:
            # 2. 스파이크 없으면 해당 분기에서 가장 기사 많은 월 선택
            best_month = max(months, key=lambda x: x[1])
            avg = sum(c for _, c in months) / len(months)
            events.append({
                "period": best_month[0],
                "type": "quarterly_peak",  # 분기 대표
                "count": best_month[1],
                "ratio": round(best_month[1] / avg, 2) if avg > 0 else 1.0,
                "average": round(avg, 1)
            })

    # max_events 제한
    if len(events) > max_events:
        # 스파이크 우선, 그 다음 기사 수 순
        events.sort(key=lambda x: (x["type"] != "spike", -x["count"]))
        events = events[:max_events]
        events.sort(key=lambda x: x["period"])  # 시간순 정렬

    return events
```

---

## NLP 키워드 추출 개선 (kiwipiepy)

### 현재 방식
```python
# 정규식으로 한글 2글자 이상 추출
matches = re.findall(r"[가-힣]{2,}", title)
```

### 개선된 방식 (kiwipiepy)
```python
from kiwipiepy import Kiwi

kiwi = Kiwi()

def extract_keywords_nlp(
    titles: list[str],
    top_n: int = 5,
    exclude_words: set[str] | None = None,
    pos_filter: set[str] = {"NNP", "NNG", "VV", "VA"}  # 고유명사, 일반명사, 동사, 형용사
) -> list[dict]:
    """형태소 분석 기반 키워드 추출.

    Returns:
        [{"word": "한동훈", "pos": "NNP", "count": 45}, ...]
    """
    if not titles:
        return []

    word_counts = Counter()
    word_pos = {}  # 단어별 품사 저장

    for title in titles:
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
            if exclude_words and word in exclude_words:
                continue

            word_counts[word] += 1
            word_pos[word] = pos

    # 상위 N개 반환
    result = []
    for word, count in word_counts.most_common(top_n):
        result.append({
            "word": word,
            "pos": word_pos[word],
            "pos_label": POS_LABELS.get(word_pos[word], "기타"),
            "count": count
        })

    return result


POS_LABELS = {
    "NNP": "고유명사",
    "NNG": "일반명사",
    "VV": "동사",
    "VA": "형용사",
    "NNB": "의존명사",
}
```

---

## 구현 상태

### Phase 1: 핵심 기능 ✅ 완료
1. [x] kiwipiepy 의존성 추가
2. [x] `extract_keywords_nlp` 함수 구현
3. [x] 분기별 필수 추출 로직 (`ensure_quarterly_events`)
4. [x] `analyze_timeline`에 통합

### Phase 2: 파이프라인 연결 ✅ 완료 (v2.0)
5. [x] `timeline_utils.py`에 통합 (파이프라인 모듈)
6. [x] `generate_next_steps` 함수들 구현
7. [x] 핵심 도구에 `next_steps` 필드 추가 (5개)

### Phase 3: 전체 도구 커버리지 ✅ 완료 (v2.1)
8. [x] 유즈케이스 타입 정의 (`UsecaseType`)
9. [x] `detect_usecase()` 함수 구현
10. [x] 스키마 확장 (`depends_on`, `requires_auth`, `context_hint`)
11. [x] **전체 11개 도구에 next_steps 통합**
    - search_news, get_article_count, analyze_timeline
    - compare_keywords, get_today_issues, export_all_articles
    - get_article, scrape_article_url (신규)
    - get_keyword_trends, get_related_keywords (신규)
    - smart_sample (신규)

### Phase 4: 테스트 및 배포
12. [ ] 단위 테스트 작성
13. [ ] 통합 테스트
14. [ ] 버전 업데이트 (v2.1.0) 및 배포

---

## 예상 결과

### Before
```json
{
  "success": true,
  "keyword": "한동훈",
  "events": [
    {"period": "2024-12", "article_count": 17199, ...}
  ]
}
```

### After
```json
{
  "success": true,
  "keyword": "한동훈",
  "events": [
    {
      "period": "2024-03",
      "type": "quarterly_peak",
      "article_count": 14076,
      "top_keywords": [
        {"word": "총선", "pos": "NNG", "count": 89},
        {"word": "대통령", "pos": "NNG", "count": 67},
        {"word": "조국", "pos": "NNP", "count": 45}
      ]
    },
    {
      "period": "2024-12",
      "type": "spike",
      "article_count": 17199,
      "top_keywords": [
        {"word": "비상계엄", "pos": "NNG", "count": 234},
        {"word": "탄핵", "pos": "NNG", "count": 189}
      ]
    }
  ],
  "next_steps": [
    {
      "priority": "high",
      "action": "search_news",
      "reason": "2024-12 이벤트 심층 분석 (17,199건)",
      "params": {
        "keyword": "한동훈",
        "start_date": "2024-12-01",
        "end_date": "2024-12-31"
      }
    },
    {
      "priority": "medium",
      "action": "compare_keywords",
      "reason": "발견된 키워드 간 관계 분석",
      "params": {
        "keywords": ["비상계엄", "탄핵", "총선"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
      }
    }
  ]
}
```
