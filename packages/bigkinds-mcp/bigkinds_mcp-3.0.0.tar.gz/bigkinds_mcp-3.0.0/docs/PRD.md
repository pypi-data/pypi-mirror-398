# PRD: BigKinds MCP Server

> Product Requirements Document for BigKinds News Search & Analysis MCP Server

## 1. Introduction

### 1.1 Product Overview
BigKinds MCP Server는 한국언론진흥재단의 BigKinds 뉴스 데이터베이스를 Claude Desktop 및 기타 MCP 클라이언트에서 사용할 수 있게 하는 Model Context Protocol 서버입니다.

### 1.2 Background
- **BigKinds**: 1990년부터 현재까지 한국 주요 언론사 뉴스 기사를 수집한 국내 최대 뉴스 데이터베이스
- **MCP (Model Context Protocol)**: Anthropic이 개발한 AI 모델과 외부 도구/데이터 연결 표준 프로토콜
- **Unofficial API**: 웹사이트 내부 HTTP 엔드포인트 활용

### 1.3 Document Version
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-15 | - | Initial PRD |

---

## 2. Problem Statement

### 2.1 Current Pain Points
- **P1**: AI 어시스턴트가 한국 뉴스 데이터에 실시간으로 접근할 수 없음
- **P2**: BigKinds 웹사이트 수동 검색은 반복적이고 시간 소모적
- **P3**: 뉴스 트렌드 분석과 연관어 분석을 자동화할 방법이 없음
- **P4**: 한국 시사 이슈에 대한 AI 분석이 outdated 정보에 의존

### 2.2 Target Users
| User Type | Description | Primary Need |
|-----------|-------------|--------------|
| **리서처** | 언론/미디어 연구자 | 뉴스 트렌드 분석, 키워드 비교 |
| **PR/마케터** | 기업 홍보/마케팅 담당자 | 브랜드 언급 모니터링, 이슈 추적 |
| **기자/에디터** | 언론인 | 배경 조사, 관련 기사 탐색 |
| **일반 사용자** | 시사에 관심 있는 개인 | 일일 이슈 브리핑, 뉴스 요약 |

### 2.3 Success Metrics
- **SM1**: MCP 클라이언트에서 뉴스 검색 응답 시간 < 3초
- **SM2**: 일일 API 호출 성공률 > 99%
- **SM3**: 사용자가 수동 검색 대비 80% 시간 절약

---

## 3. Solution Overview

### 3.1 Product Vision
> BigKinds의 뉴스 검색/분석 기능을 MCP 프로토콜로 완전히 포팅하여, AI 어시스턴트가 한국 뉴스 데이터를 자연어로 탐색하고 분석할 수 있게 함

### 3.2 Key Features
| Feature | Description | Priority |
|---------|-------------|----------|
| **뉴스 검색** | 키워드/날짜/언론사/카테고리 기반 검색 | P0 |
| **기사 상세** | 개별 기사 본문 및 메타데이터 조회 | P0 |
| **오늘의 이슈** | 일별 인기 뉴스 Top 10 조회 | P0 |
| **키워드 트렌드** | 시계열 기사 수 추이 분석 | P1 |
| **연관어 분석** | TF-IDF 기반 관련 키워드 추출 | P1 |
| **URL 스크래핑** | 외부 뉴스 URL 본문 추출 | P2 |

### 3.3 Out of Scope
- 관계도 분석 (브라우저 전용 API)
- 실시간 푸시 알림
- 뉴스 기사 저장/북마크
- 사용자 계정 관리

---

## 4. User Stories

### 4.1 뉴스 검색 (US1-US4)

**US1**: As a 리서처, I want to search news by keyword and date range so I can find relevant articles for my research.

**US2**: As a PR담당자, I want to filter news by specific publishers so I can monitor coverage from major outlets.

**US3**: As a 기자, I want to sort results by date or relevance so I can find the most recent or most relevant articles.

**US4**: As a 일반사용자, I want to get article counts grouped by day/week/month so I can understand news volume trends.

### 4.2 기사 조회 (US5-US6)

**US5**: As a 리서처, I want to get full article content with images so I can analyze the complete story.

**US6**: As a 기자, I want to scrape external news URLs so I can access articles from other sources.

### 4.3 이슈 분석 (US7-US9)

**US7**: As a 일반사용자, I want to see today's top issues so I can stay updated on current events.

**US8**: As a 마케터, I want to analyze keyword trends over time so I can identify rising topics.

**US9**: As a 리서처, I want to find related keywords for a topic so I can expand my research scope.

### 4.4 유틸리티 (US10-US12)

**US10**: As a 사용자, I want to get current Korean time so I can use accurate dates in queries.

**US11**: As a 사용자, I want to search publisher/category codes so I can use correct filter values.

**US12**: As a 사용자, I want to list all available publishers and categories so I can see filtering options.

---

## 5. Technical Requirements

### 5.1 MCP Tools Specification

#### 5.1.1 Public Tools (인증 불필요)

