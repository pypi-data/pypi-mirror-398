# BigKinds 시각화 MCP Tools

BigKinds MCP 서버에 추가된 시각화 분석 도구들입니다.

## 개요

BigKinds의 시각화 API를 활용하여 뉴스 데이터를 다양한 방식으로 분석할 수 있습니다:

1. **키워드 트렌드**: 시간 경과에 따른 키워드 언급 빈도 추이
2. **연관어 분석**: TF-IDF 기반 연관 키워드 추출
3. **네트워크 분석**: 개체(인물, 기관, 장소) 간 관계 그래프

## 인증 요구사항

모든 시각화 API는 **로그인이 필수**입니다.

### 환경변수 설정

`.env` 파일에 BigKinds 계정 정보를 설정하세요:

```env
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password
```

### 자동 로그인

- MCP 서버가 시작되면 자동으로 로그인을 시도합니다
- 세션이 만료되면 자동으로 재로그인합니다
- 로그인 실패 시 에러 메시지를 반환합니다

## Tools

### 1. get_keyword_trends

키워드별 기사 수 추이를 시간축 그래프로 분석합니다.

#### 파라미터

```python
keyword: str                    # 검색 키워드 (콤마로 구분하여 여러 키워드 가능)
start_date: str                 # 시작일 (YYYY-MM-DD)
end_date: str                   # 종료일 (YYYY-MM-DD)
interval: int = 1               # 시간 단위 (1:일간, 2:주간, 3:월간, 4:연간)
providers: list[str] | None     # 언론사 필터
categories: list[str] | None    # 카테고리 필터
```

#### 반환값

```python
{
    "success": bool,
    "keyword": str,
    "date_range": str,
    "interval": int,
    "interval_name": str,           # "일간", "주간", "월간", "연간"
    "trends": [
        {
            "keyword": str,
            "data": [
                {
                    "date": str,    # YYYY-MM-DD
                    "count": int    # 기사 수
                }
            ],
            "total_count": int      # 전체 기사 수 합계
        }
    ],
    "total_keywords": int,
    "total_data_points": int,
    "summary": {
        "keywords_analyzed": [str],
        "total_articles_sum": int
    }
}
```

#### 사용 예시

```python
# 단일 키워드, 일간 트렌드
result = await get_keyword_trends(
    keyword="AI",
    start_date="2024-12-01",
    end_date="2024-12-15",
    interval=1
)

# 여러 키워드 비교, 주간 트렌드
result = await get_keyword_trends(
    keyword="AI,인공지능,머신러닝",
    start_date="2024-11-01",
    end_date="2024-12-15",
    interval=2
)

# 특정 언론사만, 월간 트렌드
result = await get_keyword_trends(
    keyword="대통령",
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval=3,
    providers=["경향신문", "한겨레"]
)
```

#### 알려진 이슈

- API가 빈 결과(`root: []`)를 반환하는 경우가 있습니다
- 계정 권한이나 데이터 기간에 따라 결과가 다를 수 있습니다
- 로그인은 성공하지만 데이터는 없는 상태

---

### 2. get_related_keywords

검색 키워드와 연관된 키워드를 TF-IDF 기반으로 분석합니다.

#### 파라미터

```python
keyword: str                    # 검색 키워드
start_date: str                 # 시작일 (YYYY-MM-DD)
end_date: str                   # 종료일 (YYYY-MM-DD)
max_news_count: int = 100       # 최대 뉴스 수 (50, 100, 200, 500, 1000)
result_number: int = 50         # 연관어 결과 수
providers: list[str] | None     # 언론사 필터
categories: list[str] | None    # 카테고리 필터
```

#### 반환값

```python
{
    "success": bool,
    "keyword": str,
    "date_range": str,
    "related_words": [
        {
            "name": str,         # 연관 키워드
            "weight": float,     # TF-IDF 가중치
            "tf": int           # Term Frequency
        }
    ],
    "news_count": int,          # 분석한 뉴스 수
    "total_related_words": int,
    "top_words": [              # 상위 10개 연관어
        {
            "name": str,
            "weight": float,
            "tf": int
        }
    ],
    "summary": {
        "analyzed_articles": int,
        "max_news_count": int,
        "found_keywords": int
    }
}
```

#### 사용 예시

```python
# 기본 연관어 분석
result = await get_related_keywords(
    keyword="AI",
    start_date="2024-12-01",
    end_date="2024-12-15"
)

# 더 많은 뉴스 분석 (500건)
result = await get_related_keywords(
    keyword="대통령",
    start_date="2024-12-01",
    end_date="2024-12-15",
    max_news_count=500,
    result_number=100
)

# 특정 카테고리만 분석
result = await get_related_keywords(
    keyword="반도체",
    start_date="2024-12-01",
    end_date="2024-12-15",
    categories=["경제", "IT_과학"]
)
```

#### 테스트 결과

✅ **정상 작동** (2024-12-15 테스트)

```python
# AI 키워드 연관어 분석 (100건)
분석 뉴스 수: 50
연관어 수: 32

상위 10개:
1. 인공지능: 43.3200
2. 생성형 AI: 9.0000
3. SK텔레콤: 6.0000
4. AI 디지털교과서: 5.8600
5. 조직개편: 4.5000
6. AI 기본법: 4.2400
7. 챗GPT: 3.6800
8. B2B: 3.5300
9. AI 시대: 3.4700
10. 생성형 인공지능: 3.2700
```

---

### 3. get_network_analysis

