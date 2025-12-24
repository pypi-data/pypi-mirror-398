# BigKinds MCP Server - 구현 워크플로

> 기존 코드 기반 MCP 서버 구현 세부 계획

## 현황 요약

### 재사용 가능한 기존 코드

| 파일 | 역할 | 재사용 방식 |
|------|------|------------|
| `client.py` | BigKinds HTTP 통신 | 비동기 래퍼 생성 |
| `models.py` | Pydantic 모델 | 확장 (MCP용 모델 추가) |
| `article_scraper.py` | 원본 기사 스크래핑 | 비동기 래퍼 생성 |
| `searcher.py` | 고수준 검색 인터페이스 | 참조용 (MCP Tools가 대체) |

### 신규 구현 필요

- FastMCP 서버 셋업
- MCP Tools (search_news, get_article, get_article_count, scrape_article_url)
- MCP Resources (news://, article://, stats://)
- MCP Prompts (news_analysis)
- 비동기 어댑터 레이어
- 인메모리 캐시

---

## Phase 1: 프로젝트 구조 재편 (30분)

### 1.1 디렉토리 구조 생성

```bash
bigkinds/
├── pyproject.toml              # 수정: dependencies 추가
├── src/
│   └── bigkinds_mcp/
│       ├── __init__.py
│       ├── server.py           # FastMCP 서버 엔트리포인트
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search.py       # search_news, get_article_count
│       │   └── article.py      # get_article, scrape_article_url
│       ├── resources/
│       │   ├── __init__.py
│       │   └── news.py         # news://, article://, stats://
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── analysis.py     # news_analysis_prompt
│       ├── core/
│       │   ├── __init__.py
│       │   ├── async_client.py # BigKindsClient 비동기 래퍼
│       │   ├── async_scraper.py# ArticleScraper 비동기 래퍼
│       │   └── cache.py        # 인메모리 캐시
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py      # MCP용 Pydantic 스키마
│       └── utils/
│           ├── __init__.py
│           └── errors.py       # 에러 정의
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_integration.py
├── client.py                   # 기존 (유지)
├── models.py                   # 기존 (유지)
├── article_scraper.py          # 기존 (유지)
├── searcher.py                 # 기존 (유지)
└── docs/
    ├── MCP_SERVER_DESIGN.md
    └── IMPLEMENTATION_WORKFLOW.md
```

### 1.2 pyproject.toml 업데이트

```toml
[project]
name = "bigkinds-mcp"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "pydantic>=2.0.0",
    "cachetools>=5.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.scripts]
bigkinds-mcp = "bigkinds_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/bigkinds_mcp"]
```

### 1.3 체크리스트

- [ ] `src/bigkinds_mcp/` 디렉토리 구조 생성
- [ ] `pyproject.toml` 업데이트
- [ ] `uv sync` 실행하여 의존성 설치

---

## Phase 2: Core Layer 구현 (1시간)

### 2.1 비동기 클라이언트 어댑터

**파일**: `src/bigkinds_mcp/core/async_client.py`

```python
"""기존 BigKindsClient의 비동기 래퍼."""

import asyncio
from functools import partial

from bigkinds.client import BigKindsClient
from bigkinds.models import SearchRequest, SearchResponse


class AsyncBigKindsClient:
    """BigKindsClient를 비동기로 래핑."""

    def __init__(self, **kwargs):
        self._client = BigKindsClient(**kwargs)
        self._loop = None

    async def search(self, request: SearchRequest) -> SearchResponse:
        """비동기 검색."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._client.search, request)
        )

    async def get_total_count(
        self,
        keyword: str,
        start_date: str,
        end_date: str
    ) -> int:
        """비동기 총 개수 조회."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._client.get_total_count, keyword, start_date, end_date)
        )

    async def health_check(self) -> bool:
        """비동기 헬스 체크."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._client.health_check
        )

    def close(self):
        self._client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()
```

### 2.2 비동기 스크래퍼 어댑터

**파일**: `src/bigkinds_mcp/core/async_scraper.py`

```python
"""기존 ArticleScraper의 비동기 래퍼."""

import asyncio
from functools import partial

from bigkinds.article_scraper import ArticleScraper, ScrapedArticle


class AsyncArticleScraper:
    """ArticleScraper를 비동기로 래핑."""

    def __init__(self, **kwargs):
        self._scraper = ArticleScraper(**kwargs)

    async def scrape(self, url: str) -> ScrapedArticle:
        """비동기 스크래핑."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._scraper.scrape, url)
        )

    def close(self):
        self._scraper.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()
```

### 2.3 인메모리 캐시

**파일**: `src/bigkinds_mcp/core/cache.py`

```python
"""간단한 TTL 캐시."""

from cachetools import TTLCache
from typing import Any, Callable
import hashlib
import json


class MCPCache:
    """MCP 서버용 캐시."""

    def __init__(self, maxsize: int = 1000, default_ttl: int = 300):
        self._search_cache = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self._article_cache = TTLCache(maxsize=maxsize, ttl=86400)  # 24시간
        self._count_cache = TTLCache(maxsize=maxsize, ttl=3600)     # 1시간

    def _make_key(self, prefix: str, **kwargs) -> str:
        """캐시 키 생성."""
        data = json.dumps(kwargs, sort_keys=True)
        hash_val = hashlib.md5(data.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_val}"

    def get_search(self, **kwargs) -> Any | None:
        key = self._make_key("search", **kwargs)
        return self._search_cache.get(key)

    def set_search(self, value: Any, **kwargs):
        key = self._make_key("search", **kwargs)
        self._search_cache[key] = value

    def get_article(self, news_id: str) -> Any | None:
        return self._article_cache.get(f"article:{news_id}")

    def set_article(self, news_id: str, value: Any):
        self._article_cache[f"article:{news_id}"] = value

    def get_count(self, **kwargs) -> Any | None:
        key = self._make_key("count", **kwargs)
        return self._count_cache.get(key)

    def set_count(self, value: Any, **kwargs):
        key = self._make_key("count", **kwargs)
        self._count_cache[key] = value
```

### 2.4 체크리스트

- [ ] `async_client.py` 구현
- [ ] `async_scraper.py` 구현
- [ ] `cache.py` 구현
- [ ] 유닛 테스트 작성

---

## Phase 3: MCP Models 정의 (30분)

### 3.1 MCP용 스키마

**파일**: `src/bigkinds_mcp/models/schemas.py`

```python
"""MCP 응답용 Pydantic 스키마."""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar('T')


class ArticleSummary(BaseModel):
    """검색 결과용 기사 요약 (컨텍스트 최적화)."""

    news_id: str = Field(..., description="BigKinds 기사 ID")
    title: str = Field(..., description="기사 제목")
    summary: str | None = Field(None, max_length=300, description="요약")
    publisher: str | None = Field(None, description="언론사")
    published_date: str | None = Field(None, description="발행일 (YYYY-MM-DD)")
    category: str | None = Field(None, description="카테고리")


class ArticleDetail(BaseModel):
    """기사 상세 정보."""

    news_id: str
    title: str
    summary: str | None = None
    full_content: str | None = Field(None, description="기사 전문")
    publisher: str | None = None
    author: str | None = None
    published_date: str | None = None
    category: str | None = None
    url: str | None = None
    images: list[dict] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    scrape_status: str | None = None
    content_length: int = 0


class PaginationMeta(BaseModel):
    """페이지네이션 메타데이터."""

    total_count: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_pages: int
    has_next: bool
    has_prev: bool


class SearchResult(BaseModel):
    """검색 결과."""

    # Pagination
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    # Results
    articles: list[ArticleSummary]

    # Query info
    keyword: str
    date_range: str

    def get_next_page_hint(self) -> str | None:
        if self.has_next:
            return f"More results available. Call search_news with page={self.page + 1}"
        return None


class ArticleCountResult(BaseModel):
    """기사 수 집계 결과."""

    keyword: str
    total_count: int
    date_range: str
    counts: list[dict]  # [{"date": "2024-01", "count": 123}]
    top_providers: list[dict] = Field(default_factory=list)


class MCPError(BaseModel):
    """에러 응답."""

    code: str
    message: str
    details: dict | None = None
```

### 3.2 체크리스트

- [ ] `schemas.py` 구현
- [ ] 기존 `models.py`에서 변환 유틸리티 추가

---

## Phase 4: MCP Tools 구현 (1.5시간)

### 4.1 search_news Tool

**파일**: `src/bigkinds_mcp/tools/search.py`

```python
"""검색 관련 MCP Tools."""

from mcp.server.fastmcp import FastMCP
from ..core.async_client import AsyncBigKindsClient
from ..core.cache import MCPCache
from ..models.schemas import SearchResult, ArticleSummary
from bigkinds.models import SearchRequest


# 전역 인스턴스 (서버 시작 시 초기화)
_client: AsyncBigKindsClient | None = None
_cache: MCPCache | None = None


def init_search_tools(client: AsyncBigKindsClient, cache: MCPCache):
    global _client, _cache
    _client = client
    _cache = cache


async def search_news(
    keyword: str,
    start_date: str,
    end_date: str,
    page: int = 1,
    page_size: int = 20,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    sort_by: str = "both",
) -> SearchResult:
    """
    BigKinds에서 뉴스 기사를 검색합니다.

    Args:
        keyword: 검색 키워드 (AND/OR 연산자 지원)
        start_date: 검색 시작일 (YYYY-MM-DD)
        end_date: 검색 종료일 (YYYY-MM-DD)
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과 수 (기본값: 20, 최대: 100)
        providers: 언론사 필터
        categories: 카테고리 필터
        sort_by: 정렬 방식
            - "both" (기본값): date + relevance 두 번 호출 후 병합
            - "date": 날짜순 (최신순)
            - "relevance": 관련도순

    Returns:
        SearchResult with pagination metadata and article summaries

    Note:
        sort_by="both"일 때 내부적으로 두 번 검색 후 news_id로 중복 제거
    """
    # 파라미터 정규화
    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)

    # 캐시 확인
    cache_params = {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "page": page,
        "page_size": page_size,
        "providers": providers,
        "categories": categories,
    }

    cached = _cache.get_search(**cache_params)
    if cached:
        return cached

    # BigKinds 요청 변환
    # page/page_size → start_no/result_number
    start_no = (page - 1) * page_size + 1

    request = SearchRequest(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        start_no=start_no,
        result_number=page_size,
        provider_codes=providers or [],
        category_codes=categories or [],
        sort_method=sort_by,
    )

    response = await _client.search(request)

    if not response.success:
        # 에러 처리
        raise ValueError(response.error_message or "Search failed")

    # 응답 변환
    total_count = response.total_count
    total_pages = (total_count + page_size - 1) // page_size

    articles = [
        ArticleSummary(
            news_id=a.news_id or "",
            title=a.title,
            summary=a.content[:200] if a.content else None,
            publisher=a.publisher,
            published_date=a.news_date[:10] if a.news_date else None,
            category=a.category,
        )
        for a in response.articles
    ]

    result = SearchResult(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        articles=articles,
        keyword=keyword,
        date_range=f"{start_date} to {end_date}",
    )

    # 캐시 저장
    _cache.set_search(result, **cache_params)

    return result


async def get_article_count(
    keyword: str,
    start_date: str,
    end_date: str,
    group_by: str = "day",
    providers: list[str] | None = None,
) -> dict:
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
    # 캐시 확인
    cache_params = {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by,
    }

    cached = _cache.get_count(**cache_params)
    if cached:
        return cached

    # 전체 개수만 빠르게 조회
    total = await _client.get_total_count(keyword, start_date, end_date)

    result = {
        "keyword": keyword,
        "total_count": total,
        "date_range": f"{start_date} to {end_date}",
        "counts": [],  # 상세 집계는 필요시 구현
        "top_providers": [],
    }

    _cache.set_count(result, **cache_params)

    return result
```

### 4.2 get_article Tool

**파일**: `src/bigkinds_mcp/tools/article.py`

```python
"""기사 관련 MCP Tools."""

from ..core.async_client import AsyncBigKindsClient
from ..core.async_scraper import AsyncArticleScraper
from ..core.cache import MCPCache
from ..models.schemas import ArticleDetail
from bigkinds.models import SearchRequest


_client: AsyncBigKindsClient | None = None
_scraper: AsyncArticleScraper | None = None
_cache: MCPCache | None = None


def init_article_tools(
    client: AsyncBigKindsClient,
    scraper: AsyncArticleScraper,
    cache: MCPCache
):
    global _client, _scraper, _cache
    _client = client
    _scraper = scraper
    _cache = cache


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
        include_full_content: 원본 기사 전문 포함 여부
        include_images: 이미지 URL 목록 포함 여부

    Returns:
        기사 상세 정보
    """
    if not news_id and not url:
        raise ValueError("news_id 또는 url 중 하나는 필수입니다")

    # 캐시 확인
    if news_id:
        cached = _cache.get_article(news_id)
        if cached:
            return cached

    article_detail = None

    # news_id로 조회
    if news_id:
        # BigKinds에서 메타데이터 조회
        # news_id로 직접 검색하는 API가 없으므로 제한적
        article_detail = ArticleDetail(
            news_id=news_id,
            title="",  # 메타데이터 필요
        )

    # URL 스크래핑
    if url and include_full_content:
        scraped = await _scraper.scrape(url)

        if scraped.success:
            article_detail = ArticleDetail(
                news_id=news_id or "",
                title=scraped.title or "",
                summary=scraped.description,
                full_content=scraped.content,
                publisher=scraped.publisher,
                author=scraped.author,
                published_date=scraped.published_date,
                url=url,
                images=scraped.images if include_images else [],
                keywords=scraped.keywords,
                scrape_status="success",
                content_length=len(scraped.content) if scraped.content else 0,
            )
        else:
            article_detail = ArticleDetail(
                news_id=news_id or "",
                title="",
                url=url,
                scrape_status=f"failed: {scraped.error}",
            )

    # 캐시 저장
    if news_id and article_detail:
        _cache.set_article(news_id, article_detail)

    return article_detail


async def scrape_article_url(
    url: str,
    extract_images: bool = False,
) -> dict:
    """
    URL에서 기사 내용을 스크래핑합니다.

    Args:
        url: 스크래핑할 기사 URL
        extract_images: 이미지 추출 여부

    Returns:
        스크래핑된 기사 정보

    Note:
        언론사 이용약관을 준수하여 사용해주세요.
    """
    scraped = await _scraper.scrape(url)

    return {
        "url": url,
        "final_url": scraped.final_url,
        "success": scraped.success,
        "title": scraped.title,
        "content": scraped.content,
        "author": scraped.author,
        "published_date": scraped.published_date,
        "publisher": scraped.publisher,
        "images": scraped.images if extract_images else [],
        "keywords": scraped.keywords,
        "error": scraped.error,
    }
```

### 4.3 체크리스트

- [ ] `tools/search.py` 구현
- [ ] `tools/article.py` 구현
- [ ] Tools 유닛 테스트

---

## Phase 5: MCP Server 통합 (30분)

### 5.1 서버 엔트리포인트

**파일**: `src/bigkinds_mcp/server.py`

```python
"""BigKinds MCP Server."""

from mcp.server.fastmcp import FastMCP

from .core.async_client import AsyncBigKindsClient
from .core.async_scraper import AsyncArticleScraper
from .core.cache import MCPCache
from .tools import search, article

# FastMCP 서버 생성
mcp = FastMCP(
    "bigkinds-news",
    version="1.0.0",
)

# 전역 인스턴스
_client: AsyncBigKindsClient | None = None
_scraper: AsyncArticleScraper | None = None
_cache: MCPCache | None = None


@mcp.on_startup
async def startup():
    """서버 시작 시 초기화."""
    global _client, _scraper, _cache

    _client = AsyncBigKindsClient()
    _scraper = AsyncArticleScraper()
    _cache = MCPCache()

    # Tools 초기화
    search.init_search_tools(_client, _cache)
    article.init_article_tools(_client, _scraper, _cache)


@mcp.on_shutdown
async def shutdown():
    """서버 종료 시 정리."""
    if _client:
        _client.close()
    if _scraper:
        _scraper.close()


# Tools 등록
mcp.tool()(search.search_news)
mcp.tool()(search.get_article_count)
mcp.tool()(article.get_article)
mcp.tool()(article.scrape_article_url)


# Resources (Phase 2에서 구현)
# @mcp.resource("news://{keyword}/{date}")
# async def get_news_resource(keyword: str, date: str) -> str:
#     ...


# Prompts (Phase 3에서 구현)
# @mcp.prompt()
# def news_analysis_prompt(...) -> str:
#     ...


def main():
    """CLI 엔트리포인트."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### 5.2 체크리스트

- [ ] `server.py` 구현
- [ ] `uv run bigkinds-mcp` 실행 테스트
- [ ] Claude Desktop 연동 테스트

---

## Phase 6: 테스트 및 문서화 (1시간)

### 6.1 통합 테스트

**파일**: `tests/test_integration.py`

```python
import pytest
from bigkinds_mcp.server import mcp


@pytest.mark.asyncio
async def test_search_news():
    """search_news 도구 테스트."""
    result = await mcp.call_tool(
        "search_news",
        keyword="AI",
        start_date="2024-12-01",
        end_date="2024-12-15",
        page_size=5,
    )

    assert result["total_count"] >= 0
    assert len(result["articles"]) <= 5


@pytest.mark.asyncio
async def test_scrape_article():
    """scrape_article_url 도구 테스트."""
    result = await mcp.call_tool(
        "scrape_article_url",
        url="https://www.hani.co.kr/arti/economy/economy_general/1111111.html",
    )

    assert "success" in result
```

### 6.2 Claude Desktop 설정

**파일**: `~/.claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uv",
      "args": ["--directory", "/path/to/bigkinds", "run", "bigkinds-mcp"],
      "env": {}
    }
  }
}
```

### 6.3 체크리스트

- [ ] 통합 테스트 작성 및 실행
- [ ] Claude Desktop 연동 테스트
- [ ] README 업데이트

---

## 구현 우선순위

| 순서 | 작업 | 예상 시간 | 의존성 |
|------|------|----------|--------|
| 1 | Phase 1: 프로젝트 구조 | 30분 | 없음 |
| 2 | Phase 2: Core Layer | 1시간 | Phase 1 |
| 3 | Phase 3: Models | 30분 | 없음 |
| 4 | Phase 4: Tools | 1.5시간 | Phase 2, 3 |
| 5 | Phase 5: Server 통합 | 30분 | Phase 4 |
| 6 | Phase 6: 테스트 | 1시간 | Phase 5 |

**총 예상 시간: 5시간**

---

## 후속 작업 (Phase 2 이후)

1. **Resources 구현**: `news://`, `article://`, `stats://`
2. **Prompts 구현**: `news_analysis_prompt`
3. **Rate Limiting**: 실제 테스트 후 필요시 추가
4. **에러 핸들링 강화**: Circuit Breaker 패턴
5. **로깅**: structlog 통합