| Tool ID | Tool Name | Parameters | Returns |
|---------|-----------|------------|---------|
| T1 | `search_news` | keyword*, start_date*, end_date*, page, page_size, providers[], categories[], sort_by | SearchResult |
| T2 | `get_article_count` | keyword*, start_date*, end_date*, group_by, providers[] | CountResult |
| T3 | `get_article` | news_id*, include_full_content, include_images | ArticleDetail |
| T4 | `scrape_article_url` | url*, extract_images | ScrapedContent |
| T5 | `get_today_issues` | date, category | IssueList |
| T6 | `get_current_korean_time` | - | KSTTime |
| T7 | `find_category` | query*, category_type | CategoryMatch[] |
| T8 | `list_providers` | - | Provider[] |
| T9 | `list_categories` | - | Category[] |

#### 5.1.2 Private Tools (로그인 필요)

| Tool ID | Tool Name | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| T10 | `get_keyword_trends` | keyword*, start_date*, end_date*, interval, providers[], categories[] | TrendData | Required |
| T11 | `get_related_keywords` | keyword*, start_date*, end_date*, max_news_count, result_number, providers[], categories[] | RelatedWords | Required |

> `*` = Required parameter

### 5.2 MCP Resources

| Resource ID | URI Pattern | Description |
|-------------|-------------|-------------|
| R1 | `stats://providers` | 언론사 목록 (Markdown) |
| R2 | `stats://categories` | 카테고리 목록 (Markdown) |
| R3 | `news://{keyword}/{date}` | 날짜별 뉴스 검색 결과 |
| R4 | `article://{news_id}` | 개별 기사 정보 |

### 5.3 MCP Prompts

| Prompt ID | Name | Parameters | Use Case |
|-----------|------|------------|----------|
| PR1 | `news_analysis` | keyword, start_date, end_date, analysis_type | 뉴스 분석 |
| PR2 | `trend_report` | keyword, days | 트렌드 리포트 |
| PR3 | `issue_briefing` | date | 일일 브리핑 |
| PR4 | `keyword_comparison` | keywords[], start_date, end_date | 키워드 비교 |

### 5.4 Data Models

```
SearchResult {
  success: boolean
  total_count: integer
  page: integer
  page_size: integer
  total_pages: integer
  articles: Article[]
}

Article {
  news_id: string
  title: string
  summary: string
  publisher: string
  category: string
  news_date: string (YYYY-MM-DD)
  url: string
}

TrendData {
  success: boolean
  keyword: string
  date_range: string
  interval: integer
  interval_name: string
  trends: TrendItem[]
}

TrendItem {
  keyword: string
  data: {date: string, count: integer}[]
  total_count: integer
}

RelatedWords {
  success: boolean
  keyword: string
  related_words: {name: string, weight: float, tf: integer}[]
  news_count: integer
}
```

### 5.5 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/news/search.do` | POST | No | 뉴스 검색 |
| `/search/trendReportData2.do` | GET | No | 오늘의 이슈 |
| `/api/analysis/keywordTrends.do` | POST | Yes | 키워드 트렌드 |
| `/api/analysis/relationalWords.do` | POST | Yes | 연관어 분석 |
| `/api/account/signin.do` | POST | - | 로그인 |

---

## 6. Acceptance Criteria

### 6.1 Core Features (P0)

#### AC1: search_news
- [x] 키워드 필수, 빈 키워드 시 에러 반환
- [x] start_date, end_date 필수, YYYY-MM-DD 형식 검증
- [x] page_size 최대 100 제한
- [x] sort_by="both" 시 date+relevance 병합, news_id로 중복 제거
- [x] providers[] 필터 적용 시 해당 언론사만 반환
- [x] categories[] 필터 적용 시 해당 카테고리만 반환
- [x] 응답에 total_count, page, total_pages 포함

#### AC2: get_article
- [x] news_id 필수
- [x] include_full_content=true 시 기사 본문 스크래핑
- [x] include_images=true 시 이미지 URL 목록 포함
- [x] 존재하지 않는 news_id 시 적절한 에러 반환

#### AC3: get_today_issues
- [x] date 미지정 시 오늘 날짜 사용 (KST 기준)
- [x] category 필터 지원 (전체/서울/경인강원/충청/경상/전라제주/AI)
- [x] Top 10 이슈 목록 반환

### 6.2 Analysis Features (P1)

#### AC4: get_keyword_trends
- [x] 환경변수 미설정 시 명확한 에러 메시지 반환
- [x] 자동 로그인 수행 (세션 유지)
- [x] interval 옵션: 1(일간), 2(주간), 3(월간), 4(연간)
- [x] 콤마로 구분된 다중 키워드 지원
- [x] 응답에 trends[], total_data_points 포함

#### AC5: get_related_keywords
- [x] 환경변수 미설정 시 명확한 에러 메시지 반환
- [x] max_news_count 옵션: 50, 100, 200, 500, 1000
- [x] related_words를 weight 내림차순 정렬
- [x] top_words에 상위 10개 포함

### 6.3 Utility Features (P2)

