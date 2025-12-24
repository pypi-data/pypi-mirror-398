"""뉴스 분석용 MCP Prompts."""

from __future__ import annotations


def news_analysis_prompt(
    keyword: str,
    start_date: str,
    end_date: str,
    analysis_type: str = "summary",
) -> str:
    """
    뉴스 분석을 위한 프롬프트를 생성합니다.

    Args:
        keyword: 분석할 키워드
        start_date: 분석 시작일 (YYYY-MM-DD)
        end_date: 분석 종료일 (YYYY-MM-DD)
        analysis_type: 분석 유형
            - summary: 주요 내용 요약
            - sentiment: 감성 분석
            - trend: 트렌드 분석
            - comparison: 언론사별 보도 비교

    Returns:
        분석 프롬프트
    """
    analysis_instructions = {
        "summary": """
## 분석 지침: 주요 내용 요약
1. 핵심 이슈 3-5개를 식별하세요.
2. 각 이슈별로 주요 내용을 2-3문장으로 요약하세요.
3. 전체적인 동향을 한 문단으로 정리하세요.
""",
        "sentiment": """
## 분석 지침: 감성 분석
1. 기사들의 전반적인 논조(긍정/중립/부정)를 파악하세요.
2. 긍정적/부정적 보도의 비율을 추정하세요.
3. 주요 긍정/부정 키워드를 추출하세요.
4. 시간에 따른 감성 변화가 있다면 분석하세요.
""",
        "trend": """
## 분석 지침: 트렌드 분석
1. 기사 수의 시간별 추이를 파악하세요.
2. 주요 이벤트와 기사 수 증가의 상관관계를 분석하세요.
3. 새롭게 등장한 관련 키워드나 주제를 식별하세요.
4. 향후 예상되는 트렌드를 제시하세요.
""",
        "comparison": """
## 분석 지침: 언론사별 보도 비교
1. 언론사별 보도 건수와 비중을 파악하세요.
2. 언론사별 보도 논조의 차이점을 분석하세요.
3. 동일 사안에 대한 프레이밍 차이를 비교하세요.
4. 보도의 다양성과 균형성을 평가하세요.
""",
    }

    instruction = analysis_instructions.get(analysis_type, analysis_instructions["summary"])

    return f"""# 뉴스 분석 요청

## 분석 대상
- **키워드**: {keyword}
- **기간**: {start_date} ~ {end_date}
- **분석 유형**: {analysis_type}

## 진행 단계

### 1단계: 데이터 수집
먼저 `search_news` 도구로 관련 기사를 검색하세요:
```
search_news(
    keyword="{keyword}",
    start_date="{start_date}",
    end_date="{end_date}",
    page_size=50,
    sort_by="both"
)
```

### 2단계: 기사 수 확인
전체 기사 수와 트렌드를 파악하세요:
```
get_article_count(
    keyword="{keyword}",
    start_date="{start_date}",
    end_date="{end_date}"
)
```

### 3단계: 상세 분석
주요 기사 3-5개를 선별하여 상세 내용을 조회하세요:
```
get_article(news_id="...", include_full_content=True)
```

### 4단계: 분석 수행
{instruction}

## 결과 형식
분석 결과를 다음 형식으로 정리해주세요:

### 개요
(1-2문장의 전체 요약)

### 주요 발견
1. ...
2. ...
3. ...

### 상세 분석
(분석 유형에 따른 상세 내용)

### 결론 및 시사점
(핵심 인사이트 정리)
"""


