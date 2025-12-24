# BigKinds MCP Server Design Specification

## 1. Overview

BigKinds MCP Server는 한국 뉴스 빅데이터 플랫폼인 BigKinds API와 원본 기사 스크래핑 기능을 Model Context Protocol(MCP)을 통해 AI 에이전트에 제공하는 서버입니다.

### 1.1 Design Goals

- **Single Responsibility**: 뉴스 검색 및 기사 추출에만 집중
- **FastMCP 기반**: Python SDK의 고수준 API 활용으로 간결한 구현
- **Async-First**: 비동기 처리로 대량 요청 성능 최적화
- **Graceful Degradation**: API 장애 시에도 부분 기능 유지
- **Context-Aware Pagination**: LLM 컨텍스트 윈도우를 고려한 페이지네이션

### 1.2 Target Users

- Claude Desktop, Claude Code 등 MCP 클라이언트
- AI 에이전트 기반 뉴스 분석 파이프라인
- RAG(Retrieval-Augmented Generation) 시스템

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          BigKinds MCP Server                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         MCP Protocol Layer                             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │  │
│  │  │     Tools       │  │   Resources     │  │       Prompts           │ │  │
│  │  ├─────────────────┤  ├─────────────────┤  ├─────────────────────────┤ │  │
│  │  │ search_news     │  │ news://         │  │ news_analysis_prompt    │ │  │
│  │  │ get_article     │  │ article://      │  │ trend_report_prompt     │ │  │
│  │  │ get_count       │  │ stats://        │  └─────────────────────────┘ │  │
│  │  │ scrape_url      │  └─────────────────┘                              │  │
│  │  └─────────────────┘                                                   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                      Pagination & Context Layer                        │  │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌────────────────────┐ │  │
│  │  │  PaginationMgr    │  │  ContextOptimizer │  │  ResponseTrimmer   │ │  │
│  │  │  - page/page_size │  │  - summary first  │  │  - max tokens      │ │  │
│  │  │  - cursor support │  │  - detail on-demand│  │  - truncation     │ │  │
│  │  │  - has_next flag  │  │  - lazy loading   │  │  - field selection│ │  │
│  │  └───────────────────┘  └───────────────────┘  └────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                           Core Layer                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │  │
│  │  │ BigKindsClient  │  │ ArticleScraper  │  │     CacheManager        │ │  │
│  │  │ (Async HTTP)    │  │ (BeautifulSoup) │  │  (TTL + LRU Cache)      │ │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        Infrastructure Layer                            │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │  │
│  │  │  Rate Limiter   │  │  Error Handler  │  │       Logging           │ │  │
│  │  │  (Token Bucket) │  │ (Circuit Break) │  │     (structlog)         │ │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                   ┌───────────────────────────────────┐
                   │        External Services          │
                   ├───────────────────────────────────┤
                   │  BigKinds API                     │
                   │  (www.bigkinds.or.kr)             │
                   │  - 10,000 articles/request max    │
                   │  - Rate limit: ~10 req/min        │
                   ├───────────────────────────────────┤
                   │  News Publisher Sites             │
                   │  (조선, 한겨레, MK, etc.)          │
                   └───────────────────────────────────┘
