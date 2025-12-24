# Implementation Workflow v2

> PRD 기반 구현 워크플로 - BigKinds MCP Server

## Overview

### 현재 상태
| Milestone | Status | Description |
|-----------|--------|-------------|
| M1: Core Search | **완료** | search_news, get_article_count, get_article |
| M2: Content Access | **완료** | scrape_article_url, get_today_issues, Resources, Prompts |
| M3: Analysis | **완료** | 로그인, get_keyword_trends, get_related_keywords |
| M4: Cleanup & Polish | **진행 중** | 에러 핸들링, 문서화 |
| M5: Enhancement | 미착수 | 추가 기능 |

### 목표
- PRD Acceptance Criteria (AC1-AC10) 100% 충족
- 프로덕션 수준 에러 핸들링 및 안정성

### Phase 구조
```
Phase 4A (Error Handling) → Phase 4B (Testing & Docs) → Phase 5 (Enhancement)
```

---

## Phase 4A: Error Handling & Validation

> 우선순위: **High** | 예상 작업량: 4 tasks

### WF4A-1: 파라미터 유효성 검증

**목표**: PRD AC1 충족 - 입력 파라미터 검증 강화

**관련 AC**:
- AC1: 키워드 필수, 빈 키워드 시 에러 반환
- AC1: start_date, end_date 필수, YYYY-MM-DD 형식 검증
- AC1: page_size 최대 100 제한

**구현 내용**:
```python
# src/bigkinds_mcp/models/schemas.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class SearchParams(BaseModel):
    keyword: str = Field(..., min_length=1, description="검색 키워드 (필수)")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v):
        datetime.strptime(v, '%Y-%m-%d')
        return v
```

**파일**:
- `src/bigkinds_mcp/models/schemas.py` (수정)
- `src/bigkinds_mcp/tools/search.py` (수정)

**테스트**:
- [ ] 빈 키워드 → `INVALID_PARAMS` 에러
- [ ] 잘못된 날짜 형식 → `INVALID_PARAMS` 에러
- [ ] page_size > 100 → `INVALID_PARAMS` 에러

---

### WF4A-2: 에러 코드 표준화

**목표**: PRD Appendix C 에러 코드 구현

**관련 AC**:
- AC9: 에러 응답에 success=false, error 메시지 포함

**구현 내용**:
```python
# src/bigkinds_mcp/utils/errors.py
from enum import Enum

class ErrorCode(str, Enum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_FAILED = "AUTH_FAILED"
    INVALID_PARAMS = "INVALID_PARAMS"
    API_ERROR = "API_ERROR"
    SCRAPE_ERROR = "SCRAPE_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"

class BigKindsError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

def error_response(code: ErrorCode, message: str) -> dict:
    return {
        "success": False,
        "error": code.value,
        "message": message,
    }
```

