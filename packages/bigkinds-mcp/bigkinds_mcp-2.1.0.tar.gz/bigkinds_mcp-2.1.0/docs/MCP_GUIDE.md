# BigKinds MCP Server 사용 가이드

BigKinds MCP 서버의 모든 기능과 출력 형식에 대한 상세 가이드입니다.

## 목차

1. [설치 및 설정](#설치-및-설정)
2. [Tools](#tools)
3. [Resources](#resources)
4. [Prompts](#prompts)
5. [출력 형식](#출력-형식)
6. [사용 시나리오](#사용-시나리오)

---

## 설치 및 설정

### 1. 설치

```bash
# uvx로 바로 실행 (권장)
uvx bigkinds-mcp

# 또는 pip 설치
pip install bigkinds-mcp
```

### 2. MCP 클라이언트 설정

#### Claude Desktop (macOS / Windows)

macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uvx",
      "args": ["bigkinds-mcp"],
      "env": {
        "BIGKINDS_USER_ID": "your_email@example.com",
        "BIGKINDS_USER_PASSWORD": "your_password"
      }
    }
  }
}
```

> `env` 필드는 선택사항. 키워드 트렌드, 연관어 분석 등 로그인 필요 기능 사용 시에만 설정.

#### Claude Code

```bash
claude mcp add bigkinds -- uvx bigkinds-mcp
```

#### Cursor / VS Code

`.cursor/mcp.json` 또는 `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uvx",
      "args": ["bigkinds-mcp"],
      "env": {
        "BIGKINDS_USER_ID": "your_email@example.com",
        "BIGKINDS_USER_PASSWORD": "your_password"
      }
    }
  }
}
```

### 3. 설정 확인

Claude Desktop을 재시작한 후, 대화창에서 MCP 도구가 활성화되었는지 확인합니다.

```
사용자: /mcp
Claude: 활성화된 MCP 서버: bigkinds-news
        사용 가능한 도구: 9개
```

---

## Tools

### 1. search_news

뉴스 기사를 검색합니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `keyword` | string | ✅ | - | 검색 키워드 (AND/OR 연산자 지원) |
| `start_date` | string | ✅ | - | 시작일 (YYYY-MM-DD) |
| `end_date` | string | ✅ | - | 종료일 (YYYY-MM-DD) |
| `page` | int | | 1 | 페이지 번호 |
| `page_size` | int | | 20 | 페이지당 결과 수 (최대 100) |
| `providers` | list[str] | | null | 언론사 필터 |
| `categories` | list[str] | | null | 카테고리 필터 |
| `sort_by` | string | | "both" | 정렬 방식 |

#### sort_by 옵션

- `"both"` (기본값): date + relevance 두 번 검색 후 병합 (중복 제거)
- `"date"`: 날짜순 (최신순)
- `"relevance"`: 관련도순

#### 출력 형식

```json
{
  "total_count": 9817,
  "page": 1,
  "page_size": 20,
  "total_pages": 491,
  "has_next": true,
  "has_prev": false,
  "keyword": "AI",
  "date_range": "2024-12-01 to 2024-12-15",
  "sort_by": "both",
  "articles": [
    {
      "news_id": "01100901.20241215...",
      "title": "OpenAI, GPT-5 개발 착수",
      "summary": "OpenAI가 차세대 AI 모델 GPT-5 개발에...",
      "publisher": "한국경제",
      "published_date": "2024-12-15",
      "category": "IT_과학",
      "url": "https://..."
    }
  ]
}
```

#### 사용 예시

```
사용자: AI 관련 최근 뉴스 검색해줘

Claude: search_news(keyword="AI", start_date="2024-12-01", end_date="2024-12-15")
```

```
사용자: 한겨레와 경향신문의 경제 기사만 검색해줘

