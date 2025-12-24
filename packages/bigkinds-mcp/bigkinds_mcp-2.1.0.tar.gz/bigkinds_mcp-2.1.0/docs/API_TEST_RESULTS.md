# BigKinds API 테스트 결과

테스트 일시: 2024-12-15 (업데이트)
테스트 계정: ssalssi1@pukyong.ac.kr

## 요약

| API | 상태 | 비고 |
|-----|------|------|
| 로그인 | ✅ 정상 | `/api/account/signin.do` |
| 뉴스 검색 | ✅ 정상 | MCP 클라이언트 통해 작동 |
| 오늘의 이슈 | ✅ 정상 | `/search/trendReportData2.do` |
| 연관어 분석 | ✅ 정상 | 필수 파라미터 추가 후 정상 |
| 키워드 트렌드 | ✅ 정상 | `searchKey`, `indexName` 파라미터 추가 후 정상 |
| 관계도 분석 | ❌ 실패 | 302 → `/err/error400.do` 리다이렉트, 브라우저에서만 동작 |

## 상세 결과

### 1. 로그인 API ✅

```
엔드포인트: POST /api/account/signin.do
상태: 200 OK
응답: {"userSn": "20247212", ...}
```

**결론**: 정상 작동. `userSn` 필드가 있으면 로그인 성공.

### 2. 뉴스 검색 API ✅

```
엔드포인트: POST /api/news/search.do
상태: 200 OK
결과: 9817건 검색, 페이지네이션 정상
```

**결론**: MCP `BigKindsClient`를 통해 정상 작동. 직접 httpx 호출 시 400 에러 발생하나, 기존 클라이언트의 requests 세션 관리 방식 사용 시 정상.

### 3. 오늘의 이슈 API ✅

```
엔드포인트: GET /search/trendReportData2.do
파라미터: SEARCH_DATE, category
상태: 200 OK
```

**결론**: 정상 작동. 날짜별 Top 이슈 조회 가능.

### 4. 연관어 분석 API ✅

```
엔드포인트: POST /api/analysis/relationalWords.do
상태: 200 OK
결과: 33개 연관어, 50개 문서 분석
Top 3: 인공지능, 생성형 AI, AI 디지털교과서
```

**필수 파라미터** (누락 시 500 에러):
```json
{
  "searchKey": "키워드",   // ⚠️ 필수
  "indexName": "news",    // ⚠️ 필수
  "analysisType": "relational_word",
  "sortMethod": "score",
  "startNo": 1,
  "isTmUsable": true
}
```

**결론**: 정상 작동. TF-IDF 기반 연관어 분석 가능.

### 5. 키워드 트렌드 API ✅

```
엔드포인트: POST /api/analysis/keywordTrends.do
상태: 200 OK
응답: {"root":[{"data":[{"c":9496,"d":"2024"}],"keyword":"AI"}]}
```

**필수 파라미터** (누락 시 빈 결과):
```json
{
  "searchKey": "키워드",   // ⚠️ 필수 (keyword와 동일)
  "indexName": "news",    // ⚠️ 필수
  "keyword": "키워드",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "interval": 1
}
```

**결론**: `searchKey`, `indexName` 파라미터 추가 후 정상 작동.

### 6. 관계도 분석 API ❌

```
엔드포인트: POST /news/getNetworkDataAnalysis.do
상태: 302 Redirect → /err/error400.do
```

**원인 분석** (Playwright 브라우저 테스트 결과):
- 브라우저에서 로그인 후 호출: **200 OK** ✅
- httpx에서 로그인 후 직접 호출: **302 Redirect** ❌

**차이점**:
| 구분 | 연관어/키워드 트렌드 | 관계도 분석 |
|------|---------------------|------------|
| 경로 | `/api/analysis/*` | `/news/*` |
| 타입 | REST API | 웹 페이지용 엔드포인트 |
| httpx | ✅ 가능 | ❌ 불가 |

**추정 원인**:
1. 브라우저 JavaScript가 설정하는 추가 쿠키/토큰 필요
2. CSRF 토큰 검증
3. Referer/Origin 페이지 검증

**결론**: 브라우저 컨텍스트 의존성으로 인해 직접 API 호출 불가. Playwright 자동화 또는 BigKinds API 권한 문의 필요.

## MCP 서버 구현 현황

### 정상 작동하는 Tools (9개)

| Tool | 설명 | 상태 |
|------|------|------|
| `search_news` | 뉴스 검색 | ✅ |
| `get_article_count` | 기사 수 조회 | ✅ |
| `get_article` | 기사 상세 | ✅ |
| `scrape_article_url` | URL 스크래핑 | ✅ |
| `get_today_issues` | 오늘의 이슈 | ✅ |
| `get_current_korean_time` | 현재 한국 시간 | ✅ |
| `find_category` | 코드 검색 | ✅ |
| `list_providers` | 언론사 목록 | ✅ |
| `list_categories` | 카테고리 목록 | ✅ |

### 추가된 시각화 Tools (3개)

| Tool | 설명 | 상태 |
|------|------|------|
| `get_related_keywords` | 연관어 분석 | ✅ 정상 |
| `get_keyword_trends` | 키워드 트렌드 | ✅ 정상 |
| `get_network_analysis` | 관계도 분석 | ❌ 브라우저 전용 |

## 권장 사항

1. **연관어 분석** ✅ - MCP Tool로 활용 권장. 정상 작동.

2. **키워드 트렌드** ✅ - MCP Tool로 활용 권장. `searchKey`, `indexName` 필수 파라미터 추가 후 정상 작동.

3. **관계도 분석** ❌ - 직접 API 호출 불가. 해결 방안:
   - Playwright 브라우저 자동화로 브라우저 세션에서 API 호출
   - BigKinds 고객센터에 API 권한/문서 문의
   - BigKinds Lab API (api.bigkindslab.or.kr) 활용 검토

## 환경 변수

```bash
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password
```
