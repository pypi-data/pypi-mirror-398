# Response Format Integration Example

## search_news 도구 수정 예제

```python
# src/bigkinds_mcp/tools/search.py

from typing import Literal
from ..formatters.search import format_search_news_basic

# ResponseFormat 타입 추가
ResponseFormat = Literal["basic", "full"]

async def search_news(
    keyword: str,
    start_date: str,
    end_date: str,
    page: int = 1,
    page_size: int = 20,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    sort_by: str = "both",
    response_format: ResponseFormat = "basic",  # 🆕 추가
) -> dict | str:  # 🆕 str 반환 가능
    """
    BigKinds에서 뉴스 기사를 검색합니다.

    Args:
        keyword: 검색 키워드
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        page: 페이지 번호
        page_size: 페이지당 결과 수
        providers: 언론사 필터
        categories: 카테고리 필터
        sort_by: 정렬 방식 (both/date/relevance)
        response_format: 응답 형식 (basic=마크다운, full=JSON)  # 🆕

    Returns:
        - basic: 마크다운 문자열 (핵심 정보만, 컨텍스트 절약)
        - full: JSON dict (전체 데이터, 상세 분석용)
    """
    # ... 기존 검증 로직 ...

    # API 호출
    result = await _client.search(request)

    # 🆕 Response format에 따라 분기
    if response_format == "basic":
        # 마크다운 포맷으로 반환
        return format_search_news_basic(result)
    else:
        # 전체 JSON 반환 (기존 방식)
        return result
```

## get_article 도구 수정 예제

```python
# src/bigkinds_mcp/tools/article.py

from ..formatters.article import format_article_basic

async def get_article(
    news_id: str | None = None,
    url: str | None = None,
    include_full_content: bool = True,
    include_images: bool = False,
    response_format: ResponseFormat = "basic",  # 🆕
) -> dict | str:
    """
    기사의 상세 정보를 가져옵니다.

    Args:
        news_id: BigKinds 기사 ID
        url: 원본 기사 URL
        include_full_content: 전체 본문 포함 여부
        include_images: 이미지 URL 포함 여부
        response_format: 응답 형식 (basic/full)  # 🆕

    Returns:
        - basic: 마크다운 (제목, 언론사, 본문 발췌)
        - full: JSON (전체 메타데이터 + 본문)
    """
    # ... API 호출 ...

    # 🆕 포맷 분기
    if response_format == "basic":
        return format_article_basic(result)
    else:
        return result
```

## get_keyword_trends 도구 수정 예제

```python
# src/bigkinds_mcp/tools/visualization.py

from ..formatters.visualization import format_keyword_trends_basic

async def get_keyword_trends(
    keyword: str,
    start_date: str,
    end_date: str,
    interval: int = 1,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    response_format: ResponseFormat = "basic",  # 🆕
) -> dict | str:
    """
    키워드 트렌드 분석 (시간축 그래프).

    Args:
        keyword: 분석할 키워드
        start_date: 시작일
        end_date: 종료일
        interval: 시간 단위 (1=일간, 2=주간, 3=월간, 4=연간)
        providers: 언론사 필터
        categories: 카테고리 필터
        response_format: 응답 형식  # 🆕

    Returns:
        - basic: 마크다운 (ASCII 그래프 + 요약)
        - full: JSON (전체 시계열 데이터)
    """
    # ... API 호출 ...

    # 🆕 포맷 분기
    if response_format == "basic":
        return format_keyword_trends_basic(result)
    else:
        return result
```

## 모든 도구에 적용할 패턴

### 1. 파라미터 추가
```python
response_format: Literal["basic", "full"] = "basic"
```

### 2. 반환 타입 수정
```python
-> dict | str:  # basic은 str, full은 dict
```

### 3. 분기 로직 추가
```python
if response_format == "basic":
    return format_xxx_basic(result)
else:
    return result
```

### 4. Docstring 업데이트
```python
"""
Args:
    ...
    response_format: 응답 형식
        - "basic": 마크다운, 핵심 정보만, 컨텍스트 절약
        - "full": JSON, 전체 데이터, 상세 분석용

Returns:
    - basic: 마크다운 문자열
    - full: JSON dict
"""
```

## 적용 대상 도구 (14개)

### Public Tools (9개)
- [x] search_news
- [x] get_article_count
- [x] get_article
- [x] scrape_article_url
- [ ] get_today_issues (response_format 추가 필요)
- [ ] get_current_korean_time (JSON만 - 변경 불필요)
- [ ] find_category (JSON만 - 변경 불필요)
- [ ] list_providers (JSON만 - 변경 불필요)
- [ ] list_categories (JSON만 - 변경 불필요)

### Private Tools (2개)
- [x] get_keyword_trends
- [x] get_related_keywords

### Utility Tools (3개)
- [x] compare_keywords
- [x] smart_sample
- [x] export_all_articles

**총 10개 도구**에 response_format 적용 필요.

## MCP 도구 등록 시 주의사항

```python
# src/bigkinds_mcp/server.py

from mcp.server import Server
from mcp.types import Tool

mcp = Server("bigkinds")

@mcp.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_news",
            description="뉴스 기사 검색",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    # ... 기존 파라미터 ...
                    "response_format": {  # 🆕 추가
                        "type": "string",
                        "enum": ["basic", "full"],
                        "default": "basic",
                        "description": "응답 형식 (basic=마크다운, full=JSON)"
                    }
                },
                "required": ["keyword", "start_date", "end_date"]
            }
        ),
        # ... 다른 도구들 ...
    ]
```

## 테스트 예제

```python
# tests/test_response_format.py

import pytest
from src.bigkinds_mcp.tools.search import search_news

@pytest.mark.asyncio
async def test_search_news_basic_format():
    """basic 포맷이 마크다운을 반환하는지 확인."""
    result = await search_news(
        keyword="AI",
        start_date="2025-01-01",
        end_date="2025-01-10",
        response_format="basic"
    )

    assert isinstance(result, str)
    assert "# 🔍" in result
    assert "AI" in result
    assert "## 주요 기사" in result

@pytest.mark.asyncio
async def test_search_news_full_format():
    """full 포맷이 JSON을 반환하는지 확인."""
    result = await search_news(
        keyword="AI",
        start_date="2025-01-01",
        end_date="2025-01-10",
        response_format="full"
    )

    assert isinstance(result, dict)
    assert "success" in result
    assert "total_count" in result
    assert "articles" in result
```

## 모델 사용 예시

### Claude가 자동으로 basic 선택 (기본값)
```
User: "AI 관련 뉴스를 검색해줘"

Claude: [search_news 호출, response_format은 기본값 "basic"]
→ 마크다운 응답 받음 (컨텍스트 절약)
→ "AI 관련 뉴스 9,817건을 찾았습니다..."
```

### Claude가 상세 분석 필요 시 full 선택
```
User: "AI 뉴스를 모두 내보내서 Python으로 분석하고 싶어"

Claude: [search_news 호출, response_format="full"]
→ 전체 JSON 응답 받음
→ "전체 데이터를 받았습니다. export_all_articles로 저장하겠습니다..."
```

### 사용자가 명시적으로 지정
```
User: "AI 뉴스를 검색하되, 전체 JSON 데이터로 줘"

Claude: [search_news 호출, response_format="full"]
→ JSON 응답
```