Claude: search_news(
    keyword="경제",
    start_date="2024-12-01",
    end_date="2024-12-15",
    providers=["한겨레", "경향신문"],
    categories=["경제"]
)
```

---

### 2. get_article_count

키워드의 기사 수를 시간대별로 집계합니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `keyword` | string | ✅ | - | 검색 키워드 |
| `start_date` | string | ✅ | - | 시작일 (YYYY-MM-DD) |
| `end_date` | string | ✅ | - | 종료일 (YYYY-MM-DD) |
| `group_by` | string | | "total" | 집계 단위 |
| `providers` | list[str] | | null | 언론사 필터 |

#### group_by 옵션

- `"total"`: 전체 기간 총합만 반환
- `"day"`: 일별 집계 (최대 31일 권장)
- `"week"`: 주별 집계
- `"month"`: 월별 집계

#### 출력 형식

**total:**
```json
{
  "keyword": "AI",
  "total_count": 9817,
  "date_range": "2024-12-01 to 2024-12-15",
  "group_by": "total",
  "counts": []
}
```

**day:**
```json
{
  "keyword": "AI",
  "total_count": 9817,
  "date_range": "2024-12-01 to 2024-12-15",
  "group_by": "day",
  "counts": [
    {"date": "2024-12-01", "count": 523},
    {"date": "2024-12-02", "count": 612},
    ...
  ]
}
```

**month:**
```json
{
  "keyword": "AI",
  "total_count": 45230,
  "date_range": "2024-01-01 to 2024-12-31",
  "group_by": "month",
  "counts": [
    {"date": "2024-01", "month_start": "2024-01-01", "month_end": "2024-01-31", "count": 3521},
    {"date": "2024-02", "month_start": "2024-02-01", "month_end": "2024-02-29", "count": 3890},
    ...
  ]
}
```

---

### 3. get_article

기사의 상세 정보를 가져옵니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `news_id` | string | △ | null | BigKinds 기사 ID |
| `url` | string | △ | null | 원본 기사 URL |
| `include_full_content` | bool | | true | 전문 포함 여부 |
| `include_images` | bool | | false | 이미지 포함 여부 |

> △ news_id 또는 url 중 하나는 필수

#### 출력 형식

```json
{
  "news_id": "01100901.20241215...",
  "title": "OpenAI, GPT-5 개발 착수",
  "summary": "OpenAI가 차세대...",
  "full_content": "전체 기사 본문...",
  "publisher": "한국경제",
  "author": "홍길동 기자",
  "published_date": "2024-12-15",
  "category": "IT_과학",
  "url": "https://...",
  "images": [],
  "keywords": ["AI", "OpenAI", "GPT"],
  "scrape_status": "success",
  "content_length": 2340,
  "content_markdown": "# OpenAI, GPT-5 개발 착수\n\n본문...",
  "llm_context": "# OpenAI, GPT-5 개발 착수\n\n**한국경제 | 2024-12-15**\n\n..."
}
```

---

### 4. scrape_article_url

URL에서 기사 내용을 스크래핑합니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `url` | string | ✅ | - | 스크래핑할 기사 URL |
| `extract_images` | bool | | false | 이미지 추출 여부 |

#### 출력 형식

```json
{
  "url": "https://n.news.naver.com/article/...",
  "final_url": "https://n.news.naver.com/article/...",
  "success": true,
  "title": "기사 제목",
  "content": "기사 전문...",
  "author": "홍길동 기자",
  "published_date": "2024-12-15",
  "publisher": "한국경제",
  "images": [
    {
      "url": "https://...",
      "caption": "이미지 설명",
      "is_main": true
    }
  ],
  "keywords": ["키워드1", "키워드2"],
  "error": null,
  "content_markdown": "# 기사 제목\n\n본문...",
  "llm_context": "# 기사 제목\n\n**한국경제 | 2024-12-15**\n\n..."
}
```

#### 이미지 필터링

`extract_images=true` 시 다음이 자동 필터링됩니다:
- 광고 이미지 (ads, doubleclick, googlesyndication 등)
- 로고/아이콘 (logo, icon, favicon, button 등)
- 트래킹 픽셀 (pixel, beacon, 1x1 등)
- 소셜 버튼 (facebook_btn, twitter_share 등)
- UI 요소 (sprite, background, border 등)

---

### 5. get_today_issues

오늘/특정 날짜의 인기 이슈를 조회합니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `date` | string | | 오늘 | 조회 날짜 (YYYY-MM-DD) |
| `category` | string | | "전체" | 카테고리 필터 |

#### category 옵션

- `"전체"`: 모든 카테고리
- `"서울"`: 서울 지역
- `"경인강원"`: 경기/인천/강원
- `"충청"`: 충청 지역
- `"경상"`: 경상 지역
- `"전라제주"`: 전라/제주 지역
- `"AI"`: AI가 선정한 이슈

#### 출력 형식

```json
{
  "query_date": "2024-12-15",
  "category": "전체",
  "total_dates": 1,
  "results": [
    {
      "date": "20241215",
      "date_display": "2024년 12월 15일",
      "issues": [
        {
          "rank": 1,
          "title": "비상계엄 해제",
          "article_count": 1523,
          "topic_id": "..."
        },
        {
          "rank": 2,
          "title": "AI 규제 논의",
          "article_count": 892,
          "topic_id": "..."
        }
      ]
    }
  ]
}
```

---

### 6. get_current_korean_time

현재 한국 시간(KST)을 조회합니다.

#### 파라미터

없음

#### 출력 형식

```json
{
  "datetime": "2024-12-15T14:30:45+09:00",
  "date": "2024-12-15",
  "time": "14:30:45",
  "weekday": "일요일",
  "weekday_en": "Sunday",
  "timezone": "Asia/Seoul",
  "utc_offset": "+09:00"
}
```

---

### 7. find_category

언론사 또는 카테고리 코드를 검색합니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `query` | string | ✅ | - | 검색어 |
| `category_type` | string | | "all" | 검색 대상 |

#### category_type 옵션

- `"all"`: 언론사 + 카테고리 모두
- `"provider"`: 언론사만
- `"category"`: 카테고리만

#### 출력 형식

```json
{
  "query": "한겨레",
  "category_type": "all",
  "providers": [
    {
      "name": "한겨레",
      "code": "02100201",
      "group": "전국종합지"
    }
  ],
  "categories": []
}
```

---

### 8. list_providers

모든 언론사 목록을 반환합니다.

#### 파라미터

없음

#### 출력 형식

```json
{
  "total_count": 150,
  "groups": [
    {
      "name": "전국종합지",
      "providers": [
        {"name": "경향신문", "code": "01100101"},
        {"name": "국민일보", "code": "01100201"},
        {"name": "한겨레", "code": "02100201"}
      ]
    },
    {
      "name": "경제지",
      "providers": [
        {"name": "매일경제", "code": "02100801"},
        {"name": "한국경제", "code": "02100701"}
      ]
    }
  ]
}
```

---

### 9. list_categories

모든 카테고리 목록을 반환합니다.

#### 파라미터

없음

#### 출력 형식

```json
{
  "total_count": 15,
  "categories": [
    {"name": "정치", "code": "정치"},
    {"name": "경제", "code": "경제"},
    {"name": "사회", "code": "사회"},
    {"name": "문화", "code": "문화"},
    {"name": "국제", "code": "국제"},
    {"name": "IT_과학", "code": "IT_과학"},
    {"name": "스포츠", "code": "스포츠"}
  ]
}
```

---

## Resources

MCP Resources는 URI 형식으로 데이터를 제공합니다.

### stats://providers

언론사 코드 목록을 마크다운 형식으로 제공합니다.

```
URI: stats://providers