#### AC6: scrape_article_url
- [x] URL 유효성 검증
- [x] 네이버 뉴스, 다음 뉴스, 언론사 직접 URL 지원
- [x] 스크래핑 실패 시 적절한 에러 반환

#### AC7: find_category
- [x] query로 언론사명/카테고리명 검색
- [x] 부분 매칭 지원 (예: "경향" → "경향신문")
- [x] category_type 필터: "provider" 또는 "category"

### 6.4 Non-Functional

#### AC8: Performance
- [x] 뉴스 검색 응답 < 3초
- [x] 캐시 적중 시 응답 < 100ms
- [x] 동시 요청 10개 이상 처리

#### AC9: Reliability
- [x] API 실패 시 재시도 (최대 3회)
- [x] 네트워크 타임아웃 30초
- [x] 에러 응답에 success=false, error 메시지 포함

#### AC10: Caching
- [x] 검색 결과 캐시 TTL: 5분
- [x] 기사 상세 캐시 TTL: 30분
- [x] 트렌드/연관어 캐시 TTL: 10분
- [x] 언론사/카테고리 목록 캐시 TTL: 24시간

---

## 7. Constraints

### 7.1 Technical Constraints
- **TC1**: Python 3.12+ 필수 (FastMCP 요구사항)
- **TC2**: Unofficial API 사용으로 엔드포인트 변경 가능성 있음
- **TC3**: 관계도 분석 API 제외 (브라우저 전용)
- **TC4**: httpx 비동기 HTTP 클라이언트 사용

### 7.2 Business Constraints
- **BC1**: BigKinds 계정 필요 (분석 API)

### 7.3 Security Constraints
- **SC1**: 비밀번호 환경변수로만 전달 (하드코딩 금지)
- **SC2**: SSL 인증서 검증 (verify=True, 개발 시 예외)
- **SC3**: 세션 토큰 메모리에만 저장 (파일 저장 금지)

---

## 8. Dependencies

### 8.1 External Dependencies
| Dependency | Version | Purpose |
|------------|---------|---------|
| fastmcp | >=1.0.0 | MCP 서버 프레임워크 |
| httpx | >=0.27.0 | 비동기 HTTP 클라이언트 |
| pydantic | >=2.0.0 | 데이터 검증 |
| beautifulsoup4 | >=4.12.0 | HTML 파싱 |
| cachetools | >=5.0.0 | TTL 캐시 |

### 8.2 Internal Dependencies
| Module | Purpose |
|--------|---------|
| bigkinds/client.py | 기존 동기 HTTP 클라이언트 (래핑) |
| bigkinds/models.py | Pydantic 모델 정의 |
| bigkinds/article_scraper.py | 기사 본문 스크래핑 |

---

## 9. Milestones

### M1: Core Search (완료)
- [x] search_news 구현
- [x] get_article_count 구현
- [x] get_article 구현
- [x] 기본 캐싱 구현

### M2: Content Access (완료)
- [x] scrape_article_url 구현
- [x] get_today_issues 구현
- [x] MCP Resources 구현
- [x] MCP Prompts 구현

### M3: Analysis (완료)
- [x] 로그인 기능 구현
- [x] get_keyword_trends 구현
- [x] get_related_keywords 구현
- [x] 세션 유지 로직

### M4: Cleanup & Polish (완료)
- [x] 관계도 분석 코드 제거
- [x] deprecated 파일 정리
- [x] 에러 핸들링 개선 (AC1, AC9 충족)
- [x] PRD AC 기반 테스트 작성
- [x] 캐시 TTL 표준화 (AC10 충족)

### M5: Enhancement (향후)
- [ ] 키워드 비교 분석 프롬프트
- [ ] 배치 검색 지원
- [ ] 결과 내보내기 (CSV/JSON)
- [ ] 사용량 통계 대시보드

---

## 10. Appendix

### A. Environment Variables

```bash
# Required for Private Tools (T10, T11)
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password

# Optional
BIGKINDS_TIMEOUT=30          # API 타임아웃 (초)
BIGKINDS_CACHE_TTL=300       # 기본 캐시 TTL (초)
BIGKINDS_LOG_LEVEL=INFO      # 로그 레벨
```

### B. Claude Desktop Configuration

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

### C. Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | 로그인 필요 (환경변수 미설정) |
| `AUTH_FAILED` | 로그인 실패 (잘못된 자격증명) |
| `INVALID_PARAMS` | 파라미터 유효성 검증 실패 |
| `API_ERROR` | BigKinds API 호출 실패 |
| `SCRAPE_ERROR` | 기사 스크래핑 실패 |
| `RATE_LIMITED` | 요청 제한 초과 |
| `TIMEOUT` | 요청 타임아웃 |

### D. Related Documents

| Document | Path | Description |
|----------|------|-------------|
| Architecture | `docs/MCP_ARCHITECTURE_V2.md` | 시스템 아키텍처 상세 |
| Implementation | `docs/IMPLEMENTATION_WORKFLOW.md` | 구현 워크플로 |
| API Guide | `docs/MCP_GUIDE.md` | MCP 사용 가이드 |