개체(인물, 기관, 장소, 키워드) 간의 관계를 네트워크 그래프로 분석합니다.

#### 파라미터

```python
keyword: str                    # 검색 키워드
start_date: str                 # 시작일 (YYYY-MM-DD)
end_date: str                   # 종료일 (YYYY-MM-DD)
max_news_count: int = 1000      # 최대 뉴스 수
result_no: int = 100            # 표시할 노드 수
normalization: int = 10         # 정규화 값
providers: list[str] | None     # 언론사 필터
categories: list[str] | None    # 카테고리 필터
```

#### 반환값

```python
{
    "success": bool,
    "keyword": str,
    "date_range": str,
    "nodes": [
        {
            "id": str,
            "title": str,           # 표시명
            "label_ne": str,        # 개체명
            "category": str,        # PERSON, ORGANIZATION, LOCATION, KEYWORD, NEWS, ROOT
            "weight": float,        # 가중치
            "node_size": int        # 노드 크기
        }
    ],
    "links": [
        {
            "from": str,            # 출발 노드 ID
            "to": str,              # 도착 노드 ID
            "weight": float         # 관계 가중치
        }
    ],
    "news_ids": [str],              # 관련 뉴스 ID 목록
    "total_nodes": int,
    "total_links": int,
    "total_news": int,
    "nodes_by_category": {
        "PERSON": int,
        "ORGANIZATION": int,
        "LOCATION": int,
        "KEYWORD": int
    },
    "top_entities": {
        "person": [{"name": str, "weight": float}],
        "organization": [{"name": str, "weight": float}],
        "location": [{"name": str, "weight": float}],
        "keyword": [{"name": str, "weight": float}]
    }
}
```

#### 사용 예시

```python
# 기본 네트워크 분석
result = await get_network_analysis(
    keyword="AI",
    start_date="2024-12-01",
    end_date="2024-12-10"
)

# 더 상세한 분석 (많은 뉴스, 적은 노드)
result = await get_network_analysis(
    keyword="대통령",
    start_date="2024-12-01",
    end_date="2024-12-15",
    max_news_count=1000,
    result_no=50,
    normalization=5
)
```

#### 알려진 이슈

- API가 빈 결과를 반환하는 경우가 있습니다
- 로그인은 성공하지만 nodes/links가 비어있는 상태

---

## API 엔드포인트

| Tool | API 엔드포인트 | 메서드 |
|------|---------------|--------|
| get_keyword_trends | `/api/analysis/keywordTrends.do` | POST |
| get_related_keywords | `/api/analysis/relationalWords.do` | POST |
| get_network_analysis | `/news/getNetworkDataAnalysis.do` | POST |

## 에러 처리

### 로그인 실패

```python
{
    "success": False,
    "error": "Login required. Please set BIGKINDS_USER_ID and BIGKINDS_USER_PASSWORD environment variables.",
    ...
}
```

### API 호출 실패

```python
{
    "success": False,
    "error": "API 호출 실패: 500 - ...",
    ...
}
```

### 빈 결과

```python
{
    "success": True,
    "trends": [],           # 또는 nodes: [], related_words: []
    "total_keywords": 0,
    ...
}
```

## 캐싱

- 모든 시각화 API 결과는 **10분간 캐시**됩니다
- 동일한 파라미터로 재요청 시 캐시된 결과를 즉시 반환합니다
- 캐시 키는 모든 파라미터의 해시값으로 생성됩니다

## 성능 고려사항

### 권장 파라미터

| Tool | max_news_count | result_no/number | 기간 |
|------|----------------|------------------|------|
| get_keyword_trends | N/A | N/A | 최대 1년 |
| get_related_keywords | 100-500 | 50-100 | 최대 3개월 |
| get_network_analysis | 100-1000 | 50-100 | 최대 1개월 |

### 요청 제한

- BigKinds는 rate limit이 없는 것으로 추정됩니다
- 하지만 과도한 요청은 차단될 수 있으므로 적절한 간격 유지가 권장됩니다

## 트러블슈팅

### 문제: API가 빈 결과를 반환

**원인:**
- 계정 권한 부족 (무료 계정 vs 유료 계정)
- 검색 기간에 데이터가 없음
- API 내부 오류

**해결 방법:**
1. 다른 키워드로 테스트 (예: "대통령", "AI")
2. 최근 기간으로 검색 (최근 1주일)
3. 다른 계정으로 테스트

### 문제: 로그인 실패

**원인:**
- 환경변수 미설정
- 계정 정보 오류
- BigKinds 서버 문제

**해결 방법:**
1. `.env` 파일 확인
2. BigKinds 웹사이트에서 로그인 테스트
3. `tests/test_auth_api.py` 실행하여 상태 확인

## 관련 문서

- [VISUALIZATION_API.md](./VISUALIZATION_API.md): API 엔드포인트 상세 스펙
- [IMPLEMENTATION_WORKFLOW.md](./IMPLEMENTATION_WORKFLOW.md): 구현 워크플로
- [MCP_SERVER_DESIGN.md](./MCP_SERVER_DESIGN.md): 전체 아키텍처

## 업데이트 로그

- **2024-12-15**: 초기 구현
  - `get_keyword_trends` 추가 (API 빈 결과 이슈)
  - `get_related_keywords` 추가 (✅ 정상 작동)
  - `get_network_analysis` 추가 (API 빈 결과 이슈)
  - 자동 로그인 기능
  - 캐싱 지원