출력: 마크다운 테이블 (언론사명, 코드, 그룹)
```

### stats://categories

카테고리 코드 목록을 마크다운 형식으로 제공합니다.

```
URI: stats://categories

출력: 마크다운 테이블 (카테고리명, 코드)
```

### news://{keyword}/{date}

특정 날짜의 키워드 검색 결과를 제공합니다.

```
URI: news://AI/2024-12-15

출력: 해당 날짜의 AI 관련 뉴스 목록 (마크다운)
```

### article://{news_id}

개별 기사 정보를 제공합니다.

```
URI: article://01100901.20241215...

출력: 기사 상세 정보 (마크다운)
```

---

## Prompts

MCP Prompts는 LLM에게 제공할 분석 프롬프트를 생성합니다.

### news_analysis

뉴스 분석을 위한 프롬프트를 생성합니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `keyword` | string | ✅ | - | 분석할 키워드 |
| `start_date` | string | ✅ | - | 시작일 |
| `end_date` | string | ✅ | - | 종료일 |
| `analysis_type` | string | | "summary" | 분석 유형 |

#### analysis_type 옵션

- `"summary"`: 주요 내용 요약
- `"sentiment"`: 감성 분석
- `"trend"`: 트렌드 분석
- `"comparison"`: 언론사별 보도 비교

---

### trend_report

트렌드 리포트 생성을 위한 프롬프트입니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `keyword` | string | ✅ | - | 분석할 키워드 |
| `days` | int | | 7 | 분석 기간 (일) |

---

### issue_briefing

일일 이슈 브리핑을 위한 프롬프트입니다.

#### 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `date` | string | | 오늘 | 브리핑 날짜 |

---

## 출력 형식

### LLM Context 형식

`include_markdown=true` 시 제공되는 `llm_context` 필드는 다음 형식입니다:

```markdown
# 기사 제목

