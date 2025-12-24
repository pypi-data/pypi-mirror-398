# BigKinds MCP Server Architecture v2

> 관계도 분석 제거, Unofficial API 기반 완전한 MCP 포팅 설계

## 1. Executive Summary

### 목표
BigKinds 웹사이트의 Unofficial HTTP API를 활용하여 한국 뉴스 검색/분석 기능을 MCP(Model Context Protocol) 서버로 완전히 포팅

### 핵심 원칙
1. **작동하는 API만 포함**: 테스트 검증된 API만 구현
2. **관계도 분석 제외**: 브라우저 전용 API로 httpx 호출 불가
3. **캐싱 최적화**: 동일 요청 중복 호출 방지
4. **에러 복원력**: 우아한 실패 처리 및 재시도

---

## 2. API Capability Matrix

### 2.1 사용 가능한 API (Verified ✅)

| API | 엔드포인트 | 인증 | 상태 | 용도 |
|-----|-----------|------|------|------|
| 뉴스 검색 | `POST /api/news/search.do` | 불필요 | ✅ | 키워드 기반 뉴스 검색 |
| 오늘의 이슈 | `GET /search/trendReportData2.do` | 불필요 | ✅ | 일별 핫이슈 조회 |
| 연관어 분석 | `POST /api/analysis/relationalWords.do` | 로그인 | ✅ | TF-IDF 연관 키워드 |
| 키워드 트렌드 | `POST /api/analysis/keywordTrends.do` | 로그인 | ✅ | 시계열 기사 수 추이 |
| 로그인 | `POST /api/account/signin.do` | - | ✅ | 세션 인증 |

### 2.2 제외된 API (브라우저 전용)

| API | 엔드포인트 | 제외 사유 |
|-----|-----------|----------|
| 관계도 분석 | `POST /news/getNetworkDataAnalysis.do` | 302 → `/err/error400.do` 리다이렉트 |
| 노드 상세 | `POST /news/nodeDetailData.do` | 관계도 의존 |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                                │
│                   (Claude Desktop, etc.)                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │ MCP Protocol (stdio/SSE)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BigKinds MCP Server                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    FastMCP Framework                     │    │
│  │  ┌──────────┐  ┌───────────┐  ┌─────────────────────┐   │    │
│  │  │  Tools   │  │ Resources │  │      Prompts        │   │    │
│  │  │  (11개)  │  │   (4개)   │  │       (4개)         │   │    │
│  │  └────┬─────┘  └─────┬─────┘  └──────────┬──────────┘   │    │
│  └───────┼──────────────┼───────────────────┼──────────────┘    │
│          │              │                   │                    │
│  ┌───────▼──────────────▼───────────────────▼──────────────┐    │
│  │                   Core Layer                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐    │    │
│  │  │AsyncClient  │  │AsyncScraper │  │   MCPCache    │    │    │
│  │  │(httpx+auth) │  │(BeautifulSoup)│ │  (TTLCache)  │    │    │
│  │  └──────┬──────┘  └──────┬──────┘  └───────────────┘    │    │
│  └─────────┼────────────────┼──────────────────────────────┘    │
└────────────┼────────────────┼───────────────────────────────────┘
             │                │
             ▼                ▼