```

### 2.1 Pagination & Context Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LLM Context Management Flow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   LLM Request                                                           │
│       │                                                                 │
│       ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Step 1: search_news(keyword, page=1, page_size=20)             │   │
│   │  → Returns: summaries only (title, date, publisher, news_id)    │   │
│   │  → Response: ~2KB per 20 articles                               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       │  LLM decides which articles to read                             │
│       ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Step 2: get_article(news_id) - for selected articles           │   │
│   │  → Returns: full content (~5KB per article)                     │   │
│   │  → On-demand loading, not batch                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                 │
│       │  Need more results?                                             │
│       ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Step 3: search_news(keyword, page=2, page_size=20)             │   │
│   │  → has_next: true/false guides LLM decision                     │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tools Specification

### 3.1 `search_news`

뉴스 기사 검색 및 메타데이터 반환. **페이지네이션 지원**.

```python
@mcp.tool()
async def search_news(
    keyword: str,
    start_date: str,  # YYYY-MM-DD
    end_date: str,    # YYYY-MM-DD
    # Pagination parameters
    page: int = 1,              # 페이지 번호 (1부터 시작)
    page_size: int = 20,        # 페이지당 결과 수 (기본 20, 최대 100)
    # Filters
    providers: list[str] | None = None,  # 언론사 필터
    categories: list[str] | None = None,  # 카테고리 필터
    sort_by: str = "date",  # date | relevance
) -> SearchResult:
    """
    BigKinds에서 뉴스 기사를 검색합니다.

    Args:
        keyword: 검색 키워드 (AND/OR 연산자 지원)
        start_date: 검색 시작일 (YYYY-MM-DD)
        end_date: 검색 종료일 (YYYY-MM-DD)
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과 수 (기본값: 20, 최대: 100)
        providers: 언론사 필터 (예: ["경향신문", "한겨레"])
        categories: 카테고리 필터 (예: ["경제", "IT_과학"])
        sort_by: 정렬 방식 (date: 날짜순, relevance: 관련도순)

    Returns:
        SearchResult with pagination metadata and article summaries

    Note:
        - page_size 기본값 20은 LLM 컨텍스트 효율성을 위함
        - 상세 내용은 get_article로 개별 조회
        - has_next로 추가 페이지 존재 여부 확인
    """
```

**Response Schema:**
```json
{
  "total_count": 12345,
  "page": 1,
  "page_size": 20,
  "total_pages": 618,
  "has_next": true,
  "has_prev": false,
  "articles": [
    {
      "news_id": "01100001.20241215...",
      "title": "AI 기술 발전과 산업 영향",
      "summary": "인공지능 기술이 제조업 분야에...",
      "publisher": "한겨레",
      "published_date": "2024-12-15",
      "category": "IT_과학"
    }
  ]
}
```

**Pagination Design Decisions:**

| Decision | Value | Rationale |
|----------|-------|-----------|
| Default page_size | 20 | LLM 컨텍스트 효율성 (~2KB) |
| Max page_size | 100 | API 성능 + 컨텍스트 밸런스 |
| Pagination type | Offset-based | BigKinds API 호환 |
| Summary only | Yes | 전문은 get_article로 분리 |

### 3.2 `get_article`

단일 기사의 상세 정보 조회 (원본 스크래핑 포함).

```python
@mcp.tool()
async def get_article(
    news_id: str | None = None,
    url: str | None = None,
    include_full_content: bool = True,
    include_images: bool = False,
) -> ArticleDetail:
    """
    기사의 상세 정보를 가져옵니다.

    Args:
        news_id: BigKinds 기사 ID (news_id 또는 url 중 하나 필수)
        url: 원본 기사 URL
        include_full_content: 원본 기사 전문 포함 여부 (기본값: True)
        include_images: 이미지 URL 목록 포함 여부 (기본값: False)

    Returns:
        기사 상세 정보 (제목, 전문, 발행일, 기자, 이미지 등)
    """
```

**Response Schema:**
```json
{
  "news_id": "01100001.20241215...",
  "title": "AI 기술 발전과 산업 영향",
  "full_content": "인공지능(AI) 기술이 제조업 분야에서 혁신을 이끌고 있다...",
  "summary": "인공지능 기술이 제조업 분야에...",
  "publisher": "한겨레",
  "author": "홍길동 기자",
  "published_date": "2024-12-15T09:30:00+09:00",
  "category": "IT_과학",
  "url": "https://www.hani.co.kr/...",
  "images": [
    {"url": "https://...", "caption": "AI 로봇 공장", "is_main": true}
  ],
  "keywords": ["AI", "제조업", "자동화"]
}
```

### 3.3 `get_article_count`

키워드별 기사 수 조회 (트렌드 분석용).

```python
@mcp.tool()
async def get_article_count(
    keyword: str,
    start_date: str,
    end_date: str,
    group_by: str = "day",  # day | week | month
    providers: list[str] | None = None,
) -> ArticleCountResult:
    """
    키워드의 기사 수를 시간대별로 집계합니다.

    Args:
        keyword: 검색 키워드
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        group_by: 집계 단위 (day/week/month)
        providers: 언론사 필터

    Returns:
        시간대별 기사 수 집계 결과
    """