**언론사 | 발행일**

> 요약 (있는 경우)

본문 내용...

---
**키워드**: AI, 반도체, 기술
**원문**: https://...
```

### Content Markdown 형식

`content_markdown` 필드는 HTML을 정제한 순수 마크다운입니다:

- 광고/스크립트 제거
- 관련 기사 영역 제거
- 헤딩/볼드/리스트 보존
- 이미지 태그 제거 (기본값)

---

## 사용 시나리오

### 시나리오 1: 일일 뉴스 브리핑

```
사용자: 오늘 주요 뉴스 정리해줘

Claude:
1. get_current_korean_time() → 오늘 날짜 확인
2. get_today_issues() → 오늘 인기 이슈 조회
3. search_news(keyword=이슈키워드, ...) → 상세 검색
4. 브리핑 생성
```

### 시나리오 2: 키워드 트렌드 분석

```
사용자: 지난 한 달간 "AI" 키워드 트렌드 분석해줘

Claude:
1. get_article_count(keyword="AI", group_by="day", ...) → 일별 기사 수
2. search_news(keyword="AI", ...) → 대표 기사 조회
3. 트렌드 리포트 생성
```

### 시나리오 3: 기사 전문 분석

```
사용자: 이 기사 전문 분석해줘: https://...

Claude:
1. scrape_article_url(url="...", extract_images=true) → 기사 스크래핑
2. llm_context 필드 활용하여 분석
```

### 시나리오 4: 언론사별 보도 비교

```
사용자: "반도체"에 대해 한겨레와 조선일보 보도 비교해줘

Claude:
1. search_news(keyword="반도체", providers=["한겨레"], ...)
2. search_news(keyword="반도체", providers=["조선일보"], ...)
3. 각 언론사 기사 스크래핑
4. 비교 분석
```

---

## 주의사항

1. **비공식 API**: BigKinds의 비공식 API를 활용합니다
2. **날짜 형식**: 모든 날짜는 `YYYY-MM-DD` 형식 (예: 2024-12-15)
3. **시간대**: 모든 시간은 KST (한국 표준시, UTC+9) 기준
4. **캐싱**: 동일 요청은 5분간 캐싱됨