┌────────────────────┐  ┌─────────────────────┐
│  BigKinds API      │  │   News Websites     │
│  (www.bigkinds.or.kr)│  │  (Naver, etc.)    │
└────────────────────┘  └─────────────────────┘
```

---

## 4. Component Design

### 4.1 MCP Tools (14개)

#### 4.1.1 Public Tools (인증 불필요) - 9개

> 환경변수 없이 바로 사용 가능

| Tool | 설명 | 파라미터 |
|------|------|----------|
| `search_news` | 뉴스 검색 | keyword, start_date, end_date, page, page_size, providers, categories, sort_by |
| `search_news_batch` | 병렬 뉴스 검색 (v1.6.0) | queries[], max_concurrent |
| `get_article_count` | 기사 수 집계 | keyword, start_date, end_date, group_by, providers |
| `get_article` | 기사 상세 조회 | news_id (BigKinds detailView API, 전문 반환) |
| `scrape_article_url` | URL 스크래핑 | url, extract_images |
| `get_today_issues` | 오늘의 이슈 | date, category ("전체", "AI"만 지원) |
| `get_current_korean_time` | 현재 한국 시간 | - |
| `find_category` | 코드 검색 | query, category_type |
| `list_providers` | 언론사 목록 | - |
| `list_categories` | 카테고리 목록 | - |

#### 4.1.2 Private Tools (로그인 필요) - 2개

> **환경변수 필수**: `BIGKINDS_USER_ID`, `BIGKINDS_USER_PASSWORD`
>
> 환경변수 미설정 시 아래 에러 반환:
> ```json
> {
>   "success": false,
>   "error": "Login required. Please set BIGKINDS_USER_ID and BIGKINDS_USER_PASSWORD environment variables."
> }
> ```

| Tool | 설명 | 파라미터 |
|------|------|----------|
| `get_keyword_trends` | 키워드 트렌드 (시계열 기사 수) | keyword, start_date, end_date, interval, providers, categories |
| `get_related_keywords` | 연관어 분석 (TF-IDF) | keyword, start_date, end_date, max_news_count, result_number, providers, categories |

#### 4.1.3 Utility Tools (MCP 확장 기능) - 3개

| Tool | 설명 | 파라미터 |
|------|------|----------|
| `compare_keywords` | 여러 키워드 기사 수 비교 | keywords[] (2-10개), start_date, end_date, group_by |
| `smart_sample` | 대표 샘플 추출 | keyword, start_date, end_date, sample_size, strategy |
| `export_all_articles` | 전체 기사 내보내기 | keyword, start_date, end_date, output_format, max_articles |

#### 4.1.4 제거된 Tools - 1개

| Tool | 제거 사유 |
|------|----------|
| ~~`get_network_analysis`~~ | 브라우저 전용 API, httpx 직접 호출 시 302 리다이렉트 |

### 4.2 MCP Resources (4개)

| Resource URI | 설명 | 반환 형식 |
|--------------|------|----------|
| `stats://providers` | 언론사 코드 목록 | Markdown |
| `stats://categories` | 카테고리 코드 목록 | Markdown |
| `news://{keyword}/{date}` | 특정 날짜 뉴스 | Markdown |
| `article://{news_id}` | 개별 기사 정보 | Markdown |

### 4.3 MCP Prompts (4개)

| Prompt | 설명 | 파라미터 |
|--------|------|----------|
| `news_analysis` | 뉴스 분석 프롬프트 | keyword, start_date, end_date, analysis_type |
| `trend_report` | 트렌드 리포트 생성 | keyword, days |
| `issue_briefing` | 일일 이슈 브리핑 | date |
| `keyword_comparison` | 키워드 비교 분석 | keywords[], start_date, end_date |

---

## 5. Data Flow Architecture

### 5.1 인증 흐름

```
┌──────────┐     ┌─────────────────┐     ┌──────────────┐
│  환경변수 │────▶│  AsyncClient    │────▶│ BigKinds API │
│ USER_ID  │     │  .login()       │     │ /signin.do   │
│ PASSWORD │     └────────┬────────┘     └──────┬───────┘
└──────────┘              │                     │
                          │                     ▼
                    ┌─────▼─────────────────────────────┐
                    │         httpx Session             │
                    │    (쿠키/세션 자동 유지)            │
                    └───────────────────────────────────┘
```

### 5.2 검색 흐름

```
search_news("AI", "2024-12-01", "2024-12-15")
              │
              ▼
    ┌─────────────────┐
    │   Cache Check   │◀─── Hit ──▶ Return Cached
    └────────┬────────┘
             │ Miss
             ▼
    ┌─────────────────┐
    │  sort_by check  │
    └────────┬────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
 "date"   "both"  "relevance"
    │        │        │
    │   ┌────┴────┐   │
    │   │ 2 calls │   │
    │   └────┬────┘   │
    │        │        │
    └────────┼────────┘
             ▼
    ┌─────────────────┐
    │  Merge & Dedup  │
    │ (news_id 기준)  │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │   Cache Store   │
    └────────┬────────┘
             ▼
         Response
```

### 5.3 분석 API 흐름 (로그인 필요)

```
get_keyword_trends("AI", ...)
              │
              ▼
    ┌─────────────────┐
    │  Login Check    │
    │ _is_logged_in?  │
    └────────┬────────┘
             │ False
             ▼
    ┌─────────────────┐
    │   Auto Login    │
    │  (환경변수 사용) │
    └────────┬────────┘
             │ Success
             ▼
    ┌─────────────────┐
    │  API Request    │
    │  + searchKey    │◀─── 필수 파라미터
    │  + indexName    │
    └────────┬────────┘
             ▼
         Response
```