**파일**:
- `src/bigkinds_mcp/utils/errors.py` (신규)
- 모든 tools/*.py (수정 - error_response 사용)

**테스트**:
- [ ] 각 에러 코드별 응답 형식 검증

---

### WF4A-3: 재시도 로직

**목표**: AC9 충족 - API 실패 시 최대 3회 재시도

**관련 AC**:
- AC9: API 실패 시 재시도 (최대 3회)

**구현 내용**:
```python
# src/bigkinds_mcp/core/async_client.py
import asyncio
from functools import wraps

def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator
```

**파일**:
- `src/bigkinds_mcp/core/async_client.py` (수정)

**테스트**:
- [ ] 일시적 네트워크 실패 시 재시도 성공
- [ ] 3회 실패 후 최종 에러 반환

---

### WF4A-4: 타임아웃 핸들링

**목표**: AC9 충족 - 네트워크 타임아웃 30초

**관련 AC**:
- AC9: 네트워크 타임아웃 30초

**구현 내용**:
```python
# src/bigkinds_mcp/core/async_client.py
import os

TIMEOUT = float(os.getenv("BIGKINDS_TIMEOUT", "30"))

self._auth_client = httpx.AsyncClient(
    verify=False,
    follow_redirects=True,
    timeout=httpx.Timeout(TIMEOUT, connect=10.0),
)
```

**파일**:
- `src/bigkinds_mcp/core/async_client.py` (수정)

**테스트**:
- [ ] 환경변수 BIGKINDS_TIMEOUT 적용 확인
- [ ] 타임아웃 발생 시 `TIMEOUT` 에러 코드 반환

---

## Phase 4B: Testing & Documentation

> 우선순위: **High** | 예상 작업량: 4 tasks | 의존성: Phase 4A 완료

### WF4B-1: AC 기반 통합 테스트

**목표**: PRD AC1-AC10 전체 검증

**구현 내용**:
```python
# tests/test_acceptance.py
import pytest

class TestAC1SearchNews:
    """AC1: search_news Acceptance Criteria"""

    async def test_keyword_required(self):
        """키워드 필수, 빈 키워드 시 에러"""
        result = await search_news(keyword="", ...)
        assert result["success"] is False
        assert result["error"] == "INVALID_PARAMS"

    async def test_date_format_validation(self):
        """YYYY-MM-DD 형식 검증"""
        result = await search_news(start_date="2024/12/15", ...)
        assert result["success"] is False

    async def test_page_size_limit(self):
        """page_size 최대 100 제한"""
        result = await search_news(page_size=200, ...)
        assert result["success"] is False

# ... AC2-AC10 테스트 계속
```

**파일**:
- `tests/test_acceptance.py` (신규)

**테스트 범위**:
- [ ] AC1: search_news (7개 항목)
- [ ] AC2: get_article (4개 항목)
- [ ] AC3: get_today_issues (3개 항목)
- [ ] AC4: get_keyword_trends (5개 항목)
- [ ] AC5: get_related_keywords (4개 항목)
- [ ] AC6: scrape_article_url (3개 항목)
- [ ] AC7: find_category (3개 항목)

---

### WF4B-2: 성능 테스트

**목표**: AC8 충족 - 응답 시간 검증

**관련 AC**:
- AC8: 뉴스 검색 응답 < 3초
- AC8: 캐시 적중 시 응답 < 100ms
- AC8: 동시 요청 10개 이상 처리

**구현 내용**:
```python
# tests/test_performance.py
import asyncio
import time

class TestAC8Performance:

    async def test_search_response_time(self):
        """뉴스 검색 응답 < 3초"""
        start = time.perf_counter()
        await search_news(keyword="AI", ...)
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0

    async def test_cache_response_time(self):
        """캐시 적중 시 응답 < 100ms"""
        await search_news(keyword="AI", ...)  # 첫 호출 (캐시 저장)

        start = time.perf_counter()
        await search_news(keyword="AI", ...)  # 두 번째 호출 (캐시 적중)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1

    async def test_concurrent_requests(self):
        """동시 요청 10개 이상 처리"""
        tasks = [search_news(keyword=f"test{i}", ...) for i in range(10)]
        results = await asyncio.gather(*tasks)
        assert all(r["success"] for r in results)
```

**파일**:
- `tests/test_performance.py` (신규)

---

### WF4B-3: 문서 최종화

**목표**: README.md 및 docs/ 업데이트

**파일**:
- `README.md` (업데이트)
- `docs/MCP_GUIDE.md` (업데이트)
- `docs/API_REFERENCE.md` (신규)

**내용**:
- [ ] 설치 가이드 최신화
- [ ] 환경변수 문서화
- [ ] API 사용 예시 추가
- [ ] 에러 코드 문서화

---

### WF4B-4: 캐시 TTL 검증

**목표**: AC10 충족 - 캐시 정책 검증

**관련 AC**:
- AC10: 검색 결과 캐시 TTL: 5분
- AC10: 기사 상세 캐시 TTL: 30분
- AC10: 트렌드/연관어 캐시 TTL: 10분
- AC10: 언론사/카테고리 목록 캐시 TTL: 24시간

**구현 내용**:
```python
# tests/test_cache.py
class TestAC10Caching:

    def test_search_cache_ttl(self):
        """검색 결과 캐시 TTL: 5분"""
        # 캐시 TTL 설정 확인
        assert cache.get_ttl("search_*") == 300

    def test_article_cache_ttl(self):
        """기사 상세 캐시 TTL: 30분"""
        assert cache.get_ttl("article_*") == 1800
```

**파일**:
- `tests/test_cache.py` (신규)
- `src/bigkinds_mcp/core/cache.py` (검증)

---

## Phase 5: Enhancement

> 우선순위: **Medium** | 의존성: Phase 4B 완료

### WF5A-1: keyword_comparison 프롬프트

**목표**: PRD PR4 구현 - 키워드 비교 분석 프롬프트

**관련 PRD**:
- PR4: `keyword_comparison` - keywords[], start_date, end_date

**구현 내용**:
```python
# src/bigkinds_mcp/prompts/analysis.py
@mcp.prompt()
def keyword_comparison(
    keywords: list[str],
    start_date: str,
    end_date: str,
) -> str:
    """여러 키워드의 뉴스 트렌드를 비교 분석합니다."""
    keywords_str = ", ".join(keywords)
    return f"""다음 키워드들의 뉴스 트렌드를 비교 분석해주세요:

키워드: {keywords_str}
기간: {start_date} ~ {end_date}

분석 항목:
1. 각 키워드별 기사 수 추이
2. 상대적 관심도 비교
3. 교차 언급 분석
4. 주요 이슈 시점 식별

get_keyword_trends 도구를 사용하여 각 키워드의 트렌드를 조회한 후,
비교 분석 결과를 표와 그래프로 정리해주세요."""
```

**파일**:
- `src/bigkinds_mcp/prompts/analysis.py` (수정)

---

### WF5B-1: 배치 검색 지원 (Future)

**목표**: 여러 키워드 동시 검색

**Status**: Future (M5)

---

### WF5B-2: 결과 내보내기 (Future)

**목표**: CSV/JSON 파일 내보내기

**Status**: Future (M5)

---

## Dependency Graph

```
┌──────────────────────────────────────────────────────────────┐
│                        Phase 4A                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ WF4A-1  │  │ WF4A-2  │  │ WF4A-3  │  │ WF4A-4  │         │
│  │파라미터 │  │에러코드 │  │재시도   │  │타임아웃 │         │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│       │            │            │            │               │
└───────┼────────────┼────────────┼────────────┼───────────────┘
        │            │            │            │
        └────────────┴─────┬──────┴────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                        Phase 4B                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ WF4B-1  │  │ WF4B-2  │  │ WF4B-3  │  │ WF4B-4  │         │
│  │AC 테스트│  │성능테스트│  │문서화   │  │캐시검증 │         │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│       │            │            │            │               │
└───────┼────────────┼────────────┼────────────┼───────────────┘
        │            │            │            │
        └────────────┴─────┬──────┴────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                        Phase 5                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │
│  │ WF5A-1  │  │ WF5B-1  │  │ WF5B-2  │                      │
│  │비교프롬│  │배치검색 │  │내보내기 │                      │
│  └─────────┘  └─────────┘  └─────────┘                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Task Checklist

### Phase 4A: Error Handling
- [ ] WF4A-1: 파라미터 유효성 검증
- [ ] WF4A-2: 에러 코드 표준화
- [ ] WF4A-3: 재시도 로직
- [ ] WF4A-4: 타임아웃 핸들링

### Phase 4B: Testing & Docs
- [ ] WF4B-1: AC 기반 통합 테스트
- [ ] WF4B-2: 성능 테스트
- [ ] WF4B-3: 문서 최종화
- [ ] WF4B-4: 캐시 TTL 검증

### Phase 5: Enhancement
- [ ] WF5A-1: keyword_comparison 프롬프트
- [ ] WF5B-1: 배치 검색 지원 (Future)
- [ ] WF5B-2: 결과 내보내기 (Future)

---

## Execution Order

1. **즉시 실행** (Phase 4A)
   - WF4A-1, WF4A-2 병렬 진행
   - WF4A-3, WF4A-4 병렬 진행

2. **Phase 4A 완료 후** (Phase 4B)
   - WF4B-1: AC 통합 테스트 (최우선)
   - WF4B-2, WF4B-3, WF4B-4 병렬 진행

3. **Phase 4B 완료 후** (Phase 5)
   - WF5A-1: keyword_comparison (선택)
   - WF5B-*: Future 작업으로 보류

---

## Related Documents

| Document | Path |
|----------|------|
| PRD | `docs/PRD.md` |
| Architecture v2 | `docs/MCP_ARCHITECTURE_V2.md` |
| CLAUDE.md | `CLAUDE.md` |