```

**Response Schema:**
```json
{
  "keyword": "AI",
  "total_count": 5432,
  "date_range": "2024-01-01 to 2024-12-15",
  "counts": [
    {"date": "2024-01", "count": 423},
    {"date": "2024-02", "count": 512}
  ],
  "top_providers": [
    {"name": "한겨레", "count": 234},
    {"name": "조선일보", "count": 198}
  ]
}
```

### 3.4 `scrape_article_url`

외부 URL에서 기사 내용 추출.

```python
@mcp.tool()
async def scrape_article_url(
    url: str,
    extract_images: bool = False,
) -> ScrapedArticle:
    """
    URL에서 기사 내용을 스크래핑합니다.

    Args:
        url: 스크래핑할 기사 URL
        extract_images: 이미지 추출 여부

    Returns:
        스크래핑된 기사 정보

    Note:
        이 도구는 BigKinds 검색 결과의 원본 URL에서 전문을 가져올 때 사용합니다.
        언론사 이용약관을 준수하여 사용해주세요.
    """
```

---

## 4. Data Models (Pydantic Schemas)

### 4.1 Pagination Models

```python
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar('T')

class PaginationMeta(BaseModel):
    """페이지네이션 메타데이터"""
    total_count: int = Field(..., description="전체 결과 수")
    page: int = Field(..., ge=1, description="현재 페이지 (1부터 시작)")
    page_size: int = Field(..., ge=1, le=100, description="페이지당 결과 수")
    total_pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")

class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션이 적용된 응답"""
    pagination: PaginationMeta
    items: list[T]
```

### 4.2 Article Models

```python
class ArticleSummary(BaseModel):
    """검색 결과용 기사 요약 (컨텍스트 최적화)"""
    news_id: str = Field(..., description="BigKinds 기사 ID")
    title: str = Field(..., description="기사 제목")
    summary: str = Field(..., max_length=300, description="요약 (200자 내외)")
    publisher: str = Field(..., description="언론사")
    published_date: str = Field(..., description="발행일 (YYYY-MM-DD)")
    category: str | None = Field(None, description="카테고리")
    # URL은 검색 결과에서 제외 (컨텍스트 절약)
    # 필요시 get_article로 조회

class ArticleDetail(BaseModel):
    """기사 상세 정보 (전문 포함)"""
    news_id: str
    title: str
    summary: str
    full_content: str | None = Field(None, description="기사 전문")
    publisher: str
    author: str | None = Field(None, description="기자/작성자")
    published_date: str
    category: str | None
    url: str = Field(..., description="원본 기사 URL")
    images: list[ArticleImage] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    # 스크래핑 메타데이터
    scrape_status: str | None = Field(None, description="스크래핑 상태")
    content_length: int = Field(0, description="본문 길이 (자)")

class ArticleImage(BaseModel):
    """기사 이미지"""
    url: str
    caption: str | None = None
    is_main: bool = False
```

### 4.3 Search Result Model

```python
class SearchResult(BaseModel):
    """검색 결과 (페이지네이션 포함)"""
    # Pagination
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    # Results
    articles: list[ArticleSummary]

    # Query metadata
    keyword: str
    date_range: str

    @property
    def is_last_page(self) -> bool:
        return not self.has_next

    def get_next_page_hint(self) -> str | None:
        """LLM에게 다음 페이지 힌트 제공"""
        if self.has_next:
            return f"More results available. Call search_news with page={self.page + 1}"
        return None
```

### 4.4 Context Size Estimation

```python
# 컨텍스트 크기 추정 (UTF-8 기준)
CONTEXT_ESTIMATES = {
    "ArticleSummary": 150,      # ~150 bytes per summary
    "ArticleDetail": 5000,      # ~5KB per full article
    "SearchResult_20": 3500,    # 20 summaries + metadata
    "SearchResult_50": 8000,    # 50 summaries + metadata
    "SearchResult_100": 16000,  # 100 summaries + metadata
}

# LLM 컨텍스트 윈도우 기준 권장 설정
RECOMMENDED_PAGE_SIZES = {
    "claude-3-opus": 50,     # 200K context
    "claude-3-sonnet": 30,   # 200K context
    "claude-3-haiku": 20,    # 200K context
    "gpt-4-turbo": 30,       # 128K context
    "gpt-4o": 50,            # 128K context
}
```

---

## 5. Resources Specification

### 5.1 `news://{keyword}/{date}`

특정 날짜의 키워드 검색 결과를 리소스로 제공.

```python
@mcp.resource("news://{keyword}/{date}")
async def get_news_resource(keyword: str, date: str) -> str:
    """특정 날짜의 뉴스 검색 결과를 마크다운으로 반환"""
```

### 5.2 `article://{news_id}`

개별 기사를 리소스로 제공.

```python
@mcp.resource("article://{news_id}")
async def get_article_resource(news_id: str) -> str:
    """기사 상세 정보를 마크다운으로 반환"""
```

### 5.3 `stats://providers`

언론사 코드 목록 리소스.

```python
@mcp.resource("stats://providers")
async def get_providers_resource() -> str:
    """사용 가능한 언론사 코드 목록"""
```

---

## 6. Prompts Specification

### 6.1 `news_analysis`

뉴스 분석용 프롬프트 템플릿.

```python
@mcp.prompt()
def news_analysis_prompt(
    keyword: str,
    start_date: str,
    end_date: str,
    analysis_type: str = "summary",  # summary | sentiment | trend
) -> str:
    """
    뉴스 분석을 위한 프롬프트를 생성합니다.

    Args:
        keyword: 분석할 키워드
        start_date: 분석 시작일
        end_date: 분석 종료일
        analysis_type: 분석 유형
            - summary: 주요 내용 요약
            - sentiment: 감성 분석
            - trend: 트렌드 분석
    """
    return f"""
