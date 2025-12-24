# Implementation Workflow v4.0: Quality, Performance & Visualization

> PRD v3.0 구현을 위한 체계적 워크플로우

## 목차
1. [개요](#1-개요)
2. [Phase 1: High Priority 기능](#phase-1-high-priority-기능-1-2일)
3. [Phase 2: Medium Priority 기능](#phase-2-medium-priority-기능-2-3일)
4. [Phase 3: Integration & Testing](#phase-3-integration--testing-1-2일)
5. [Phase 4: Release](#phase-4-release-05일)
6. [Phase 5: Visualization (v3.0)](#phase-5-visualization-v30-1-2일)
7. [체크리스트](#전체-체크리스트)

---

## 1. 개요

### 1.1 목표
PRD v2.0의 9개 신규 User Stories (US13-US19)와 8개 Acceptance Criteria (AC11-AC18) 구현

### 1.2 원칙
- **Test-First**: 각 AC마다 테스트 먼저 작성
- **점진적 통합**: 작은 단위로 커밋 및 테스트
- **문서 우선**: 코드 전에 인터페이스 설계
- **성능 측정**: 변경 전후 벤치마크 비교

### 1.3 전제 조건
- ✅ v1.5.2 배포 완료
- ✅ 110/111 테스트 통과
- ✅ PRD v2.0 승인 완료

---

## Phase 1: High Priority 기능 (1-2일)

### 🎯 Task 1.1: 날짜 검증 강화 (AC12) - 2시간

#### 1.1.1 새 모듈 생성
```bash
# 파일 생성
touch src/bigkinds_mcp/validation/__init__.py
touch src/bigkinds_mcp/validation/date_validator.py
```

#### 1.1.2 DateValidator 클래스 구현
**파일**: `src/bigkinds_mcp/validation/date_validator.py`

```python
from datetime import datetime, date
from typing import Tuple
from ..models.errors import ErrorCode, error_response

MIN_DATE = "1990-01-01"  # BigKinds 데이터 시작일

class DateValidator:
    """날짜 검증 로직."""

    @staticmethod
    def validate_date_range(
        start_date: str,
        end_date: str
    ) -> dict | None:
        """
        날짜 범위 검증.

        Returns:
            None: 검증 성공
            dict: 에러 응답
        """
        # 1. 형식 검증 (YYYY-MM-DD)
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return error_response(
                ErrorCode.INVALID_DATE_FORMAT,
                "날짜 형식이 올바르지 않습니다",
                details={
                    "format": "YYYY-MM-DD",
                    "example": "2025-12-16",
                    "solution": "날짜를 YYYY-MM-DD 형식으로 입력하세요"
                }
            )

        # 2. 미래 날짜 검증
        today = date.today()
        if start > today or end > today:
            return error_response(
                ErrorCode.INVALID_DATE_RANGE,
                "미래 날짜는 검색할 수 없습니다",
                details={
                    "today": today.isoformat(),
                    "solution": "오늘 날짜 이전으로 검색하세요"
                }
            )

        # 3. 최소 날짜 검증 (1990-01-01)
        min_date = datetime.strptime(MIN_DATE, "%Y-%m-%d").date()
        if start < min_date or end < min_date:
            return error_response(
                ErrorCode.DATE_OUT_OF_RANGE,
                f"{MIN_DATE} 이전 데이터는 검색할 수 없습니다",
                details={
                    "min_date": MIN_DATE,
                    "max_date": today.isoformat(),
                    "solution": f"{MIN_DATE} 이후로 검색하세요"
                }
            )

        # 4. 날짜 순서 검증
        if end < start:
            return error_response(
                ErrorCode.INVALID_DATE_ORDER,
                "종료일이 시작일보다 빠릅니다",
                details={
                    "start_date": start_date,
                    "end_date": end_date,
                    "solution": "시작일 ≤ 종료일로 입력하세요"
                }
            )

        return None  # 검증 성공
```

#### 1.1.3 ErrorCode 추가
**파일**: `src/bigkinds_mcp/models/errors.py`

```python
class ErrorCode:
    # 기존 코드...

    # 날짜 검증 (신규)
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    DATE_OUT_OF_RANGE = "DATE_OUT_OF_RANGE"
    INVALID_DATE_ORDER = "INVALID_DATE_ORDER"
```

#### 1.1.4 search_news에 검증 적용
**파일**: `src/bigkinds_mcp/tools/search.py`

```python
from ..validation.date_validator import DateValidator

async def search_news(
    keyword: str,
    start_date: str,
    end_date: str,
    # ... 기존 파라미터
) -> dict:
    """뉴스 검색."""
    # 날짜 검증
    validation_error = DateValidator.validate_date_range(start_date, end_date)
    if validation_error:
        return validation_error

    # 기존 로직...
```

#### 1.1.5 테스트 작성
**파일**: `tests/unit/test_date_validator.py`

```python
import pytest
from datetime import date, timedelta
from bigkinds_mcp.validation.date_validator import DateValidator
from bigkinds_mcp.models.errors import ErrorCode

class TestDateValidator:
    """DateValidator 테스트."""

    def test_valid_date_range(self):
        """유효한 날짜 범위."""
        result = DateValidator.validate_date_range("2025-12-01", "2025-12-15")
        assert result is None

    def test_future_date_rejected(self):
        """미래 날짜 거부."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = DateValidator.validate_date_range(tomorrow, tomorrow)
        assert result["error"] == ErrorCode.INVALID_DATE_RANGE
        assert "미래 날짜" in result["message"]

    def test_date_before_1990_rejected(self):
        """1990년 이전 날짜 거부."""
        result = DateValidator.validate_date_range("1989-12-31", "1990-01-01")
        assert result["error"] == ErrorCode.DATE_OUT_OF_RANGE
        assert "1990-01-01" in result["message"]

    def test_end_before_start_rejected(self):
        """종료일 < 시작일 거부."""
        result = DateValidator.validate_date_range("2025-12-15", "2025-12-01")
        assert result["error"] == ErrorCode.INVALID_DATE_ORDER

    def test_invalid_format_rejected(self):
        """잘못된 형식 거부."""
        result = DateValidator.validate_date_range("2025/12/01", "2025-12-15")
        assert result["error"] == ErrorCode.INVALID_DATE_FORMAT
```

#### 1.1.6 통합 테스트
**파일**: `tests/integration/test_date_validation_integration.py`

```python
@pytest.mark.asyncio
async def test_search_news_rejects_future_date(setup_tools):
    """search_news가 미래 날짜를 거부하는지 확인."""
    from bigkinds_mcp.tools.search import search_news

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    result = await search_news(
        keyword="테스트",
        start_date=tomorrow,
        end_date=tomorrow
    )

    assert result["error"] == "INVALID_DATE_RANGE"
    assert "미래 날짜" in result["message"]
```

#### 1.1.7 체크리스트
- [ ] DateValidator 클래스 구현
- [ ] ErrorCode 추가 (4개)
- [ ] search_news에 검증 로직 통합
- [ ] get_article_count에 검증 로직 통합
- [ ] export_all_articles에 검증 로직 통합
- [ ] 단위 테스트 5개 작성 및 통과
- [ ] 통합 테스트 작성 및 통과
- [ ] 커밋: `feat(validation): 날짜 검증 강화 (AC12)`

---

### 🎯 Task 1.2: API 스키마 검증 (AC13) - 3시간

#### 1.2.1 Pydantic Strict 모드 적용
**파일**: `src/bigkinds_mcp/models/schemas.py`

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class StrictBaseModel(BaseModel):
    """Strict 검증이 적용된 Base Model."""
    model_config = ConfigDict(strict=True, extra='forbid')

class Article(StrictBaseModel):
    """기사 정보 (Strict 모드)."""
    news_id: str
    title: str
    summary: str
    publisher: str
    category: str
    news_date: str  # YYYY-MM-DD
    url: str

class SearchResult(StrictBaseModel):
    """검색 결과 (Strict 모드)."""
    success: bool
    total_count: int
    page: int
    page_size: int
    total_pages: int
    articles: List[Article]
```

#### 1.2.2 스키마 검증 래퍼 함수
**파일**: `src/bigkinds_mcp/core/schema_validator.py`

```python
import logging
from pydantic import ValidationError
from typing import Type, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')

def validate_api_response(
    data: dict,
    schema: Type[T],
    context: str = ""
) -> T:
    """
    API 응답을 Pydantic 스키마로 검증.

    Args:
        data: 검증할 데이터
        schema: Pydantic 스키마 클래스
        context: 에러 로그용 컨텍스트

    Returns:
        검증된 스키마 인스턴스

    Raises:
        ValidationError: 스키마 불일치 시
    """
    try:
        return schema.model_validate(data)
    except ValidationError as e:
        logger.error(
            f"[Schema Validation Failed] {context}\n"
            f"Errors: {e.errors()}\n"
            f"Raw data: {data}"
        )
        raise
```

#### 1.2.3 async_client에 검증 적용
**파일**: `src/bigkinds_mcp/core/async_client.py`

```python
from .schema_validator import validate_api_response
from ..models.schemas import SearchResult, Article

async def search(self, request: SearchRequest) -> SearchResult:
    """뉴스 검색 (스키마 검증 적용)."""
    response = await self._client.search(request)

    # 스키마 검증
    try:
        validated = validate_api_response(
            response.model_dump(),
            SearchResult,
            context=f"search(keyword={request.keyword})"
        )
        return validated
    except ValidationError:
        # 검증 실패 시 에러 응답 반환
        return error_response(
            ErrorCode.SCHEMA_VALIDATION_FAILED,
            "API 응답이 예상과 다릅니다",
            details={
                "expected_fields": SearchResult.model_fields.keys(),
                "solution": "개발자에게 문의하세요 (API 스키마 변경 가능성)"
            }
        )
```

#### 1.2.4 테스트 작성
**파일**: `tests/unit/test_schema_validator.py`

```python
import pytest
from pydantic import ValidationError
from bigkinds_mcp.core.schema_validator import validate_api_response
from bigkinds_mcp.models.schemas import Article

class TestSchemaValidator:
    """스키마 검증 테스트."""

    def test_valid_data_passes(self):
        """유효한 데이터 통과."""
        data = {
            "news_id": "123",
            "title": "테스트",
            "summary": "요약",
            "publisher": "경향신문",
            "category": "정치",
            "news_date": "2025-12-16",
            "url": "https://example.com"
        }
        result = validate_api_response(data, Article)
        assert result.news_id == "123"

    def test_missing_required_field_raises(self):
        """필수 필드 누락 시 에러."""
        data = {
            "news_id": "123",
            # title 누락
            "summary": "요약"
        }
        with pytest.raises(ValidationError):
            validate_api_response(data, Article)

    def test_wrong_type_raises(self):
        """타입 불일치 시 에러."""
        data = {
            "news_id": 123,  # str이어야 하는데 int
            "title": "테스트",
            # ...
        }
        with pytest.raises(ValidationError):
            validate_api_response(data, Article)
```

#### 1.2.5 체크리스트
- [ ] StrictBaseModel 구현
- [ ] 기존 모델에 Strict 모드 적용
- [ ] schema_validator 모듈 생성
- [ ] async_client에 검증 로직 통합
- [ ] 단위 테스트 작성 및 통과
- [ ] 기존 테스트 110개 모두 통과 확인
- [ ] 커밋: `feat(validation): API 스키마 strict 검증 (AC13)`

---

### 🎯 Task 1.3: 진행률 피드백 (AC14) - 3시간

#### 1.3.1 Progress Tracker 구현
**파일**: `src/bigkinds_mcp/core/progress.py`

```python
import logging
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class ProgressTracker:
    """대용량 작업 진행률 추적."""

    def __init__(
        self,
        total: int,
        description: str = "Processing",
        threshold: int = 5000,  # 진행률 표시 최소 건수
        interval: int = 10,     # 진행률 업데이트 주기 (%)
        callback: Optional[Callable[[int, int], None]] = None
    ):
        self.total = total
        self.description = description
        self.threshold = threshold
        self.interval = interval
        self.callback = callback
        self.current = 0
        self.start_time = datetime.now()
        self.last_reported = 0

        self.enabled = total >= threshold

    def update(self, amount: int = 1):
        """진행률 업데이트."""
        if not self.enabled:
            return

        self.current += amount
        progress_pct = (self.current / self.total) * 100

        # interval 단위로만 로깅
        if progress_pct >= self.last_reported + self.interval:
            self._log_progress(progress_pct)
            self.last_reported = int(progress_pct / self.interval) * self.interval

            if self.callback:
                self.callback(self.current, self.total)

    def _log_progress(self, progress_pct: float):
        """진행률 로깅."""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # 예상 완료 시간 계산
        if progress_pct > 0:
            eta = (elapsed / progress_pct) * (100 - progress_pct)
        else:
            eta = 0

        logger.info(
            f"[진행률] {self.description}: "
            f"{self.current}/{self.total} ({progress_pct:.1f}%) - "
            f"예상 완료: {eta:.0f}초"
        )
```

#### 1.3.2 export_all_articles에 적용
**파일**: `src/bigkinds_mcp/tools/analysis.py`

```python
from ..core.progress import ProgressTracker

async def export_all_articles(
    # ... 기존 파라미터
) -> dict:
    """전체 기사 내보내기 (진행률 추적)."""

    # 1. 총 기사 수 확인
    count_result = await get_article_count(keyword, start_date, end_date, "total", providers, categories)
    total_count = count_result["total_count"]

    # 2. Progress Tracker 생성
    progress = ProgressTracker(
        total=min(total_count, max_articles),
        description=f"'{keyword}' 기사 내보내기",
        threshold=5000
    )

    # 3. 페이지별 검색 및 진행률 업데이트
    all_articles = []
    page = 1

    while len(all_articles) < max_articles:
        result = await search_news(
            keyword, start_date, end_date, page, page_size,
            providers, categories, sort_by
        )

        if not result.get("articles"):
            break

        all_articles.extend(result["articles"])
        progress.update(len(result["articles"]))  # 진행률 업데이트
        page += 1

    # 4. 파일 저장 및 반환...
```

#### 1.3.3 MCP 응답에 진행률 추가 (선택사항)
**파일**: `src/bigkinds_mcp/tools/analysis.py`

```python
# MCP 스트리밍 응답 예시 (향후 구현)
async def export_all_articles_streaming(...):
    """진행률을 실시간으로 Claude에게 전달."""

    def progress_callback(current: int, total: int):
        # MCP 프로토콜로 진행률 전송
        yield {
            "type": "progress",
            "current": current,
            "total": total,
            "percentage": (current / total) * 100
        }

    progress = ProgressTracker(
        total=total_count,
        callback=progress_callback
    )
    # ...
```

#### 1.3.4 테스트
**파일**: `tests/unit/test_progress_tracker.py`

```python
from bigkinds_mcp.core.progress import ProgressTracker

class TestProgressTracker:
    """Progress Tracker 테스트."""

    def test_small_task_disabled(self):
        """5000건 미만 작업은 진행률 비활성화."""
        tracker = ProgressTracker(total=100, threshold=5000)
        assert tracker.enabled is False

    def test_large_task_enabled(self):
        """5000건 이상 작업은 진행률 활성화."""
        tracker = ProgressTracker(total=10000, threshold=5000)
        assert tracker.enabled is True

    def test_callback_invoked(self):
        """콜백 함수 호출 확인."""
        called = []

        def callback(current, total):
            called.append((current, total))

        tracker = ProgressTracker(total=100, threshold=0, interval=25, callback=callback)
        tracker.update(25)  # 25%
        tracker.update(25)  # 50%

        assert len(called) == 2
        assert called[0] == (25, 100)
```

#### 1.3.5 체크리스트
- [ ] ProgressTracker 클래스 구현
- [ ] export_all_articles에 진행률 적용
- [ ] 로깅 형식 검증 (예: `[진행률] 1000/10000 (10%) - 예상 완료: 30초`)
- [ ] 단위 테스트 작성 및 통과
- [ ] 실제 10K 건 export 테스트
- [ ] 커밋: `feat(progress): 대용량 작업 진행률 피드백 (AC14)`

---

### 🎯 Task 1.4: 병렬 API 호출 (AC11) - 4시간

#### 1.4.1 Rate Limiter 구현
**파일**: `src/bigkinds_mcp/core/rate_limiter.py`

```python
import asyncio
from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    """Rate limiting for API calls."""

    def __init__(self, max_requests: int = 3, period: float = 1.0):
        """
        Args:
            max_requests: 기간당 최대 요청 수
            period: 제한 기간 (초)
        """
        self.max_requests = max_requests
        self.period = period
        self.requests = deque()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """요청 허가 획득 (필요 시 대기)."""
        async with self.lock:
            now = datetime.now()

            # 만료된 요청 제거
            while self.requests and self.requests[0] < now - timedelta(seconds=self.period):
                self.requests.popleft()

            # Rate limit 초과 시 대기
            if len(self.requests) >= self.max_requests:
                sleep_time = (self.requests[0] + timedelta(seconds=self.period) - now).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.requests.popleft()

            # 요청 기록
            self.requests.append(now)
```

#### 1.4.2 병렬 검색 헬퍼 함수
**파일**: `src/bigkinds_mcp/tools/search.py`

```python
from ..core.rate_limiter import RateLimiter

# 전역 rate limiter (1초당 3 요청)
_rate_limiter = RateLimiter(max_requests=3, period=1.0)

async def search_news_parallel(
    queries: List[dict],
    max_concurrent: int = 5
) -> List[dict]:
    """
    여러 검색 쿼리를 병렬 실행.

    Args:
        queries: 검색 파라미터 리스트 [{"keyword": "AI", "start_date": "2025-12-01", ...}, ...]
        max_concurrent: 최대 동시 실행 수 (기본 5)

    Returns:
        검색 결과 리스트

    Example:
        >>> results = await search_news_parallel([
        ...     {"keyword": "AI", "start_date": "2025-12-01", "end_date": "2025-12-15"},
        ...     {"keyword": "블록체인", "start_date": "2025-12-01", "end_date": "2025-12-15"},
        ... ])
    """
    async def _search_with_rate_limit(query: dict) -> dict:
        """Rate limiting 적용하여 검색."""
        await _rate_limiter.acquire()
        return await search_news(**query)

    # Semaphore로 동시 실행 수 제한
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _bounded_search(query: dict) -> dict:
        async with semaphore:
            return await _search_with_rate_limit(query)

    # 병렬 실행
    tasks = [_bounded_search(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 예외 처리
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append({
                "error": "PARALLEL_SEARCH_FAILED",
                "message": f"쿼리 {i+1}번 실패: {str(result)}",
                "query": queries[i]
            })
        else:
            final_results.append(result)

    return final_results
```

#### 1.4.3 MCP Tool 등록
**파일**: `src/bigkinds_mcp/tools/search.py`

```python
@mcp.tool()
async def search_news_batch(
    queries: List[dict]
) -> dict:
    """
    여러 뉴스 검색을 동시에 실행합니다.

    Args:
        queries: 검색 조건 목록 (최대 5개)

    Returns:
        각 검색 결과 목록

    Example:
        queries = [
            {"keyword": "AI", "start_date": "2025-12-01", "end_date": "2025-12-15"},
            {"keyword": "블록체인", "start_date": "2025-12-01", "end_date": "2025-12-15"}
        ]
    """
    if len(queries) > 5:
        return error_response(
            ErrorCode.TOO_MANY_REQUESTS,
            "한 번에 최대 5개 검색만 가능합니다",
            details={"max_queries": 5, "provided": len(queries)}
        )

    results = await search_news_parallel(queries)

    return {
        "success": True,
        "total_queries": len(queries),
        "results": results,
        "successful": sum(1 for r in results if "error" not in r),
        "failed": sum(1 for r in results if "error" in r)
    }
```

#### 1.4.4 테스트
**파일**: `tests/integration/test_parallel_search.py`

```python
@pytest.mark.asyncio
async def test_parallel_search_basic(setup_tools):
    """기본 병렬 검색 테스트."""
    from bigkinds_mcp.tools.search import search_news_parallel

    queries = [
        {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"}
    ]

    results = await search_news_parallel(queries)

    assert len(results) == 2
    assert all("total_count" in r for r in results if "error" not in r)

@pytest.mark.asyncio
async def test_parallel_search_rate_limiting():
    """Rate limiting 확인."""
    import time

    queries = [{"keyword": f"test{i}", "start_date": "2025-12-10", "end_date": "2025-12-15"}
               for i in range(10)]

    start = time.time()
    results = await search_news_parallel(queries)
    elapsed = time.time() - start

    # 10개 요청, 1초당 3개 → 최소 3초 소요
    assert elapsed >= 3.0
```

#### 1.4.5 성능 벤치마크
**파일**: `tests/benchmark/test_parallel_performance.py`

```python
@pytest.mark.benchmark
async def test_parallel_vs_sequential():
    """병렬 vs 순차 실행 성능 비교."""
    import time

    queries = [
        {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        {"keyword": "메타버스", "start_date": "2025-12-10", "end_date": "2025-12-15"}
    ]

    # 순차 실행
    start = time.time()
    for q in queries:
        await search_news(**q)
    sequential_time = time.time() - start

    # 병렬 실행
    start = time.time()
    await search_news_parallel(queries)
    parallel_time = time.time() - start

    print(f"순차: {sequential_time:.2f}s, 병렬: {parallel_time:.2f}s")
    assert parallel_time < sequential_time * 0.6  # 40% 이상 빨라야 함
```

#### 1.4.6 체크리스트
- [ ] RateLimiter 클래스 구현
- [ ] search_news_parallel 함수 구현
- [ ] search_news_batch MCP Tool 등록
- [ ] Rate limiting 단위 테스트
- [ ] 병렬 검색 통합 테스트
- [ ] 성능 벤치마크 (2배 이상 속도 향상)
- [ ] 문서 업데이트 (API_REFERENCE.md)
- [ ] 커밋: `feat(search): 병렬 API 호출 지원 (AC11)`

---

## Phase 2: Medium Priority 기능 (2-3일)

### 🎯 Task 2.1: 에러 메시지 한글화 (AC15) - 4시간

#### 2.1.1 한글 에러 메시지 매핑
**파일**: `src/bigkinds_mcp/models/errors_kr.py`

```python
"""한국어 에러 메시지 및 해결 방법."""

from typing import Dict, Optional

ERROR_MESSAGES_KR: Dict[str, dict] = {
    "INVALID_DATE_FORMAT": {
        "message": "날짜 형식이 올바르지 않습니다",
        "solution": "YYYY-MM-DD 형식으로 입력하세요 (예: 2025-12-16)",
        "docs": "https://github.com/seolcoding/bigkinds-mcp#날짜-형식"
    },
    "INVALID_DATE_RANGE": {
        "message": "미래 날짜는 검색할 수 없습니다",
        "solution": "오늘 날짜 이하로 검색하세요",
    },
    "DATE_OUT_OF_RANGE": {
        "message": "검색 가능한 날짜 범위를 벗어났습니다",
        "solution": "1990-01-01부터 오늘까지만 검색 가능합니다",
    },
    "INVALID_DATE_ORDER": {
        "message": "종료일이 시작일보다 빠릅니다",
        "solution": "시작일 ≤ 종료일로 입력하세요",
    },
    "KEYWORD_REQUIRED": {
        "message": "검색 키워드를 입력해주세요",
        "solution": "최소 1자 이상의 키워드가 필요합니다",
    },
    "RATE_LIMIT_EXCEEDED": {
        "message": "요청이 너무 많습니다",
        "solution": "잠시 후 다시 시도하세요 (초당 최대 3회)",
    },
    "API_TIMEOUT": {
        "message": "BigKinds API 응답 시간 초과",
        "solution": "네트워크 연결을 확인하거나 잠시 후 재시도하세요",
    },
    "AUTHENTICATION_FAILED": {
        "message": "BigKinds 로그인에 실패했습니다",
        "solution": "BIGKINDS_USER_ID, BIGKINDS_USER_PASSWORD 환경변수를 확인하세요",
        "docs": "https://github.com/seolcoding/bigkinds-mcp#환경변수-설정"
    },
    # ... 모든 에러 코드 추가
}

def get_error_message_kr(
    error_code: str,
    details: Optional[Dict] = None
) -> dict:
    """한글 에러 메시지 반환."""
    error_info = ERROR_MESSAGES_KR.get(error_code, {
        "message": "알 수 없는 오류가 발생했습니다",
        "solution": "개발자에게 문의하세요"
    })

    result = {
        "error": error_code,
        "message": error_info["message"],
        "solution": error_info["solution"]
    }

    if "docs" in error_info:
        result["docs"] = error_info["docs"]

    if details:
        result["details"] = details

    return result
```

#### 2.1.2 기존 error_response 함수 수정
**파일**: `src/bigkinds_mcp/models/errors.py`

```python
from .errors_kr import get_error_message_kr

def error_response(
    error_code: str,
    message: str = "",  # 더 이상 필수 아님
    details: dict | None = None
) -> dict:
    """에러 응답 생성 (한글 자동 적용)."""
    return get_error_message_kr(error_code, details)
```

#### 2.1.3 기존 코드 마이그레이션
- 모든 `error_response()` 호출에서 `message` 파라미터 제거
- 한글 메시지는 errors_kr.py에서 자동 로드

#### 2.1.4 테스트
**파일**: `tests/unit/test_errors_kr.py`

```python
from bigkinds_mcp.models.errors_kr import get_error_message_kr

class TestKoreanErrorMessages:
    """한글 에러 메시지 테스트."""

    def test_all_error_codes_have_korean_message(self):
        """모든 ErrorCode가 한글 메시지를 가지는지 확인."""
        from bigkinds_mcp.models.errors import ErrorCode

        for attr in dir(ErrorCode):
            if not attr.startswith("_"):
                code = getattr(ErrorCode, attr)
                msg = get_error_message_kr(code)
                assert "message" in msg
                assert "solution" in msg

    def test_error_message_contains_solution(self):
        """에러 메시지에 해결 방법 포함."""
        msg = get_error_message_kr("INVALID_DATE_FORMAT")
        assert "YYYY-MM-DD" in msg["solution"]
```

#### 2.1.5 체크리스트
- [ ] errors_kr.py 생성 및 모든 에러 코드 매핑
- [ ] error_response 함수 수정
- [ ] 기존 코드에서 message 파라미터 제거
- [ ] 단위 테스트 작성 및 통과
- [ ] 문서 업데이트 (모든 에러 코드 + 한글 설명)
- [ ] 커밋: `feat(errors): 에러 메시지 한글화 (AC15)`

---

### 🎯 Task 2.2: Circuit Breaker 패턴 (AC16) - 5시간

#### 2.2.1 Circuit Breaker 구현
**파일**: `src/bigkinds_mcp/core/circuit_breaker.py`

```python
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
import asyncio

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit Breaker 상태."""
    CLOSED = "closed"      # 정상
    OPEN = "open"          # 차단
    HALF_OPEN = "half_open"  # 테스트

class CircuitBreaker:
    """Circuit Breaker 패턴 구현."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
        name: str = "default"
    ):
        """
        Args:
            failure_threshold: 연속 실패 임계값
            recovery_timeout: 복구 대기 시간(초)
            name: Circuit 이름 (로깅용)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Circuit Breaker를 통해 함수 호출.

        Returns:
            함수 실행 결과

        Raises:
            CircuitBreakerOpenError: Circuit이 open 상태일 때
        """
        async with self.lock:
            # Circuit 상태 확인
            self._check_state()

            if self.state == CircuitState.OPEN:
                logger.warning(f"[CircuitBreaker:{self.name}] Circuit is OPEN - Request blocked")
                raise CircuitBreakerOpenError(
                    f"Circuit '{self.name}'이 차단 상태입니다. "
                    f"{self.recovery_timeout}초 후 재시도하세요."
                )

        # 함수 실행
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    def _check_state(self):
        """현재 상태 확인 및 업데이트."""
        if self.state == CircuitState.OPEN:
            # recovery_timeout 경과 시 HALF_OPEN으로 전환
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self._change_state(CircuitState.HALF_OPEN)

    async def _on_success(self):
        """호출 성공 시."""
        if self.state == CircuitState.HALF_OPEN:
            # HALF_OPEN에서 성공 → CLOSED로 복구
            self._change_state(CircuitState.CLOSED)
            self.failure_count = 0

    async def _on_failure(self):
        """호출 실패 시."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # HALF_OPEN에서 실패 → 다시 OPEN
            self._change_state(CircuitState.OPEN)
        elif self.failure_count >= self.failure_threshold:
            # CLOSED에서 임계값 초과 → OPEN
            self._change_state(CircuitState.OPEN)

    def _change_state(self, new_state: CircuitState):
        """상태 전환 및 로깅."""
        old_state = self.state
        self.state = new_state
        logger.info(
            f"[CircuitBreaker:{self.name}] State changed: {old_state.value} → {new_state.value}"
        )

class CircuitBreakerOpenError(Exception):
    """Circuit이 open 상태일 때 발생하는 에러."""
    pass
```

#### 2.2.2 async_client에 Circuit Breaker 적용
**파일**: `src/bigkinds_mcp/core/async_client.py`

```python
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

class AsyncBigKindsClient:
    """비동기 BigKinds 클라이언트 (Circuit Breaker 적용)."""

    def __init__(self):
        # 기존 초기화...

        # Circuit Breaker 생성
        self.search_circuit = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            name="search_api"
        )

    async def search(self, request: SearchRequest) -> SearchResult:
        """뉴스 검색 (Circuit Breaker 적용)."""
        try:
            return await self.search_circuit.call(
                self._search_internal,
                request
            )
        except CircuitBreakerOpenError as e:
            # Circuit open 시 캐시 데이터 반환 시도
            cache_key = f"search_{request.keyword}_{request.start_date}_{request.end_date}"
            cached = self._cache.get(cache_key)

            if cached:
                logger.info(f"[CircuitBreaker] Returning cached data for {cache_key}")
                return cached
            else:
                # 캐시도 없으면 에러 반환
                return error_response(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    details={
                        "reason": "BigKinds API가 일시적으로 사용 불가합니다",
                        "retry_after": 30
                    }
                )

    async def _search_internal(self, request: SearchRequest) -> SearchResult:
        """실제 검색 로직 (Circuit Breaker에서 호출)."""
        # 기존 search() 로직을 여기로 이동
        ...
```

#### 2.2.3 테스트
**파일**: `tests/unit/test_circuit_breaker.py`

```python
import pytest
import asyncio
from bigkinds_mcp.core.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenError

class TestCircuitBreaker:
    """Circuit Breaker 테스트."""

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        """임계값 초과 시 OPEN으로 전환."""
        circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        async def failing_func():
            raise Exception("Fail")

        # 3번 실패
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit.call(failing_func)

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_blocks_requests_when_open(self):
        """OPEN 상태일 때 요청 차단."""
        circuit = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        async def failing_func():
            raise Exception("Fail")

        # 1번 실패 → OPEN
        with pytest.raises(Exception):
            await circuit.call(failing_func)

        # OPEN 상태에서 즉시 차단
        with pytest.raises(CircuitBreakerOpenError):
            await circuit.call(failing_func)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self):
        """timeout 후 HALF_OPEN으로 전환."""
        circuit = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        async def failing_func():
            raise Exception("Fail")

        # OPEN으로 전환
        with pytest.raises(Exception):
            await circuit.call(failing_func)

        # 1초 대기
        await asyncio.sleep(1.1)

        # HALF_OPEN으로 전환되어 테스트 요청 허용
        async def success_func():
            return "OK"

        result = await circuit.call(success_func)
        assert result == "OK"
        assert circuit.state == CircuitState.CLOSED  # 성공 시 CLOSED로 복구
```

#### 2.2.4 체크리스트
- [ ] CircuitBreaker 클래스 구현
- [ ] CircuitBreakerOpenError 정의
- [ ] async_client에 Circuit Breaker 적용
- [ ] 캐시 fallback 로직 추가
- [ ] 단위 테스트 작성 및 통과
- [ ] 통합 테스트 (실제 API 장애 시뮬레이션)
- [ ] 커밋: `feat(reliability): Circuit Breaker 패턴 적용 (AC16)`

---

### 🎯 Task 2.3: 재시도 전략 고도화 (AC17) - 2시간

#### 2.3.1 기존 retry_async 개선
**파일**: `src/bigkinds_mcp/core/async_client.py`

```python
import random

def retry_async(
    max_retries: int = 3,
    base_delay: float = 1.0,
    jitter: bool = True
):
    """
    재시도 데코레이터 (개선 버전).

    개선사항:
    - 5xx 에러만 재시도, 4xx는 즉시 실패
    - jitter 추가 (0~500ms 랜덤 대기)
    - 재시도 횟수 로깅
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    # 4xx 에러는 재시도 안 함
                    if 400 <= e.response.status_code < 500:
                        logger.warning(f"[Retry] Client error {e.response.status_code} - No retry")
                        raise

                    # 5xx 에러만 재시도
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)

                        # Jitter 추가 (0~500ms)
                        if jitter:
                            delay += random.uniform(0, 0.5)

                        logger.info(
                            f"[Retry] Attempt {attempt + 1}/{max_retries} - "
                            f"Waiting {delay:.1f}s (status: {e.response.status_code})"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"[Retry] Max retries exceeded for {func.__name__}")
                        raise
                except Exception as e:
                    # 기타 예외도 재시도
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        if jitter:
                            delay += random.uniform(0, 0.5)

                        logger.info(f"[Retry] Attempt {attempt + 1}/{max_retries} - Waiting {delay:.1f}s")
                        await asyncio.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator
```

#### 2.3.2 테스트
**파일**: `tests/unit/test_retry_strategy.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
import httpx

@pytest.mark.asyncio
async def test_retry_on_5xx_errors():
    """5xx 에러 시 재시도."""
    from bigkinds_mcp.core.async_client import retry_async

    call_count = 0

    @retry_async(max_retries=2, base_delay=0.1, jitter=False)
    async def failing_func():
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            response = httpx.Response(500)
            raise httpx.HTTPStatusError("Server error", request=None, response=response)
        return "Success"

    result = await failing_func()
    assert result == "Success"
    assert call_count == 3  # 2번 재시도 + 1번 성공

@pytest.mark.asyncio
async def test_no_retry_on_4xx_errors():
    """4xx 에러 시 재시도 안 함."""
    from bigkinds_mcp.core.async_client import retry_async

    call_count = 0

    @retry_async(max_retries=2, base_delay=0.1)
    async def failing_func():
        nonlocal call_count
        call_count += 1

        response = httpx.Response(404)
        raise httpx.HTTPStatusError("Not found", request=None, response=response)

    with pytest.raises(httpx.HTTPStatusError):
        await failing_func()

    assert call_count == 1  # 재시도 안 함
```

#### 2.3.3 체크리스트
- [ ] retry_async 함수 개선
- [ ] 4xx/5xx 에러 분리 처리
- [ ] jitter 추가
- [ ] 재시도 로깅 추가
- [ ] 단위 테스트 작성 및 통과
- [ ] 커밋: `feat(reliability): 재시도 전략 고도화 (AC17)`

---

### 🎯 Task 2.4: Playwright 통합 테스트 (AC18) - 6시간

#### 2.4.1 Playwright 설정
**파일**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
markers = [
    "e2e: End-to-end tests",
    "playwright: Playwright browser tests",
    "benchmark: Performance benchmarks"
]

[project.optional-dependencies]
playwright = [
    "pytest-playwright>=0.5.0",
    "playwright>=1.40.0"
]
```

#### 2.4.2 Playwright 테스트 작성
**파일**: `tests/e2e_playwright/test_bigkinds_search_flow.py`

```python
import pytest
from playwright.async_api import async_playwright, Page

@pytest.mark.playwright
@pytest.mark.asyncio
async def test_bigkinds_search_workflow():
    """BigKinds 검색 워크플로우 E2E 테스트."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. BigKinds 메인 페이지 접속
        await page.goto("https://www.bigkinds.or.kr")
        await page.wait_for_load_state("networkidle")

        # 2. 검색어 입력
        await page.fill("input[name='searchKey']", "인공지능")
        await page.click("button[type='submit']")

        # 3. 검색 결과 확인
        await page.wait_for_selector(".news-list")
        articles = await page.query_selector_all(".news-item")
        assert len(articles) > 0

        # 4. 세션 쿠키 확인
        cookies = await page.context.cookies()
        session_cookie = next((c for c in cookies if "JSESSIONID" in c["name"]), None)
        assert session_cookie is not None

        await browser.close()

@pytest.mark.playwright
@pytest.mark.asyncio
async def test_network_analysis_api_via_browser():
    """네트워크 분석 API 브라우저 호출 검증."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 네트워크 요청 모니터링
        network_responses = []

        def handle_response(response):
            if "getNetworkDataAnalysis" in response.url:
                network_responses.append(response)

        page.on("response", handle_response)

        # BigKinds 접속 및 네트워크 분석 실행
        await page.goto("https://www.bigkinds.or.kr")
        # ... (네트워크 분석 버튼 클릭 등)

        # 네트워크 분석 API 호출 확인
        await page.wait_for_timeout(5000)

        if network_responses:
            response = network_responses[0]
            print(f"Network Analysis API Status: {response.status}")
            print(f"Response Headers: {response.headers}")

            # API 성공 시 로직 복원 가능성 검토
            if response.status == 200:
                data = await response.json()
                print(f"Network Analysis Data: {data}")

        await browser.close()
```

#### 2.4.3 Playwright MCP 통합 (선택사항)
**파일**: `tests/e2e_playwright/test_with_playwright_mcp.py`

```python
@pytest.mark.playwright
@pytest.mark.asyncio
async def test_bigkinds_with_playwright_mcp():
    """Playwright MCP를 활용한 BigKinds 테스트."""
    # Playwright MCP 도구 사용
    # (실제 구현은 Playwright MCP 문서 참조)
    pass
```

#### 2.4.4 Visual Regression 테스트 (선택사항)
**파일**: `tests/e2e_playwright/test_visual_regression.py`

```python
@pytest.mark.playwright
@pytest.mark.asyncio
async def test_search_results_visual():
    """검색 결과 페이지 visual regression 테스트."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto("https://www.bigkinds.or.kr")
        await page.fill("input[name='searchKey']", "AI")
        await page.click("button[type='submit']")
        await page.wait_for_selector(".news-list")

        # 스크린샷 저장
        await page.screenshot(path="tests/screenshots/search_results.png")

        # (선택사항) Percy 등 visual testing 도구 연동
        await browser.close()
```

#### 2.4.5 체크리스트
- [ ] Playwright 의존성 추가
- [ ] 검색 워크플로우 E2E 테스트
- [ ] 네트워크 분석 API 브라우저 호출 테스트
- [ ] 세션 쿠키 획득 로직 검증
- [ ] Playwright MCP 통합 (선택사항)
- [ ] Visual regression 테스트 (선택사항)
- [ ] GitHub Actions에 Playwright 테스트 추가
- [ ] 커밋: `feat(test): Playwright 통합 테스트 추가 (AC18)`

---

## Phase 3: Integration & Testing (1-2일)

### 🎯 Task 3.1: 전체 테스트 통합 - 4시간

#### 3.1.1 테스트 마커 정리
**파일**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests (live API)",
    "playwright: Playwright browser tests",
    "benchmark: Performance benchmarks",
    "slow: Slow-running tests (>5s)"
]
```

#### 3.1.2 테스트 스위트 구성
```bash
# 빠른 테스트 (CI용)
uv run pytest -m "not slow and not playwright" --maxfail=3

# 전체 테스트 (release 전)
uv run pytest --cov=src/bigkinds_mcp --cov-report=html

# 성능 테스트만
uv run pytest -m benchmark

# Playwright 테스트만
uv run pytest -m playwright
```

#### 3.1.3 커버리지 목표
- 전체 커버리지: 95% 이상
- Critical Path (검색/캐시/검증): 100%
- 새 기능 (병렬/진행률/Circuit Breaker): 95% 이상

#### 3.1.4 체크리스트
- [ ] 모든 테스트 통과 (110+ 개)
- [ ] 코드 커버리지 95% 달성
- [ ] 성능 벤치마크 목표 달성
- [ ] Playwright 테스트 5개 이상 통과

---

### 🎯 Task 3.2: 문서 업데이트 - 3시간

#### 3.2.1 업데이트 대상
1. **README.md**
   - v2.0 주요 기능 소개
   - 병렬 검색 예제 추가

2. **docs/API_REFERENCE.md**
   - search_news_batch 문서화
   - 새 에러 코드 (8개) 추가
   - 한글 에러 메시지 표 추가

3. **docs/GETTING_STARTED.md**
   - Circuit Breaker 환경변수 추가
   - 병렬 검색 가이드

4. **CHANGELOG.md**
   - v2.0.0 릴리스 노트 작성

#### 3.2.2 CHANGELOG 예시
```markdown
## [2.0.0] - 2025-12-17

### Added
- **병렬 API 호출**: `search_news_batch` 도구로 최대 5개 검색 동시 실행 (AC11)
- **날짜 검증 강화**: 미래 날짜/1990년 이전 거부, 순서 검증 (AC12)
- **API 스키마 검증**: Pydantic strict 모드로 타입 엄격 검증 (AC13)
- **진행률 피드백**: 대용량 작업(5K+) 시 10% 단위 진행률 로깅 (AC14)
- **에러 메시지 한글화**: 모든 에러 코드에 한글 메시지 및 해결 방법 (AC15)
- **Circuit Breaker**: API 장애 시 자동 차단 및 캐시 fallback (AC16)
- **Playwright 테스트**: 브라우저 기반 E2E 테스트 추가 (AC18)

### Changed
- **재시도 전략 개선**: 5xx만 재시도, 4xx 즉시 실패, jitter 추가 (AC17)
- **에러 응답 형식**: `solution`, `docs` 필드 추가

### Performance
- 병렬 3개 검색: ~9초 → ~4초 (55% 개선)
- 캐시 hit 응답: < 100ms → < 50ms

### Breaking Changes
- Pydantic strict 모드로 타입 검증 강화 (일부 느슨한 데이터 거부 가능)
```

#### 3.2.3 체크리스트
- [ ] README.md 업데이트
- [ ] API_REFERENCE.md 업데이트
- [ ] GETTING_STARTED.md 업데이트
- [ ] CHANGELOG.md v2.0.0 작성
- [ ] CLAUDE.md PRD v2.0 반영

---

### 🎯 Task 3.3: 성능 벤치마크 - 2시간

#### 3.3.1 벤치마크 스크립트
**파일**: `tests/benchmark/benchmark_v2.py`

```python
import asyncio
import time
from bigkinds_mcp.tools.search import search_news, search_news_parallel

async def benchmark_sequential_vs_parallel():
    """순차 vs 병렬 검색 벤치마크."""
    queries = [
        {"keyword": "AI", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        {"keyword": "블록체인", "start_date": "2025-12-10", "end_date": "2025-12-15"},
        {"keyword": "메타버스", "start_date": "2025-12-10", "end_date": "2025-12-15"}
    ]

    # 순차 실행
    start = time.time()
    for q in queries:
        await search_news(**q)
    sequential_time = time.time() - start

    # 병렬 실행
    start = time.time()
    await search_news_parallel(queries)
    parallel_time = time.time() - start

    print(f"=== 병렬 검색 벤치마크 ===")
    print(f"순차 실행: {sequential_time:.2f}s")
    print(f"병렬 실행: {parallel_time:.2f}s")
    print(f"속도 향상: {((sequential_time - parallel_time) / sequential_time * 100):.1f}%")

    return {
        "sequential": sequential_time,
        "parallel": parallel_time,
        "improvement": (sequential_time - parallel_time) / sequential_time
    }

if __name__ == "__main__":
    asyncio.run(benchmark_sequential_vs_parallel())
```

#### 3.3.2 목표 달성 확인
- [ ] 병렬 검색 2배 이상 빠름
- [ ] 캐시 hit < 50ms
- [ ] Circuit Breaker 오버헤드 < 1ms

---

## Phase 4: Release (0.5일)

### 🎯 Task 4.1: 배포 준비 - 2시간

#### 4.1.1 버전 업데이트
```bash
# pyproject.toml
version = "2.0.0"
```

#### 4.1.2 배포 체크리스트
- [ ] 모든 테스트 통과 (120+ 개)
- [ ] 코드 커버리지 95%+
- [ ] 성능 벤치마크 목표 달성
- [ ] 문서 업데이트 완료
- [ ] CHANGELOG.md 작성 완료
- [ ] GitHub Issues 정리

#### 4.1.3 배포 명령
```bash
git add -A
git commit -m "chore: bump version to v2.0.0"
git push origin main

git tag v2.0.0
git push origin v2.0.0
```

#### 4.1.4 GitHub Release Notes
**제목**: `v2.0.0: Quality & Performance Enhancements`

**내용**:
```markdown
# BigKinds MCP v2.0.0 🚀

품질, 성능, 사용성을 대폭 개선한 메이저 업데이트입니다.

## ✨ 주요 신규 기능

### 1. 병렬 API 호출 ⚡
- `search_news_batch` 도구로 여러 검색을 동시 실행
- 3개 검색 기준 **55% 속도 향상** (~9초 → ~4초)
- Rate limiting 자동 적용

### 2. 날짜 검증 강화 🔒
- 미래 날짜 자동 거부
- 1990년 이전 데이터 차단
- 명확한 에러 메시지

### 3. 진행률 피드백 📊
- 대용량 작업(5,000건+) 시 진행률 실시간 표시
- 예상 완료 시간 제공

### 4. 에러 메시지 한글화 🇰🇷
- 모든 에러 메시지 한국어 지원
- 해결 방법 및 문서 링크 포함

### 5. Circuit Breaker 🛡️
- API 장애 시 자동 차단 (30초)
- 캐시 fallback으로 부분 서비스 유지

## 🔧 기술 개선

- Pydantic strict 모드로 타입 안정성 향상
- 재시도 전략 개선 (jitter, 4xx/5xx 분리)
- Playwright 통합 테스트 추가

## 📈 성능 지표

| 항목 | v1.5.2 | v2.0.0 | 개선 |
|------|--------|--------|------|
| 병렬 3개 검색 | ~9초 | ~4초 | 55% ⬆️ |
| 캐시 hit 응답 | < 100ms | < 50ms | 50% ⬆️ |
| 테스트 커버리지 | 99% | 100% | 1% ⬆️ |

## ⚠️ Breaking Changes

- Pydantic strict 모드로 타입 검증 강화 (일부 느슨한 데이터 거부 가능)

## 📚 마이그레이션 가이드

기존 사용자는 추가 작업 없이 자동 업그레이드됩니다:
```bash
uvx --reinstall bigkinds-mcp@latest
```

## 🙏 감사의 말

이번 릴리스는 커뮤니티 피드백을 바탕으로 개선되었습니다. 감사합니다!

전체 변경사항: [CHANGELOG.md](./CHANGELOG.md)
```

---

## 전체 체크리스트

### Phase 1: High Priority ✅
- [ ] AC11: 병렬 API 호출
- [ ] AC12: 날짜 검증 강화
- [ ] AC13: API 스키마 검증
- [ ] AC14: 진행률 피드백

### Phase 2: Medium Priority ✅
- [ ] AC15: 에러 메시지 한글화
- [ ] AC16: Circuit Breaker 패턴
- [ ] AC17: 재시도 전략 고도화
- [ ] AC18: Playwright 통합 테스트

### Phase 3: Integration ✅
- [ ] 전체 테스트 120+ 통과
- [ ] 코드 커버리지 95%+
- [ ] 성능 벤치마크 달성
- [ ] 문서 업데이트

### Phase 4: Release ✅
- [ ] v2.0.0 배포
- [ ] GitHub Release Notes
- [ ] 마이그레이션 가이드

### Phase 5: Visualization (v3.0) ✅
- [ ] AC19: Chart Data Formatting
- [ ] AC20: WordCloud Data
- [ ] AC21: Timeline Data
- [ ] AC22: Comparison Data
- [ ] AC23: Heatmap Data
- [ ] 시각화 모듈 통합
- [ ] v3.0.0 배포

---

## Phase 5: Visualization (v3.0) (1-2일)

### 🎯 Task 5.1: Chart Data Formatting (AC19) - 3시간

#### 5.1.1 새 모듈 생성
```bash
# 디렉토리 및 파일 생성
mkdir -p src/bigkinds_mcp/visualization
touch src/bigkinds_mcp/visualization/__init__.py
touch src/bigkinds_mcp/visualization/chart_formatter.py
```

#### 5.1.2 format_chart_data 함수 구현
**파일**: `src/bigkinds_mcp/visualization/chart_formatter.py`

```python
from typing import List, Dict, Any, Literal
from datetime import datetime, timedelta

ChartType = Literal["line", "bar", "area"]
ChartFormat = Literal["echarts", "plotly", "chartjs"]
FillStrategy = Literal["null", "zero", "interpolate"]

def format_chart_data(
    data: List[Dict[str, Any]],
    chart_type: ChartType = "line",
    format: ChartFormat = "echarts",
    fill_missing: FillStrategy = "null",
    x_field: str = "date",
    y_field: str = "count"
) -> Dict[str, Any]:
    """
    시계열 데이터를 차트 라이브러리 포맷으로 변환.

    Args:
        data: 원본 데이터 [{date: "2025-12-01", count: 100}, ...]
        chart_type: 차트 유형 (line, bar, area)
        format: 출력 포맷 (echarts, plotly, chartjs)
        fill_missing: 누락 날짜 처리 (null, zero, interpolate)
        x_field: X축 필드명
        y_field: Y축 필드명

    Returns:
        차트 라이브러리 호환 데이터 구조
    """
    # 1. 데이터 정렬
    sorted_data = sorted(data, key=lambda x: x.get(x_field, ""))

    # 2. 누락 날짜 채우기
    filled_data = _fill_missing_dates(sorted_data, fill_missing, x_field, y_field)

    # 3. 포맷별 변환
    if format == "echarts":
        return _to_echarts(filled_data, chart_type, x_field, y_field)
    elif format == "plotly":
        return _to_plotly(filled_data, chart_type, x_field, y_field)
    elif format == "chartjs":
        return _to_chartjs(filled_data, chart_type, x_field, y_field)
    else:
        raise ValueError(f"Unknown format: {format}")

def _fill_missing_dates(
    data: List[Dict],
    strategy: FillStrategy,
    x_field: str,
    y_field: str
) -> List[Dict]:
    """누락 날짜 채우기."""
    if not data or strategy == "null":
        return data

    # 날짜 범위 계산
    dates = [datetime.strptime(d[x_field], "%Y-%m-%d") for d in data]
    date_values = {d[x_field]: d[y_field] for d in data}

    start, end = min(dates), max(dates)
    current = start
    filled = []

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in date_values:
            filled.append({x_field: date_str, y_field: date_values[date_str]})
        else:
            value = 0 if strategy == "zero" else None
            filled.append({x_field: date_str, y_field: value})
        current += timedelta(days=1)

    # interpolate 전략은 후처리
    if strategy == "interpolate":
        filled = _interpolate_nulls(filled, y_field)

    return filled

def _to_echarts(
    data: List[Dict],
    chart_type: str,
    x_field: str,
    y_field: str
) -> Dict[str, Any]:
    """ECharts 포맷으로 변환."""
    return {
        "xAxis": {
            "type": "category",
            "data": [d[x_field] for d in data]
        },
        "yAxis": {
            "type": "value"
        },
        "series": [{
            "type": chart_type,
            "data": [d[y_field] for d in data],
            "smooth": True if chart_type == "line" else False
        }]
    }

def _to_plotly(
    data: List[Dict],
    chart_type: str,
    x_field: str,
    y_field: str
) -> Dict[str, Any]:
    """Plotly 포맷으로 변환."""
    plotly_type = "scatter" if chart_type == "line" else chart_type
    mode = "lines+markers" if chart_type == "line" else None

    trace = {
        "x": [d[x_field] for d in data],
        "y": [d[y_field] for d in data],
        "type": plotly_type
    }
    if mode:
        trace["mode"] = mode

    return {
        "data": [trace],
        "layout": {
            "xaxis": {"title": x_field},
            "yaxis": {"title": y_field}
        }
    }

def _to_chartjs(
    data: List[Dict],
    chart_type: str,
    x_field: str,
    y_field: str
) -> Dict[str, Any]:
    """Chart.js 포맷으로 변환."""
    return {
        "type": chart_type,
        "data": {
            "labels": [d[x_field] for d in data],
            "datasets": [{
                "data": [d[y_field] for d in data],
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)"
            }]
        },
        "options": {
            "responsive": True
        }
    }
```

#### 5.1.3 테스트 작성
**파일**: `tests/unit/test_chart_formatter.py`

```python
import pytest
from bigkinds_mcp.visualization.chart_formatter import format_chart_data

class TestChartFormatter:
    """Chart Formatter 테스트."""

    def test_echarts_line_chart(self):
        """ECharts 라인 차트 변환."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-02", "count": 150}
        ]
        result = format_chart_data(data, chart_type="line", format="echarts")

        assert "xAxis" in result
        assert result["xAxis"]["data"] == ["2025-12-01", "2025-12-02"]
        assert result["series"][0]["type"] == "line"

    def test_plotly_bar_chart(self):
        """Plotly 바 차트 변환."""
        data = [{"date": "2025-12-01", "count": 100}]
        result = format_chart_data(data, chart_type="bar", format="plotly")

        assert "data" in result
        assert result["data"][0]["type"] == "bar"

    def test_fill_missing_zero(self):
        """누락 날짜 0으로 채우기."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-03", "count": 150}  # 12-02 누락
        ]
        result = format_chart_data(data, fill_missing="zero", format="echarts")

        assert len(result["xAxis"]["data"]) == 3
        assert result["series"][0]["data"][1] == 0  # 12-02 = 0
```

#### 5.1.4 체크리스트
- [ ] visualization 디렉토리 생성
- [ ] format_chart_data 함수 구현
- [ ] ECharts/Plotly/Chart.js 포맷 지원
- [ ] fill_missing 전략 구현 (null, zero, interpolate)
- [ ] 단위 테스트 작성 및 통과
- [ ] 커밋: `feat(visualization): chart data formatter (AC19)`

---

### 🎯 Task 5.2: WordCloud Data (AC20) - 2시간

#### 5.2.1 format_wordcloud_data 함수 구현
**파일**: `src/bigkinds_mcp/visualization/wordcloud_formatter.py`

```python
from typing import List, Dict, Any

def format_wordcloud_data(
    keywords: List[Dict[str, Any]],
    max_items: int = 50,
    min_weight: int = 10,
    max_weight: int = 100,
    text_field: str = "word",
    value_field: str = "count"
) -> List[Dict[str, Any]]:
    """
    키워드 데이터를 워드클라우드 포맷으로 변환.

    Args:
        keywords: 키워드 데이터 [{word: "AI", count: 500}, ...]
        max_items: 최대 항목 수
        min_weight: 최소 가중치 (폰트 크기)
        max_weight: 최대 가중치 (폰트 크기)
        text_field: 텍스트 필드명
        value_field: 값 필드명

    Returns:
        워드클라우드 호환 데이터 [{text: "AI", value: 100}, ...]
    """
    if not keywords:
        return []

    # 상위 N개 추출
    sorted_kw = sorted(keywords, key=lambda x: x.get(value_field, 0), reverse=True)
    top_keywords = sorted_kw[:max_items]

    # 값 범위 계산
    values = [kw.get(value_field, 0) for kw in top_keywords]
    min_val, max_val = min(values), max(values)
    value_range = max_val - min_val if max_val != min_val else 1

    # 정규화 및 변환
    result = []
    for kw in top_keywords:
        val = kw.get(value_field, 0)
        # 선형 스케일링
        normalized = (val - min_val) / value_range
        weight = int(min_weight + normalized * (max_weight - min_weight))

        result.append({
            "text": kw.get(text_field, ""),
            "value": weight,
            "original_count": val
        })

    return result
```

#### 5.2.2 테스트 작성
**파일**: `tests/unit/test_wordcloud_formatter.py`

```python
import pytest
from bigkinds_mcp.visualization.wordcloud_formatter import format_wordcloud_data

class TestWordcloudFormatter:
    """WordCloud Formatter 테스트."""

    def test_basic_conversion(self):
        """기본 변환 테스트."""
        keywords = [
            {"word": "AI", "count": 1000},
            {"word": "블록체인", "count": 500},
            {"word": "메타버스", "count": 100}
        ]
        result = format_wordcloud_data(keywords)

        assert len(result) == 3
        assert result[0]["text"] == "AI"
        assert result[0]["value"] == 100  # max_weight
        assert result[2]["value"] == 10   # min_weight

    def test_max_items_limit(self):
        """최대 항목 수 제한."""
        keywords = [{"word": f"kw{i}", "count": i} for i in range(100)]
        result = format_wordcloud_data(keywords, max_items=10)

        assert len(result) == 10
```

#### 5.2.3 체크리스트
- [ ] format_wordcloud_data 함수 구현
- [ ] 가중치 정규화 로직 구현
- [ ] max_items 제한 구현
- [ ] 단위 테스트 작성 및 통과
- [ ] 커밋: `feat(visualization): wordcloud data formatter (AC20)`

---

### 🎯 Task 5.3: Timeline Data (AC21) - 3시간

#### 5.3.1 format_timeline_data 함수 구현
**파일**: `src/bigkinds_mcp/visualization/timeline_formatter.py`

```python
from typing import List, Dict, Any, Optional

def format_timeline_data(
    events: List[Dict[str, Any]],
    include_media: bool = True,
    date_field: str = "date",
    title_field: str = "title",
    description_field: str = "summary",
    image_field: str = "thumbnail"
) -> Dict[str, Any]:
    """
    이벤트 데이터를 TimelineJS 포맷으로 변환.

    Args:
        events: 이벤트 데이터 [{date, title, summary, thumbnail}, ...]
        include_media: 미디어(이미지) 포함 여부
        date_field: 날짜 필드명
        title_field: 제목 필드명
        description_field: 설명 필드명
        image_field: 이미지 필드명

    Returns:
        TimelineJS 호환 데이터 구조
    """
    timeline_events = []

    for event in events:
        date_str = event.get(date_field, "")

        # 날짜 파싱 (YYYY-MM-DD)
        date_parts = date_str.split("-") if date_str else []

        timeline_event = {
            "start_date": {
                "year": int(date_parts[0]) if len(date_parts) > 0 else 2025,
                "month": int(date_parts[1]) if len(date_parts) > 1 else 1,
                "day": int(date_parts[2]) if len(date_parts) > 2 else 1
            },
            "text": {
                "headline": event.get(title_field, ""),
                "text": event.get(description_field, "")
            }
        }

        # 미디어 추가
        if include_media and event.get(image_field):
            timeline_event["media"] = {
                "url": event.get(image_field),
                "caption": event.get(title_field, "")
            }

        # 추가 메타데이터
        if event.get("url"):
            timeline_event["text"]["text"] += f'<p><a href="{event["url"]}">원문 보기</a></p>'

        timeline_events.append(timeline_event)

    return {
        "title": {
            "text": {
                "headline": "뉴스 타임라인",
                "text": f"총 {len(events)}건의 이벤트"
            }
        },
        "events": timeline_events
    }
```

#### 5.3.2 테스트 작성
**파일**: `tests/unit/test_timeline_formatter.py`

```python
import pytest
from bigkinds_mcp.visualization.timeline_formatter import format_timeline_data

class TestTimelineFormatter:
    """Timeline Formatter 테스트."""

    def test_basic_conversion(self):
        """기본 변환 테스트."""
        events = [
            {
                "date": "2025-12-15",
                "title": "AI 혁신 발표",
                "summary": "OpenAI가 새로운 모델 발표",
                "thumbnail": "https://example.com/image.jpg"
            }
        ]
        result = format_timeline_data(events)

        assert "events" in result
        assert len(result["events"]) == 1
        event = result["events"][0]
        assert event["start_date"]["year"] == 2025
        assert event["start_date"]["month"] == 12
        assert event["text"]["headline"] == "AI 혁신 발표"

    def test_without_media(self):
        """미디어 제외 테스트."""
        events = [{"date": "2025-12-15", "title": "테스트", "thumbnail": "url"}]
        result = format_timeline_data(events, include_media=False)

        assert "media" not in result["events"][0]
```

#### 5.3.3 체크리스트
- [ ] format_timeline_data 함수 구현
- [ ] TimelineJS 포맷 지원
- [ ] 미디어 포함/제외 옵션 구현
- [ ] 단위 테스트 작성 및 통과
- [ ] 커밋: `feat(visualization): timeline data formatter (AC21)`

---

### 🎯 Task 5.4: Comparison Data (AC22) - 2시간

#### 5.4.1 format_comparison_data 함수 구현
**파일**: `src/bigkinds_mcp/visualization/comparison_formatter.py`

```python
from typing import List, Dict, Any, Literal

ComparisonMode = Literal["absolute", "relative", "normalized"]

def format_comparison_data(
    keywords_data: Dict[str, List[Dict[str, Any]]],
    mode: ComparisonMode = "absolute",
    date_field: str = "date",
    value_field: str = "count"
) -> Dict[str, Any]:
    """
    다중 키워드 비교 데이터를 차트 포맷으로 변환.

    Args:
        keywords_data: 키워드별 데이터 {"AI": [{date, count}], "블록체인": [...]}
        mode: 비교 모드
            - absolute: 절대값 비교
            - relative: 첫 날 대비 상대 변화율 (%)
            - normalized: 0-100 정규화
        date_field: 날짜 필드명
        value_field: 값 필드명

    Returns:
        비교 차트용 데이터 구조
    """
    if not keywords_data:
        return {"series": [], "categories": []}

    # 모든 날짜 수집 및 정렬
    all_dates = set()
    for data in keywords_data.values():
        for item in data:
            all_dates.add(item.get(date_field, ""))
    categories = sorted(all_dates)

    # 시리즈 생성
    series = []
    for keyword, data in keywords_data.items():
        # 날짜-값 매핑
        date_values = {d.get(date_field): d.get(value_field, 0) for d in data}
        values = [date_values.get(date, 0) for date in categories]

        # 모드별 변환
        if mode == "relative" and values and values[0] > 0:
            base = values[0]
            values = [((v - base) / base) * 100 for v in values]
        elif mode == "normalized":
            max_val = max(values) if values else 1
            values = [(v / max_val) * 100 if max_val > 0 else 0 for v in values]

        series.append({
            "name": keyword,
            "type": "line",
            "data": values
        })

    return {
        "categories": categories,
        "series": series,
        "mode": mode
    }
```

#### 5.4.2 테스트 작성
**파일**: `tests/unit/test_comparison_formatter.py`

```python
import pytest
from bigkinds_mcp.visualization.comparison_formatter import format_comparison_data

class TestComparisonFormatter:
    """Comparison Formatter 테스트."""

    def test_absolute_mode(self):
        """절대값 비교 모드."""
        data = {
            "AI": [{"date": "2025-12-01", "count": 100}],
            "블록체인": [{"date": "2025-12-01", "count": 50}]
        }
        result = format_comparison_data(data, mode="absolute")

        assert len(result["series"]) == 2
        assert result["series"][0]["data"] == [100]

    def test_relative_mode(self):
        """상대 변화율 모드."""
        data = {
            "AI": [
                {"date": "2025-12-01", "count": 100},
                {"date": "2025-12-02", "count": 150}
            ]
        }
        result = format_comparison_data(data, mode="relative")

        # 첫 날 대비: 100→100 = 0%, 100→150 = 50%
        assert result["series"][0]["data"][0] == 0
        assert result["series"][0]["data"][1] == 50
```

#### 5.4.3 체크리스트
- [ ] format_comparison_data 함수 구현
- [ ] absolute/relative/normalized 모드 구현
- [ ] 다중 키워드 지원
- [ ] 단위 테스트 작성 및 통과
- [ ] 커밋: `feat(visualization): comparison data formatter (AC22)`

---

### 🎯 Task 5.5: Heatmap Data (AC23) - 2시간

#### 5.5.1 format_heatmap_data 함수 구현
**파일**: `src/bigkinds_mcp/visualization/heatmap_formatter.py`

```python
from typing import List, Dict, Any, Literal

NormalizeMode = Literal["none", "row", "column", "all"]

def format_heatmap_data(
    data: List[Dict[str, Any]],
    x_axis: str,
    y_axis: str,
    value_field: str = "count",
    normalize: NormalizeMode = "none"
) -> Dict[str, Any]:
    """
    데이터를 히트맵 포맷으로 변환.

    Args:
        data: 원본 데이터 [{publisher: "경향", date: "2025-12-01", count: 10}, ...]
        x_axis: X축 필드명 (예: "date")
        y_axis: Y축 필드명 (예: "publisher")
        value_field: 값 필드명
        normalize: 정규화 모드 (none, row, column, all)

    Returns:
        히트맵 데이터 구조 (ECharts 호환)
    """
    if not data:
        return {"xAxis": [], "yAxis": [], "data": []}

    # 축 값 수집
    x_values = sorted(set(d.get(x_axis, "") for d in data))
    y_values = sorted(set(d.get(y_axis, "") for d in data))

    # 2D 매트릭스 생성
    matrix = {}
    for d in data:
        x = d.get(x_axis, "")
        y = d.get(y_axis, "")
        matrix[(x, y)] = d.get(value_field, 0)

    # 히트맵 데이터 생성 [x_index, y_index, value]
    heatmap_data = []
    for xi, x in enumerate(x_values):
        for yi, y in enumerate(y_values):
            value = matrix.get((x, y), 0)
            heatmap_data.append([xi, yi, value])

    # 정규화 적용
    if normalize != "none":
        heatmap_data = _normalize_heatmap(heatmap_data, len(x_values), len(y_values), normalize)

    # 최대/최소값 계산
    values = [d[2] for d in heatmap_data]

    return {
        "xAxis": x_values,
        "yAxis": y_values,
        "data": heatmap_data,
        "min": min(values) if values else 0,
        "max": max(values) if values else 0
    }

def _normalize_heatmap(
    data: List[List],
    x_len: int,
    y_len: int,
    mode: NormalizeMode
) -> List[List]:
    """히트맵 데이터 정규화."""
    if mode == "all":
        values = [d[2] for d in data]
        max_val = max(values) if values else 1
        return [[d[0], d[1], d[2] / max_val * 100 if max_val else 0] for d in data]

    # row/column 정규화는 더 복잡한 로직 필요
    # 간단한 구현
    return data
```

#### 5.5.2 테스트 작성
**파일**: `tests/unit/test_heatmap_formatter.py`

```python
import pytest
from bigkinds_mcp.visualization.heatmap_formatter import format_heatmap_data

class TestHeatmapFormatter:
    """Heatmap Formatter 테스트."""

    def test_basic_conversion(self):
        """기본 변환 테스트."""
        data = [
            {"date": "2025-12-01", "publisher": "경향", "count": 10},
            {"date": "2025-12-01", "publisher": "한겨레", "count": 15},
            {"date": "2025-12-02", "publisher": "경향", "count": 20}
        ]
        result = format_heatmap_data(data, x_axis="date", y_axis="publisher")

        assert result["xAxis"] == ["2025-12-01", "2025-12-02"]
        assert "경향" in result["yAxis"]
        assert len(result["data"]) == 4  # 2 dates x 2 publishers
```

#### 5.5.3 체크리스트
- [ ] format_heatmap_data 함수 구현
- [ ] normalize 모드 구현
- [ ] ECharts 호환 포맷 출력
- [ ] 단위 테스트 작성 및 통과
- [ ] 커밋: `feat(visualization): heatmap data formatter (AC23)`

---

### 🎯 Task 5.6: Visualization 모듈 통합 - 1시간

#### 5.6.1 __init__.py 설정
**파일**: `src/bigkinds_mcp/visualization/__init__.py`

```python
"""시각화 유틸리티 모듈."""

from .chart_formatter import format_chart_data
from .wordcloud_formatter import format_wordcloud_data
from .timeline_formatter import format_timeline_data
from .comparison_formatter import format_comparison_data
from .heatmap_formatter import format_heatmap_data

__all__ = [
    "format_chart_data",
    "format_wordcloud_data",
    "format_timeline_data",
    "format_comparison_data",
    "format_heatmap_data"
]
```

#### 5.6.2 체크리스트
- [ ] 모든 포매터 export
- [ ] 통합 테스트 작성
- [ ] 문서 업데이트
- [ ] 커밋: `feat(visualization): module integration (v3.0)`

---

## 예상 소요 시간

| Phase | 작업 | 시간 |
|-------|------|------|
| Phase 1 | High Priority (4개 AC) | 12시간 |
| Phase 2 | Medium Priority (4개 AC) | 17시간 |
| Phase 3 | Integration & Testing | 9시간 |
| Phase 4 | Release | 2시간 |
| Phase 5 | Visualization (5개 AC) | 13시간 |
| **총계** | **전체 작업** | **53시간** (7일) |

---

## 다음 단계

이 워크플로우를 따라 구현하시겠습니까? 특정 Phase부터 시작하거나 일부 작업을 생략하고 싶으시면 말씀해주세요.