def trend_report_prompt(
    keyword: str,
    days: int = 7,
) -> str:
    """
    트렌드 리포트 생성을 위한 프롬프트를 생성합니다.

    Args:
        keyword: 분석할 키워드
        days: 분석 기간 (일 단위, 기본 7일)

    Returns:
        트렌드 리포트 프롬프트
    """
    return f"""# 트렌드 리포트 생성

## 분석 대상
- **키워드**: {keyword}
- **기간**: 최근 {days}일

## 진행 단계

### 1단계: 현재 날짜 확인
먼저 한국 시간 기준 현재 날짜를 확인하세요:
```
get_current_korean_time()
```

### 2단계: 오늘의 이슈 확인
오늘의 주요 이슈를 확인하세요:
```
get_today_issues()
```

### 3단계: 키워드 검색
지정된 키워드로 최근 기사를 검색하세요:
```
search_news(
    keyword="{keyword}",
    start_date="(현재 날짜에서 {days}일 전)",
    end_date="(현재 날짜)",
    sort_by="date",
    page_size=30
)
```

### 4단계: 기사 수 트렌드 분석
```
get_article_count(
    keyword="{keyword}",
    start_date="(현재 날짜에서 {days}일 전)",
    end_date="(현재 날짜)"
)
```

### 5단계: 주요 기사 분석
가장 최신 또는 중요한 기사 3개를 상세 조회하세요.

## 리포트 형식

### {keyword} 트렌드 리포트

**생성일**: (현재 날짜)
**분석 기간**: 최근 {days}일

#### 1. 핵심 요약
(3줄 이내의 핵심 내용)

#### 2. 주요 수치
- 총 기사 수: N건
- 일평균 기사 수: N건
- 최다 보도일: YYYY-MM-DD (N건)

#### 3. 주요 이슈 Top 5
1. ...
2. ...
3. ...
4. ...
5. ...

#### 4. 언론사별 보도 현황
(주요 언론사의 보도 동향)

#### 5. 향후 전망
(예상되는 트렌드 또는 주목할 포인트)
"""


def issue_briefing_prompt(date: str | None = None) -> str:
    """
    일일 이슈 브리핑을 위한 프롬프트를 생성합니다.

    Args:
        date: 브리핑 날짜 (YYYY-MM-DD). None이면 오늘

    Returns:
        이슈 브리핑 프롬프트
    """
    date_instruction = f'date="{date}"' if date else ""

    return f"""# 일일 이슈 브리핑

## 분석 대상
- **날짜**: {date if date else "오늘"}

## 진행 단계

### 1단계: 날짜 확인
현재 한국 시간을 확인하세요:
```
get_current_korean_time()
```

### 2단계: 인기 이슈 조회
오늘/지정일의 인기 이슈를 조회하세요:
```
get_today_issues({date_instruction})
```

### 3단계: 주요 이슈별 상세 검색
상위 5개 이슈에 대해 각각 상세 검색하세요:
```
search_news(keyword="(이슈 키워드)", start_date="...", end_date="...", page_size=10)
```

### 4단계: 대표 기사 조회
각 이슈별로 가장 중요한 기사 1개씩 상세 조회하세요.

## 브리핑 형식

### 일일 이슈 브리핑

**날짜**: {date if date else "(오늘 날짜)"}

---

#### TOP 1: (이슈 제목)
- **보도량**: N건
- **핵심 내용**: (2-3문장)
- **주요 언론사**: ...

#### TOP 2: (이슈 제목)
- **보도량**: N건
- **핵심 내용**: (2-3문장)
- **주요 언론사**: ...

(... TOP 5까지 반복 ...)

---

### 오늘의 한 줄 요약
(가장 중요한 이슈 한 문장으로 요약)
"""


