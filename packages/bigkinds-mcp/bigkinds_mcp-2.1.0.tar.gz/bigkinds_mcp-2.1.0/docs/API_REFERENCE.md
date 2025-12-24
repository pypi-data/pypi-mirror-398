# BigKinds MCP Server API Reference

> BigKinds MCP 서버의 전체 API 레퍼런스입니다.

## 목차

- [MCP Tools](#mcp-tools)
  - [검색 도구](#검색-도구)
  - [기사 조회 도구](#기사-조회-도구)
  - [분석 도구](#분석-도구)
  - [유틸리티 도구](#유틸리티-도구)
- [MCP Resources](#mcp-resources)
- [MCP Prompts](#mcp-prompts)
- [오류 처리](#오류-처리)
- [API 제한사항](#api-제한사항)

---

## MCP Tools

### 검색 도구

#### `search_news`

뉴스 기사를 검색합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `keyword` | string | O | - | 검색 키워드 (AND/OR 연산자 지원) |
| `start_date` | string | O | - | 검색 시작일 (YYYY-MM-DD) |
| `end_date` | string | O | - | 검색 종료일 (YYYY-MM-DD) |
| `page` | integer | X | 1 | 페이지 번호 |
| `page_size` | integer | X | 20 | 페이지당 결과 수 (최대 100) |
| `providers` | string[] | X | - | 언론사 필터 (예: ["경향신문", "한겨레"]) |
| `categories` | string[] | X | - | 카테고리 필터 (예: ["경제", "IT_과학"]) |
| `sort_by` | string | X | "both" | 정렬 방식: "both", "date", "relevance" |

**정렬 방식 설명:**
- `"both"`: date + relevance 두 번 호출 후 병합 (news_id로 중복 제거)
- `"date"`: 날짜순 (최신순)
- `"relevance"`: 관련도순

**응답 예시:**

```json
{
  "total_count": 3241,
  "page": 1,
  "page_size": 20,
  "total_pages": 163,
  "articles": [
    {
      "news_id": "01100401.20251215...",
      "title": "AI 기술 발전...",
      "summary": "인공지능 기술이...",
      "provider": "경향신문",
      "date": "2025-12-15",
      "url": "https://..."
    }
  ],
  "workflow_hint": "100건 이상입니다. export_all_articles 사용을 권장합니다."
}
```

---

#### `get_article_count`

기사 수를 집계합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `keyword` | string | O | - | 검색 키워드 |
| `start_date` | string | O | - | 검색 시작일 (YYYY-MM-DD) |
| `end_date` | string | O | - | 검색 종료일 (YYYY-MM-DD) |
| `group_by` | string | X | "total" | 집계 단위: "total", "day", "week", "month" |
| `providers` | string[] | X | - | 언론사 필터 |

**응답 예시 (group_by="month"):**

```json
{
  "total_count": 56642,
  "counts": [
    {"period": "2025-01", "count": 3475},
    {"period": "2025-02", "count": 4210},
    ...
  ]
}
```

---

### 기사 조회 도구

#### `get_article`

기사 상세 정보를 조회합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `news_id` | string | △ | - | BigKinds 기사 ID (news_id 또는 url 중 하나 필수) |
| `url` | string | △ | - | 원본 기사 URL |
| `include_full_content` | boolean | X | true | 전체 본문 포함 여부 |
| `include_images` | boolean | X | false | 이미지 URL 포함 여부 |

**응답 예시:**

```json
{
  "news_id": "01100401.20251215...",
  "title": "AI 기술 발전...",
  "content": "전체 기사 본문...",
  "provider": "경향신문",
  "date": "2025-12-15",
  "byline": "홍길동 기자",
  "url": "https://...",
  "source": "bigkinds_api"
}
```

**source 필드:**
- `"bigkinds_api"`: BigKinds detailView API로 본문 획득 (권장)
- `"scraping"`: URL 스크래핑으로 본문 획득 (폴백)

---

#### `scrape_article_url`

URL에서 직접 기사를 스크래핑합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `url` | string | O | - | 스크래핑할 기사 URL |
| `extract_images` | boolean | X | false | 이미지 추출 여부 |

---

### 분석 도구

#### `get_today_issues`

오늘/특정 날짜의 인기 이슈를 조회합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `date` | string | X | 오늘 | 조회 날짜 (YYYY-MM-DD) |
| `category` | string | X | "전체" | 카테고리 필터 |

**지원 카테고리:** (지역/유형 기반)
- `"전체"`: 모든 카테고리
- `"서울"`: 서울 지역
- `"경인강원"`: 경기/인천/강원 지역
- `"충청"`: 충청 지역
- `"경상"`: 경상 지역
- `"전라제주"`: 전라/제주 지역
- `"AI"`: AI가 선정한 이슈

**응답 예시:**

```json
{
  "date": "2025-12-15",
  "category": "전체",
  "issues": [
    {
      "rank": 1,
      "title": "카카오 판교사옥 폭파 협박",
      "article_count": 43,
      "topic_category": "서울"
    }
  ]
}
```

---

#### `compare_keywords`

여러 키워드의 기사 수를 비교합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `keywords` | string[] | O | - | 비교할 키워드 목록 (2-10개) |
| `start_date` | string | O | - | 검색 시작일 (YYYY-MM-DD) |
| `end_date` | string | O | - | 검색 종료일 (YYYY-MM-DD) |
| `group_by` | string | X | "total" | 집계 단위: "total", "day", "week", "month" |

**응답 예시:**

```json
{
  "keywords": ["AI", "반도체", "전기차"],
  "period": "2025-01-01 ~ 2025-12-15",
  "comparison": [
    {"keyword": "AI", "total_count": 505885, "rank": 1},
    {"keyword": "반도체", "total_count": 161451, "rank": 2},
    {"keyword": "전기차", "total_count": 74648, "rank": 3}
  ]
}
```

---

#### `get_keyword_trends` (로그인 필요)

키워드 트렌드를 시계열로 분석합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `keyword` | string | O | - | 분석 키워드 (쉼표로 여러 개 가능) |
| `start_date` | string | O | - | 분석 시작일 (YYYY-MM-DD) |
| `end_date` | string | O | - | 분석 종료일 (YYYY-MM-DD) |
| `interval` | integer | X | 1 | 시간 단위 힌트 (1: 일, 2: 주, 3: 월, 4: 년) |
| `providers` | string[] | X | - | 언론사 필터 |
| `categories` | string[] | X | - | 카테고리 필터 |

**참고:** BigKinds API는 `interval` 값과 관계없이 날짜 범위에 따라 자동으로 granularity를 조정합니다.

---

#### `get_related_keywords` (로그인 필요)

연관어를 TF-IDF 기반으로 분석합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `keyword` | string | O | - | 분석 키워드 |
| `start_date` | string | O | - | 분석 시작일 (YYYY-MM-DD) |
| `end_date` | string | O | - | 분석 종료일 (YYYY-MM-DD) |
| `max_news_count` | integer | X | 100 | 분석할 최대 뉴스 수 (50, 100, 200, 500, 1000 권장) |
| `result_number` | integer | X | 50 | 반환할 연관어 수 |

**응답 예시:**

```json
{
  "keyword": "인공지능",
  "period": "2025-12-01 ~ 2025-12-15",
  "related_words": [
    {"word": "AI", "score": 42.63},
    {"word": "머신러닝", "score": 15.03},
    {"word": "딥러닝", "score": 8.67}
  ]
}
```

---

### 유틸리티 도구

#### `smart_sample`

대용량 검색 결과에서 대표 샘플을 추출합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `keyword` | string | O | - | 검색 키워드 |
| `start_date` | string | O | - | 검색 시작일 (YYYY-MM-DD) |
| `end_date` | string | O | - | 검색 종료일 (YYYY-MM-DD) |
| `sample_size` | integer | X | 100 | 추출할 샘플 수 (최대 500) |
| `strategy` | string | X | "stratified" | 샘플링 전략 |

**샘플링 전략:**
- `"stratified"`: 기간별 균등 분포 (연도/월별 비례 샘플링)
- `"latest"`: 최신 기사 우선
- `"random"`: 무작위 추출 (API 15페이지 제한 적용)

---

#### `export_all_articles`

전체 기사를 일괄 내보냅니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `keyword` | string | O | - | 검색 키워드 |
| `start_date` | string | O | - | 검색 시작일 (YYYY-MM-DD) |
| `end_date` | string | O | - | 검색 종료일 (YYYY-MM-DD) |
| `output_format` | string | X | "json" | 출력 형식: "json", "csv", "jsonl" |
| `output_path` | string | X | 자동 생성 | 저장 경로 |
| `max_articles` | integer | X | 10000 | 최대 내보내기 수 (최대 50000) |
| `include_content` | boolean | X | false | 전체 본문 포함 (시간 오래 걸림) |

**응답 예시:**

```json
{
  "success": true,
  "output_path": "/path/to/bigkinds_export_AI_20251215.json",
  "exported_count": 3241,
  "analysis_code": "import json\nimport pandas as pd\n..."
}
```

---

#### `get_current_korean_time`

현재 한국 시간(KST)을 반환합니다.

**파라미터:** 없음

**응답 예시:**

```json
{
  "datetime": "2025-12-15T21:45:30+09:00",
  "date": "2025-12-15",
  "time": "21:45:30",
  "weekday": "월요일"
}
```

---

#### `find_category`

언론사 또는 카테고리 코드를 검색합니다.

**파라미터:**

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `query` | string | O | - | 검색어 (예: "경향", "IT") |
| `category_type` | string | X | "all" | 검색 대상: "all", "provider", "category" |

---

#### `list_providers`

전체 언론사 목록을 반환합니다.

**파라미터:** 없음

**응답:** 72개 언론사 목록 (종합일간지, 경제지, 지역일간지, 방송사 등)

---

#### `list_categories`

전체 카테고리 목록을 반환합니다.

**파라미터:** 없음

**응답:** 8개 카테고리 (정치, 경제, 사회, 문화, 국제, 지역, 스포츠, IT_과학)

---

#### `cache_stats`

캐시 사용 현황을 조회합니다.

**파라미터:** 없음

**응답 예시:**

```json
{
  "search": {"size": 13, "max_size": 1000, "usage_percent": 1.3},
  "article": {"size": 1, "max_size": 1000, "usage_percent": 0.1},
  "count": {"size": 3, "max_size": 1000, "usage_percent": 0.3}
}
```

---

## MCP Resources

### `stats://providers`

언론사 코드 목록을 마크다운 형식으로 반환합니다.

### `stats://categories`

카테고리 코드 목록을 마크다운 형식으로 반환합니다.

### `news://{keyword}/{date}`

특정 날짜의 뉴스 검색 결과를 반환합니다.

**예시:** `news://인공지능/2025-12-15`

### `article://{news_id}`

개별 기사 정보를 반환합니다.

**예시:** `article://01100401.20251215123456`

---

## MCP Prompts

### `news_analysis`

뉴스 분석 프롬프트를 생성합니다.

**인자:**
- `analysis_type`: "summary", "sentiment", "trend", "comparison"
- `keyword`: 분석 키워드
- `period`: 분석 기간

### `trend_report`

트렌드 리포트 생성 프롬프트를 제공합니다.

### `issue_briefing`

일일 이슈 브리핑 프롬프트를 제공합니다.

### `large_scale_analysis`

대용량 분석 워크플로우 가이드를 제공합니다.

**사용 시점:** 100건 이상의 기사를 분석해야 할 때

---

## 오류 처리

### 일반 오류 응답

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "오류 상세 설명"
}
```

### 주요 오류 코드

| 코드 | 설명 | 해결 방법 |
|------|------|----------|
| `INVALID_PARAMETER` | 잘못된 파라미터 | 파라미터 값 확인 |
| `AUTH_REQUIRED` | 로그인 필요 | 환경변수 설정 확인 |
| `RATE_LIMITED` | 요청 제한 초과 | 잠시 후 재시도 |
| `NOT_FOUND` | 기사 없음 | news_id 또는 URL 확인 |
| `INSUFFICIENT_DATA` | 데이터 부족 | 검색 조건 완화 |

---

## API 제한사항

### BigKinds API 제한

| 항목 | 제한 |
|------|------|
| 페이지네이션 | 최대 ~15-17페이지 |
| 검색 결과 | 페이지당 최대 100건 |
| 검색 요약 | 200자로 제한 (전체 본문은 get_article 사용) |
| 카테고리 API | `get_today_issues`는 `전체`만 API 지원, 나머지는 클라이언트 필터링 |

### 캐시 TTL

| 캐시 대상 | TTL |
|----------|-----|
| 검색 결과 | 5분 |
| 기사 상세 | 30분 |
| 트렌드 데이터 | 10분 |

### 재시도 정책

- 최대 재시도: 3회
- 재시도 간격: 지수 백오프 (1초, 2초, 4초)
- 타임아웃: 30초

---

## 환경변수

```bash
# 로그인 필요 도구 사용 시 필수
export BIGKINDS_USER_ID=your_email@example.com
export BIGKINDS_USER_PASSWORD=your_password

# 선택 (기본값 표시)
export BIGKINDS_TIMEOUT=30          # API 타임아웃 (초)
export BIGKINDS_MAX_RETRIES=3       # 최대 재시도 횟수
export BIGKINDS_RETRY_DELAY=1.0     # 재시도 간격 (초)
```