다음 조건으로 뉴스를 분석해주세요:

키워드: {keyword}
기간: {start_date} ~ {end_date}
분석 유형: {analysis_type}

1. 먼저 search_news 도구로 기사를 검색하세요.
2. 주요 기사 3-5개를 get_article로 상세 조회하세요.
3. 분석 결과를 작성해주세요.
"""
```

---

## 7. Usage Examples

### 7.1 Basic Pagination Flow

```python
# Example: LLM이 뉴스 검색 및 페이지네이션을 사용하는 흐름

# Step 1: 첫 페이지 검색
result = await search_news(
    keyword="AI 반도체",
    start_date="2024-12-01",
    end_date="2024-12-15",
    page=1,
    page_size=20
)
# Response:
# {
#   "total_count": 543,
#   "page": 1, "page_size": 20, "total_pages": 28,
#   "has_next": true, "has_prev": false,
#   "articles": [...20 summaries...]
# }

# Step 2: LLM이 관심있는 기사 상세 조회
article = await get_article(news_id="01100901.20241215...")
# Response: full_content 포함된 상세 정보

# Step 3: 더 많은 결과 필요 시 다음 페이지
result = await search_news(
    keyword="AI 반도체",
    start_date="2024-12-01",
    end_date="2024-12-15",
    page=2,  # 다음 페이지
    page_size=20
)
```

### 7.2 Context-Efficient Analysis Workflow

```python
# 대량 기사 분석 시 컨텍스트 효율적 접근

# 1. 전체 수 먼저 확인 (가벼운 요청)
count_result = await get_article_count(
    keyword="금리 인상",
    start_date="2024-01-01",
    end_date="2024-12-15",
    group_by="month"
)
# → 월별 추이 파악

# 2. 특정 기간만 상세 검색
result = await search_news(
    keyword="금리 인상",
    start_date="2024-11-01",  # 관심 기간만
    end_date="2024-11-30",
    page_size=30  # 적정 수준
)

# 3. Top 5 기사만 전문 조회
for article in result.articles[:5]:
    detail = await get_article(news_id=article.news_id)
    # 분석 수행
```

### 7.3 Bulk Processing with Generator

```python
# 전체 결과 순회 (내부 구현 예시)

async def iter_all_articles(keyword: str, start_date: str, end_date: str):
    """모든 기사를 페이지 단위로 순회"""
    page = 1
    while True:
        result = await search_news(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=100  # 벌크 처리 시 최대값 사용
        )

        for article in result.articles:
            yield article

        if not result.has_next:
            break
        page += 1
```

---

## 8. Implementation Details

### 8.1 Project Structure

```
bigkinds/
├── pyproject.toml          # uv 프로젝트 설정
├── src/
│   └── bigkinds_mcp/
│       ├── __init__.py
│       ├── server.py       # MCP 서버 메인
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search.py   # search_news, get_article_count
│       │   ├── article.py  # get_article, scrape_article_url
│       │   └── schemas.py  # Pydantic 스키마
│       ├── resources/
│       │   ├── __init__.py
│       │   └── news.py     # 리소스 핸들러
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── analysis.py # 프롬프트 템플릿
│       ├── core/
│       │   ├── __init__.py
│       │   ├── client.py   # BigKindsClient (기존 코드 활용)
│       │   ├── scraper.py  # ArticleScraper (기존 코드 활용)
│       │   └── cache.py    # 인메모리 캐시
│       └── utils/
│           ├── __init__.py
│           ├── rate_limit.py
│           └── errors.py
├── tests/
│   ├── test_tools.py
│   ├── test_resources.py
│   └── test_integration.py
└── docs/
    └── MCP_SERVER_DESIGN.md
```

### 8.2 Server Entry Point

```python
# src/bigkinds_mcp/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "bigkinds-news",
    version="1.0.0",
    json_response=True,
)

# Tools 등록
from .tools import search, article

mcp.tool()(search.search_news)
mcp.tool()(search.get_article_count)
mcp.tool()(article.get_article)
mcp.tool()(article.scrape_article_url)

# Resources 등록
from .resources import news

mcp.resource("news://{keyword}/{date}")(news.get_news_resource)
mcp.resource("article://{news_id}")(news.get_article_resource)
mcp.resource("stats://providers")(news.get_providers_resource)

# Prompts 등록
from .prompts import analysis

mcp.prompt()(analysis.news_analysis_prompt)

if __name__ == "__main__":
    mcp.run(transport="stdio")  # Claude Desktop용
    # mcp.run(transport="streamable-http")  # HTTP용
```

### 8.3 Dependencies

```toml
# pyproject.toml
[project]
name = "bigkinds-mcp"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",        # async HTTP client
    "beautifulsoup4>=4.12.0",
    "pydantic>=2.0.0",
    "structlog>=24.0.0",    # structured logging
    "cachetools>=5.0.0",    # TTL cache
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",        # httpx mocking
]
```

---

## 9. Error Handling

### 9.1 Error Categories

| Category | Code | Description | Retry |
|----------|------|-------------|-------|
| CLIENT_ERROR | 4xx | 잘못된 요청 (파라미터 오류) | No |
| RATE_LIMITED | 429 | API 요청 제한 초과 | Yes (60s) |
| API_ERROR | 5xx | BigKinds API 서버 오류 | Yes (30s) |
| SCRAPE_ERROR | - | 스크래핑 실패 | No |
| TIMEOUT | - | 요청 타임아웃 | Yes (1x) |

### 9.2 Error Response Schema

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "API 요청 제한을 초과했습니다. 60초 후 재시도해주세요.",
    "retry_after": 60,
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2024-12-15T10:30:00+09:00"
    }
  }
}
```

---

## 10. Rate Limiting & Caching

### 10.1 Rate Limiting

```python
# Token Bucket Algorithm
RATE_LIMIT_CONFIG = {
    "search_news": {"rate": 10, "burst": 5},      # 10 req/min, burst 5
    "get_article": {"rate": 30, "burst": 10},     # 30 req/min, burst 10
    "scrape_article_url": {"rate": 20, "burst": 5},  # 20 req/min
}
```

### 10.2 Caching Strategy

| Operation | Cache TTL | Key Pattern |
|-----------|-----------|-------------|
| search_news | 5분 | `search:{keyword}:{dates}:{hash(params)}` |
| get_article_count | 1시간 | `count:{keyword}:{dates}` |
| get_article | 24시간 | `article:{news_id}` |
| scrape_article_url | 24시간 | `scrape:{url_hash}` |

---

## 11. Configuration

### 11.1 Environment Variables

```bash
# .env
BIGKINDS_TIMEOUT=120        # API 타임아웃 (초)
BIGKINDS_MAX_RETRIES=3      # 최대 재시도 횟수
BIGKINDS_RATE_LIMIT_DELAY=0.5  # 요청 간 딜레이 (초)

# 캐시 설정
CACHE_MAX_SIZE=1000         # 최대 캐시 항목 수
CACHE_DEFAULT_TTL=300       # 기본 TTL (초)

# 로깅
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 11.2 Claude Desktop Configuration

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uv",
      "args": ["run", "bigkinds-mcp"],
      "env": {
        "BIGKINDS_TIMEOUT": "120",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

## 12. Testing Strategy

### 12.1 Unit Tests

```python
# tests/test_tools.py
import pytest
from bigkinds_mcp.tools import search

@pytest.mark.asyncio
async def test_search_news_valid():
    result = await search.search_news(
        keyword="AI",
        start_date="2024-12-01",
        end_date="2024-12-15",
        max_results=10,
    )
    assert result.total_count > 0
    assert len(result.articles) <= 10

@pytest.mark.asyncio
async def test_search_news_invalid_date():
    with pytest.raises(ValueError):
        await search.search_news(
            keyword="AI",
            start_date="invalid",
            end_date="2024-12-15",
        )
```

### 12.2 Integration Tests

```python
# tests/test_integration.py
from mcp import Client

@pytest.mark.asyncio
async def test_full_workflow():
    async with Client("bigkinds") as client:
        # 1. 검색
        search_result = await client.call_tool(
            "search_news",
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-15",
        )

        # 2. 첫 번째 기사 상세 조회
        article = await client.call_tool(
            "get_article",
            news_id=search_result["articles"][0]["news_id"],
        )

        assert article["full_content"]
```

---

## 13. Reference: Similar MCP Servers

### 13.1 news_mcp (skydockAI)

- **구조**: RSS 피드 기반 뉴스 수집
- **Tools**: `get_news_rss_list`, `get_news_feeds`, `get_news_article`
- **특징**: OpenAI 모델로 요약/감성분석
- **참고점**: 구조화된 응답 스키마

### 13.2 mcp-newsapi (matteoantoci)

- **구조**: NewsAPI.org 래퍼
- **Tools**: `search`, `top_headlines`
- **특징**: 카테고리/국가별 필터링
- **참고점**: 페이지네이션 처리

### 13.3 Best Practices Applied

| Practice | Implementation |
|----------|----------------|
| Single Responsibility | 뉴스 검색/스크래핑에만 집중 |
| Defense in Depth | Rate Limiting + Caching + Error Handling |
| Fail-Safe Design | Circuit Breaker + Fallback 캐시 |
| Comprehensive Error Handling | 에러 분류 및 재시도 정책 |
| Structured Logging | structlog으로 JSON 로깅 |

---

## 14. Implementation Phases

### Phase 1: Core (MVP)
- [ ] FastMCP 서버 셋업
- [ ] `search_news` 도구 구현
- [ ] `get_article` 도구 구현
- [ ] 기본 에러 핸들링

### Phase 2: Enhanced
- [ ] `get_article_count` 도구 구현
- [ ] `scrape_article_url` 도구 구현
- [ ] 캐싱 레이어 추가
- [ ] Rate Limiting 구현

### Phase 3: Production
- [ ] Resources 구현
- [ ] Prompts 구현
- [ ] Health check 엔드포인트
- [ ] 통합 테스트
- [ ] 문서화

---

## 15. Appendix

### A. BigKinds Provider Codes (주요 언론사)

| Code | Name |
|------|------|
| 01100001 | 경향신문 |
| 01100101 | 국민일보 |
| 01100201 | 내일신문 |
| 01100301 | 동아일보 |
| 01100401 | 문화일보 |
| 01100501 | 서울신문 |
| 01100601 | 세계일보 |
| 01100701 | 조선일보 |
| 01100801 | 중앙일보 |
| 01100901 | 한겨레 |
| 01101001 | 한국일보 |

### B. Category Codes

| Code | Name |
|------|------|
| 정치 | 정치 |
| 경제 | 경제 |
| 사회 | 사회 |
| 문화 | 문화 |
| 국제 | 국제 |
| 지역 | 지역 |
| 스포츠 | 스포츠 |
| IT_과학 | IT/과학 |