def large_scale_analysis_prompt(
    keyword: str,
    start_date: str,
    end_date: str,
    analysis_goal: str = "general",
) -> str:
    """
    대용량 데이터 분석을 위한 워크플로우 프롬프트.

    100건 이상의 기사를 분석할 때 사용합니다.
    컨텍스트 윈도우 제한을 우회하여 정확한 분석을 수행합니다.

    Args:
        keyword: 분석할 키워드
        start_date: 분석 시작일 (YYYY-MM-DD)
        end_date: 분석 종료일 (YYYY-MM-DD)
        analysis_goal: 분석 목표
            - general: 일반 분석 (언론사별, 시간대별, 키워드 빈도)
            - tone: 논조 분석 (긍정/부정/중립)
            - comparison: 언론사별 보도 비교
            - timeline: 시계열 트렌드 분석

    Returns:
        대용량 분석 워크플로우 프롬프트
    """
    analysis_goals = {
        "general": "언론사별 분포, 시간대별 추이, 주요 키워드 추출",
        "tone": "긍정/부정/중립 논조 분류, 스캔들 언급 여부, 감성 키워드 분석",
        "comparison": "언론사별 보도 프레이밍 비교, 헤드라인 차이 분석",
        "timeline": "시간대별 보도량 변화, 이벤트-보도 상관관계 분석",
    }

    goal_description = analysis_goals.get(analysis_goal, analysis_goals["general"])

    return f"""# 대용량 뉴스 데이터 분석 워크플로우

## 분석 개요
- **키워드**: {keyword}
- **기간**: {start_date} ~ {end_date}
- **분석 목표**: {goal_description}

## ⚠️ 중요: 대용량 분석 원칙

컨텍스트 윈도우 제한으로 100건 이상의 기사는 직접 분석할 수 없습니다.
**반드시 아래 워크플로우를 따르세요.**

---

## Step 1: 데이터 규모 확인

먼저 검색 결과 수를 확인합니다:

```
search_news(
    keyword="{keyword}",
    start_date="{start_date}",
    end_date="{end_date}",
    page_size=1
)
```

`total_count`를 확인하세요:
- **< 20건**: 직접 분석 가능 → Step 5로 이동
- **20-100건**: `smart_sample` 사용 권장 → Step 3으로 이동
- **> 100건**: `export_all_articles` 필수 → Step 2로 이동

---

## Step 2: 로컬 파일로 내보내기 (100건 이상)

대용량 데이터를 로컬 파일로 저장합니다:

```
export_all_articles(
    keyword="{keyword}",
    start_date="{start_date}",
    end_date="{end_date}",
    output_format="json",
    output_path="data/{keyword.replace(' ', '_')}_articles.json",
    max_articles=10000
)
```

**반환값에서 확인할 것:**
- `output_path`: 저장된 파일 경로
- `exported_count`: 실제 저장된 기사 수
- `analysis_code`: Python 분석 코드 템플릿

---

## Step 3: 분석 코드 저장

반환된 `analysis_code`를 파일로 저장합니다:

**파일명**: `scripts/analyze_{keyword.replace(' ', '_')}.py`

분석 목표({analysis_goal})에 맞게 코드를 수정하세요:

### {goal_description}을 위한 추가 코드 예시:

```python
# 논조 분석 (tone)
def analyze_tone(articles):
    positive_keywords = ["성공", "기대", "호평", "인기"]
    negative_keywords = ["논란", "비판", "스캔들", "실패"]

    for article in articles:
        content = article.get("title", "") + " " + article.get("summary", "")
        pos_count = sum(1 for kw in positive_keywords if kw in content)
        neg_count = sum(1 for kw in negative_keywords if kw in content)
        article["tone"] = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"

# 언론사별 비교 (comparison)
def compare_publishers(articles):
    from collections import defaultdict
    by_publisher = defaultdict(list)
    for a in articles:
        by_publisher[a.get("publisher", "Unknown")].append(a)

    for pub, arts in sorted(by_publisher.items(), key=lambda x: -len(x[1])):
        print(f"{{pub}}: {{len(arts)}}건")
```

---

## Step 4: 분석 실행 안내

사용자에게 다음 명령어 실행을 안내합니다:

```bash
python scripts/analyze_{keyword.replace(' ', '_')}.py
```

또는

```bash
uv run python scripts/analyze_{keyword.replace(' ', '_')}.py
```

---

## Step 5: 결과 해석 및 보고 (선택)

분석 결과를 바탕으로 인사이트를 정리합니다.

### 보고서 형식:

#### 1. 분석 개요
- 키워드: {keyword}
- 기간: {start_date} ~ {end_date}
- 분석 기사 수: N건

#### 2. 주요 발견
- (언론사별 분포 요약)
- (시간대별 추이 요약)
- (주요 키워드 요약)

#### 3. 상세 분석 결과
(분석 목표에 따른 세부 결과)

#### 4. 결론 및 시사점
(핵심 인사이트)

---

## 요약: 워크플로우 체크리스트

□ Step 1: 데이터 규모 확인 (`search_news`)
□ Step 2: 로컬 파일 저장 (`export_all_articles`)
□ Step 3: 분석 코드 저장 (반환된 `analysis_code` 사용)
□ Step 4: 실행 명령어 안내
□ Step 5: 결과 해석 및 보고
"""