---

## 6. Module Structure

```
bigkinds/
├── src/bigkinds_mcp/
│   ├── __init__.py
│   ├── server.py                 # FastMCP 엔트리포인트
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── async_client.py       # BigKinds HTTP 클라이언트 (인증 포함)
│   │   ├── async_scraper.py      # 기사 스크래핑
│   │   └── cache.py              # TTL 캐시
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py             # search_news, get_article_count
│   │   ├── article.py            # get_article, scrape_article_url
│   │   ├── analysis.py           # get_keyword_trends, get_related_keywords (통합)
│   │   └── utils.py              # 유틸리티 도구들
│   │
│   ├── resources/
│   │   ├── __init__.py
│   │   └── news.py               # MCP Resources
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── analysis.py           # MCP Prompts
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic 스키마
│   │
│   └── utils/
│       ├── __init__.py
│       ├── errors.py             # 커스텀 예외
│       ├── markdown.py           # 마크다운 포맷팅
│       └── image_filter.py       # 이미지 필터링
│
├── bigkinds/                     # 기존 레거시 코드 (래핑용)
│   ├── client.py
│   ├── models.py
│   ├── searcher.py
│   └── article_scraper.py
│
└── tests/
    ├── test_tools.py
    ├── test_resources.py
    └── test_integration.py
```

---

## 7. API Specifications

### 7.1 search_news

```python
@mcp.tool()
async def search_news(
    keyword: str,           # 검색 키워드 (AND/OR 연산자 지원)
    start_date: str,        # 시작일 (YYYY-MM-DD)
    end_date: str,          # 종료일 (YYYY-MM-DD)
    page: int = 1,          # 페이지 번호
    page_size: int = 20,    # 페이지당 결과 수 (최대 100)
    providers: list[str] | None = None,   # 언론사 필터
    categories: list[str] | None = None,  # 카테고리 필터
    sort_by: str = "both",  # 정렬: "both" | "date" | "relevance"
) -> dict:
    """BigKinds에서 뉴스 기사를 검색합니다."""
```

**Response Schema:**
```json
{
  "success": true,
  "total_count": 9817,
  "page": 1,
  "page_size": 20,
  "total_pages": 491,
  "articles": [
    {
      "news_id": "01100901.20241215...",
      "title": "AI 기술 발전...",
      "summary": "인공지능 기술이...",
      "publisher": "경향신문",
      "category": "IT_과학",
      "news_date": "2024-12-15",
      "url": "https://..."
    }
  ]
}
```

### 7.2 get_keyword_trends (로그인 필요)

```python
@mcp.tool()
async def get_keyword_trends(
    keyword: str,           # 검색 키워드 (콤마로 여러 개 가능)
    start_date: str,        # 시작일
    end_date: str,          # 종료일
    interval: int = 1,      # 1: 일간, 2: 주간, 3: 월간, 4: 연간
    providers: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict:
    """키워드별 기사 수 추이를 분석합니다."""
```

**Response Schema:**
```json
{
  "success": true,
  "keyword": "AI",
  "date_range": "2024-12-01 to 2024-12-15",
  "interval": 1,
  "interval_name": "일간",
  "trends": [
    {
      "keyword": "AI",
      "data": [
        {"date": "2024-12-01", "count": 125},
        {"date": "2024-12-02", "count": 98}
      ],
      "total_count": 1523
    }
  ],
  "summary": {
    "keywords_analyzed": ["AI"],
    "total_articles_sum": 1523
  }
}
```

### 7.3 get_related_keywords (로그인 필요)

```python
@mcp.tool()
async def get_related_keywords(
    keyword: str,           # 검색 키워드
    start_date: str,        # 시작일
    end_date: str,          # 종료일
    max_news_count: int = 100,   # 분석할 뉴스 수 (50, 100, 200, 500, 1000)
    result_number: int = 50,     # 반환할 연관어 수
    providers: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict:
    """TF-IDF 기반 연관어를 분석합니다."""
```

**Response Schema:**
```json
{
  "success": true,
  "keyword": "AI",
  "date_range": "2024-12-01 to 2024-12-15",
  "related_words": [
    {"name": "인공지능", "weight": 0.85, "tf": 45},
    {"name": "생성형 AI", "weight": 0.72, "tf": 38}
  ],
  "news_count": 100,
  "top_words": [...],
  "summary": {
    "analyzed_articles": 100,
    "found_keywords": 33
  }
}
```

---

## 8. Caching Strategy

### 8.1 캐시 정책

| 데이터 유형 | TTL | 키 패턴 |
|------------|-----|---------|
| 뉴스 검색 결과 | 5분 | `search_{hash(params)}` |
| 기사 상세 | 30분 | `article_{news_id}` |
| 기사 수 집계 | 10분 | `count_{hash(params)}` |
| 키워드 트렌드 | 10분 | `trends_{hash(params)}` |
| 연관어 분석 | 10분 | `related_{hash(params)}` |
| 오늘의 이슈 | 5분 | `issues_{date}_{category}` |
| 언론사/카테고리 | 24시간 | `providers`, `categories` |

### 8.2 캐시 구현

```python
class MCPCache:
    def __init__(self, default_ttl: int = 300):
        self._cache = TTLCache(maxsize=1000, ttl=default_ttl)

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        # TTL 개별 설정은 별도 캐시 인스턴스 사용
        self._cache[key] = value
```

---

## 9. Error Handling

### 9.1 에러 계층

```python
class BigKindsError(Exception):
    """Base exception for BigKinds MCP."""
    pass

class AuthenticationError(BigKindsError):
    """로그인 실패."""
    pass

class RateLimitError(BigKindsError):
    """요청 제한 초과."""
    pass

class APIError(BigKindsError):
    """API 호출 실패."""
    pass

class ScrapingError(BigKindsError):
    """스크래핑 실패."""
    pass
```

### 9.2 에러 응답 형식

```json
{
  "success": false,
  "error": "AuthenticationError",
  "message": "Login required. Please set BIGKINDS_USER_ID and BIGKINDS_USER_PASSWORD environment variables.",
  "code": "AUTH_REQUIRED"
}
```

---

## 10. Configuration

### 10.1 환경 변수

```bash
# 필수 (분석 API 사용 시)
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password

# 선택
BIGKINDS_TIMEOUT=30
BIGKINDS_CACHE_TTL=300
BIGKINDS_LOG_LEVEL=INFO
```

### 10.2 Claude Desktop 설정

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/bigkinds",
        "run", "bigkinds-mcp"
      ],
      "env": {
        "BIGKINDS_USER_ID": "your_email@example.com",
        "BIGKINDS_USER_PASSWORD": "your_password"
      }
    }
  }
}
```

---

## 11. Implementation Priority

### Phase 1: Core (완료)
- [x] 뉴스 검색 (`search_news`)
- [x] 기사 상세 (`get_article`)
- [x] 기사 스크래핑 (`scrape_article_url`)
- [x] 오늘의 이슈 (`get_today_issues`)
- [x] 유틸리티 도구들

### Phase 2: Analysis (완료)
- [x] 키워드 트렌드 (`get_keyword_trends`)
- [x] 연관어 분석 (`get_related_keywords`)
- [x] 자동 로그인 구현

### Phase 3: Cleanup (진행 중)
- [ ] 관계도 분석 제거
- [ ] visualization.py 정리
- [ ] 문서 업데이트
- [ ] 테스트 코드 정비

### Phase 4: Enhancement (향후)
- [ ] 키워드 비교 프롬프트 추가
- [ ] 배치 검색 지원
- [ ] 결과 내보내기 (CSV/JSON)
- [ ] 실시간 알림 (선택)

---

## 12. Testing Strategy

### 12.1 유닛 테스트
```bash
uv run pytest tests/test_tools.py -v
```

### 12.2 통합 테스트
```bash
# 실제 API 호출 테스트 (계정 필요)
uv run pytest tests/test_integration.py -v --env-file .env
```

### 12.3 MCP Inspector 테스트
```bash
npx @anthropic-ai/mcp-inspector uv run bigkinds-mcp
```

---

## 13. Changelog

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| v2.0 | 2024-12-15 | 관계도 분석 제거, 아키텍처 재설계 |
| v1.0 | 2024-12-14 | 초기 MCP 서버 구현 |
