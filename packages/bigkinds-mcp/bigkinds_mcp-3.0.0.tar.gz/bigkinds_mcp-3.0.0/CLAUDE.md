# BigKinds MCP Server Project

## 참조 문서 인덱스

| 문서 | 경로 | 설명 |
|------|------|------|
| **PRD v3.0** | `docs/PRD_V2.md` | 제품 요구사항 문서 (US13-US24, AC11-AC23) - 시각화 추가 |
| **전문가 리뷰** | `docs/SPEC_PANEL_REVIEW.md` | 5인 전문가 패널 분석 (2025-12-20) |
| 워크플로 v3 | `docs/IMPLEMENTATION_WORKFLOW_V3.md` | Phase 1-3 구현 워크플로 (AC11-AC17) |
| **아키텍처 v3** | `docs/MCP_ARCHITECTURE_V2.md` | 시스템 아키텍처 (15개 Tools + 5개 Visualization Utilities) |
| MCP 서버 설계 | `docs/MCP_SERVER_DESIGN.md` | 전체 아키텍처, Tools/Resources/Prompts 스펙 |
| **시각화 연구** | `claudedocs/research_news_visualization_patterns_2025-12-21.md` | CHI 2024 디자인 패턴, 한국 데이터 저널리즘 사례 |

## 핵심 사항

### 비공식 API 활용
- `www.bigkinds.or.kr`의 내부 HTTP 엔드포인트 사용
- 인증 없음 (세션/쿠키 기반 추정)
- API 제한사항 고려하여 구현

### 기존 코드 재사용
- `client.py` → `AsyncBigKindsClient`로 래핑
- `article_scraper.py` → `AsyncArticleScraper`로 래핑
- `models.py` → MCP 스키마로 변환

### 정렬 방식 (sort_by)
- `"both"` (기본값): date + relevance 두 번 호출 후 병합, news_id로 중복 제거
- `"date"`: 날짜순 (최신순)
- `"relevance"`: 관련도순

## 기술 스택

- Python 3.12+
- FastMCP (mcp>=1.0.0)
- httpx (비동기 HTTP)
- Pydantic v2
- BeautifulSoup4 (스크래핑)
- cachetools (인메모리 캐시)

## 프로젝트 구조

```
bigkinds/
├── src/bigkinds_mcp/       # MCP 서버
│   ├── server.py           # 엔트리포인트
│   ├── tools/              # MCP Tools
│   ├── resources/          # MCP Resources
│   ├── prompts/            # MCP Prompts
│   ├── core/               # 비동기 어댑터, 캐시, Circuit Breaker
│   ├── models/             # MCP 스키마, 한글 에러 메시지
│   ├── validation/         # 날짜 검증 등 (v2.0)
│   └── visualization/      # 시각화 유틸리티 (v3.0) ⏳
│       ├── chart_formatter.py
│       ├── wordcloud_formatter.py
│       ├── timeline_formatter.py
│       ├── comparison_formatter.py
│       ├── heatmap_formatter.py
│       └── colors.py
├── client.py               # 기존 HTTP 클라이언트
├── models.py               # 기존 Pydantic 모델
├── article_scraper.py      # 기존 스크래퍼
└── searcher.py             # 기존 고수준 검색 (참조용)
```

## 명령어

```bash
# 의존성 설치
uv sync

# MCP 서버 실행
uv run bigkinds-mcp

# 테스트
uv run pytest
```

## 배포

태그 푸시 시 GitHub Actions가 자동으로 PyPI에 배포합니다.

```bash
# 1. pyproject.toml 버전 업데이트
# 2. 커밋 & 푸시
git add -A && git commit -m "chore: bump version to vX.Y.Z"
git push origin main

# 3. 태그 생성 & 푸시 → 자동 배포 트리거
git tag vX.Y.Z
git push origin vX.Y.Z
```

배포 상태 확인: `gh run list --limit 3`

## Claude Desktop 설정

### 로컬 stdio 모드

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uvx",
      "args": ["bigkinds-mcp"]
    }
  }
}
```

### Remote MCP Server (HTTP/SSE)

원격 서버가 배포되어 있습니다:

| 항목 | 값 |
|------|-----|
| **서버 IP** | `100.114.192.51` |
| **내부 포트** | `58002` (MCP), `56379` (Redis) |
| **영구 URL** | `https://bigkinds.seolcoding.com` |
| **API Key** | `bigkinds_mcp_secret_key_2025` |
| **Health Check** | `GET /health` |

#### 구성 요소

| 구성요소 | 실행 방식 | 설명 |
|---------|----------|------|
| bigkinds-mcp | Docker | MCP Remote Server (HTTP/SSE) |
| redis | Docker | 캐시 서버 |
| cloudflared | systemd | Cloudflare Named Tunnel (자동 시작) |

#### API 호출 예시

```bash
# Health check
curl https://bigkinds.seolcoding.com/health

# 도구 목록
curl -H "x-api-key: bigkinds_mcp_secret_key_2025" \
  https://bigkinds.seolcoding.com/api/tools

# 뉴스 검색
curl -X POST \
  -H "x-api-key: bigkinds_mcp_secret_key_2025" \
  -H "Content-Type: application/json" \
  -d '{"keyword":"AI","start_date":"2025-12-01","end_date":"2025-12-15"}' \
  https://bigkinds.seolcoding.com/api/tools/search_news
```

#### 서버 관리 (SSH)

```bash
# 접속
ssh wai-3090ti@100.114.192.51

# Docker 컨테이너 상태
cd ~/bigkinds-mcp && sudo docker compose ps

# Docker 로그 확인
sudo docker compose logs -f bigkinds-mcp

# Docker 재시작
sudo docker compose restart

# Cloudflare Tunnel 상태
sudo systemctl status cloudflared-tunnel

# Cloudflare Tunnel 재시작
sudo systemctl restart cloudflared-tunnel
```

## 구현 완료 사항

### MCP Tools (15개)

#### Public Tools - 인증 불필요 (10개)
- [x] search_news: 뉴스 검색 (sort_by: both/date/relevance)
- [x] get_article_count: 기사 수 조회 (group_by: total/day/week/month)
- [x] get_article: 기사 상세 (**v1.4.0**: BigKinds detailView API로 전체 본문 반환, 실패 시 URL 스크래핑 폴백)
- [x] scrape_article_url: URL 스크래핑
- [x] get_article_thumbnail: 대표 이미지 추출 (**v1.7.3**: og:image 우선, 없으면 본문 이미지)
- [x] get_today_issues: 오늘의 인기 이슈 (키워드 없이 핫이슈 조회)
  - **v1.7.2**: 지원 카테고리를 "전체", "AI"로 제한 (API 실제 지원 범위에 맞춤)
  - 지원 카테고리: "전체" (기본값), "AI" (AI 선정 이슈)
- [x] get_current_korean_time: 현재 한국 시간 조회 (KST)
- [x] find_category: 언론사/카테고리 코드 검색
- [x] list_providers: 전체 언론사 목록
- [x] list_categories: 전체 카테고리 목록

#### Private Tools - 로그인 필요 (2개)
- [x] get_keyword_trends: 키워드 트렌드 분석 (시간축 그래프)
- [x] get_related_keywords: 연관어 분석 (TF-IDF 기반)

#### Utility Tools - MCP 확장 기능 (4개)
- [x] compare_keywords: 여러 키워드(2-10개) 기사 수 비교 분석
- [x] smart_sample: 대용량 검색 결과에서 대표 샘플 추출 (stratified/latest/random)
  - **v1.5.2**: random 전략 버그 수정 (API 페이지네이션 15페이지 제한 반영)
- [x] export_all_articles: 전체 기사 일괄 내보내기 (JSON/CSV/JSONL, 최대 50,000건)
  - `include_content=True`: BigKinds detailView API로 전체 본문 획득 (v1.4.0 개선)
  - `analysis_code`: Python 분석 템플릿 자동 반환 (**v1.5.0**)
  - 참고: 검색 API는 200자 요약만 반환하지만, detailView API로 전체 본문 획득 가능
- [x] analyze_timeline: 타임라인 분석 및 주요 이벤트 자동 탐지 (**v1.9.0**)
  - NLP 기반 스파이크 탐지, 키워드 추출, 대표 기사 선정
  - 25만건 이상 대용량 기사에서 시간별 주요 사건 자동 추출
  - 월별 기사 수가 평균의 1.5배 이상인 시점을 이벤트로 탐지

#### 대용량 분석 워크플로우 (v1.5.0)
- search_news 결과에 `workflow_hint` 필드 추가 (100건 이상 시 로컬 내보내기 권장)
- export_all_articles 결과에 `analysis_code` 필드 추가 (Python 분석 템플릿)
- large_scale_analysis MCP Prompt로 LLM에게 워크플로우 가이드 제공

#### Visualization Utilities - 시각화 유틸리티 (v3.0) ⏳
> 차트 라이브러리(ECharts, Plotly, Chart.js) 호환 데이터 포맷 생성

| 함수 | 설명 | 입력 → 출력 |
|------|------|------------|
| `format_chart_data` | 차트용 데이터 포맷팅 | 시계열 데이터 → ECharts/Plotly JSON |
| `format_wordcloud_data` | 워드클라우드 데이터 | 키워드 목록 → {text, weight}[] |
| `format_timeline_data` | 타임라인 데이터 | 이벤트 목록 → TimelineJS JSON |
| `format_comparison_data` | 비교 차트 데이터 | 다중 시계열 → 시리즈 배열 |
| `format_heatmap_data` | 히트맵 데이터 | 2D 데이터 → 매트릭스 형식 |

**사용 예시:**
```python
from bigkinds_mcp.visualization import format_chart_data, format_wordcloud_data

# 키워드 트렌드 → ECharts 라인 차트
trends = await get_keyword_trends("AI", "2024-12-01", "2024-12-15")
chart_data = format_chart_data(trends["trends"][0]["data"], chart_type="line", format="echarts")

# 연관어 → 워드클라우드
keywords = await get_related_keywords("AI", "2024-12-01", "2024-12-15")
wordcloud = format_wordcloud_data(keywords["related_words"], max_items=30)
```

#### 제거된 Tools
- ~~get_network_analysis~~: 관계도 분석 (브라우저 전용 API, httpx 호출 불가)

### MCP Resources (4개)
- [x] stats://providers: 언론사 코드 목록 (마크다운)
- [x] stats://categories: 카테고리 코드 목록 (마크다운)
- [x] news://{keyword}/{date}: 특정 날짜 뉴스 검색 결과
- [x] article://{news_id}: 개별 기사 정보

### MCP Prompts (4개)
- [x] news_analysis: 뉴스 분석 프롬프트 (summary/sentiment/trend/comparison)
- [x] trend_report: 트렌드 리포트 생성 프롬프트
- [x] issue_briefing: 일일 이슈 브리핑 프롬프트
- [x] large_scale_analysis: 대용량 분석 워크플로우 가이드 (**v1.5.0**)

## 테스트 결과

### Public Tools
- search_news: ✅ OK (9817건 검색, 페이지네이션 정상)
- sort_by="both": ✅ OK (date+relevance 병합, 중복 제거)
- get_article: ✅ OK (detailView API로 전체 본문 반환, source: "bigkinds_api") **(v1.4.0)**
- scrape_article_url: ✅ OK (네이버 뉴스 등)
- get_today_issues: ✅ OK (일별 Top 10 이슈, 클라이언트 측 카테고리 필터링) **(v1.5.2)**
- get_current_korean_time: ✅ OK (KST 시간대 정상)
- find_category: ✅ OK (언론사/카테고리 검색 정상)

### Private Tools (로그인 필요)
- get_keyword_trends: ✅ OK (로그인 후 시계열 데이터 반환)
- get_related_keywords: ✅ OK (50건 분석, 32개 연관어 추출)

### Utility Tools
- compare_keywords: ✅ OK (2-10개 키워드 비교, 일별/주별/월별 집계)
- smart_sample: ✅ OK (stratified/latest/random 샘플링, API 15페이지 제한 반영) **(v1.5.2)**
- export_all_articles: ✅ OK (JSON/CSV/JSONL 내보내기, include_content 지원)

### Resources/Prompts
- Resources/Prompts: ✅ OK (정상 등록 확인)

## API 엔드포인트

| 기능 | 엔드포인트 | 인증 | 설명 |
|------|-----------|------|------|
| 뉴스 검색 | `/api/news/search.do` | 불필요 | POST, keyword 필수, 200자 요약만 반환 |
| **기사 상세** | `/news/detailView.do` | 불필요 | GET, 전체 본문(CONTENT) 반환, 세션 쿠키 필요 (**v1.4.0**) |
| 오늘의 이슈 | `/search/trendReportData2.do` | 불필요 | GET, 세션 쿠키 필요 |
| 키워드 트렌드 | `/api/analysis/keywordTrends.do` | **필수** | POST, 로그인 필수 |
| 연관어 분석 | `/api/analysis/relationalWords.do` | **필수** | POST, 로그인 필수 |
| ~~네트워크 분석~~ | ~~`/news/getNetworkDataAnalysis.do`~~ | - | 브라우저 전용, 제거됨 |

## 발견된 이슈

### 해결된 이슈

#### v1.5.2 (2025-12-15)
- **`get_today_issues` 카테고리 버그 수정**:
  - 문제: API가 `category=전체`만 지원, 다른 카테고리 전달 시 404 에러
  - 해결: 항상 `전체`로 API 호출 후 클라이언트 측에서 `topic_category` 필드로 필터링
  - 실제 카테고리 (지역/유형 기반): "전체", "서울", "경인강원", "충청", "경상", "전라제주", "AI"
- **`smart_sample` random 전략 버그 수정**:
  - 문제 1: `sample_size // page_size`가 0이 되어 빈 결과 반환
  - 문제 2: BigKinds API가 약 15-17페이지까지만 페이지네이션 지원 (이후 빈 결과)
  - 해결: 최소 1페이지 샘플링 보장 + API 페이지 제한 15로 설정

#### 이전 버전
- `PROVIDER` 필드가 언론사명 (models.py에서 `PUBLISHER` 대신 `PROVIDER` 매핑 필요)
- provider_codes는 "경향신문" 같은 이름이 아닌 "08100401" 같은 코드 형식

### 알려진 API 특성
- `get_keyword_trends` interval 파라미터 (**v1.5.1**): BigKinds API는 날짜 범위에 따라 자동으로 데이터 granularity를 조정합니다.
  - interval 값은 힌트로만 사용됨
  - 짧은 기간 (2주 이하): 연도별/월별 집계로 반환될 수 있음
  - 긴 기간 (1년 이상): 일별 데이터로 반환될 수 있음

### 제거된 기능
- **네트워크 분석 API** (`/news/getNetworkDataAnalysis.do`)
  - 브라우저에서 호출: 200 OK (정상)
  - httpx에서 직접 호출: 302 → `/err/error400.do` (실패)
  - JavaScript가 설정하는 추가 쿠키/토큰 또는 CSRF 검증 필요로 추정
  - **결론**: 브라우저 전용 API로 MCP에서 제외

## 환경변수

Private Tools (키워드 트렌드, 연관어 분석) 사용을 위해 환경변수 설정 필요:

```env
# 필수 (Private Tools)
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password

# 선택 (PRD AC9)
BIGKINDS_TIMEOUT=30          # API 타임아웃 (초)
BIGKINDS_MAX_RETRIES=3       # 최대 재시도 횟수
BIGKINDS_RETRY_DELAY=1.0     # 재시도 간격 (초)
```

## PRD Acceptance Criteria 충족 현황

**AC1-AC16 모두 충족 완료** (`docs/PRD_V2.md` 참조)

### Phase 2 (v1.7.0) - UX & Reliability 개선 사항
- **AC15**: 에러 메시지 한글화 ✅
  - `errors_kr.py`: 모든 ErrorCode에 대한 한글 메시지 맵핑
  - 에러 응답 구조: `{success: false, error: {code, message, solution, docs?, details?}}`
  - 자동 한글 메시지 적용: `error_response(code)` 호출 시 message 생략 가능
  - 모든 에러에 `solution` 필드 포함 (사용자 가이드)
  - 중요 에러에 `docs` 필드 추가 (문서 링크)
- **AC16**: Circuit Breaker 패턴 ✅
  - `CircuitBreaker` 클래스: 3-state machine (CLOSED, OPEN, HALF_OPEN)
  - `AsyncBigKindsClient`에 3개 독립 Circuit 통합:
    - `search_circuit`: 검색 API 보호
    - `detail_circuit`: 상세 API 보호
    - `visualization_circuit`: 시각화 API 보호
  - 설정: 5회 연속 실패 시 OPEN, 30초 복구 타임아웃
  - 캐시 fallback: Circuit OPEN 시 캐시 데이터 반환
  - 테스트: 17개 (unit 11개 + integration 6개)

### Phase 1 (v1.6.0) - High Priority 개선 사항
- **AC11**: 병렬 API 호출 지원 ✅
  - `search_news_parallel` 함수 및 `search_news_batch` MCP tool 추가
  - Rate limiting (3 req/sec) + Semaphore (max 5 concurrent)
  - 55% 성능 향상 (벤치마크 기준)
- **AC12**: 날짜 검증 강화 ✅
  - `DateValidator` 클래스 (4개 검증 규칙)
  - 새 ErrorCode: INVALID_DATE_FORMAT, FUTURE_DATE_NOT_ALLOWED, DATE_TOO_OLD, INVALID_DATE_ORDER
  - 모든 날짜 기반 tools에 통합 (search_news, get_article_count, visualization tools)
- **AC13**: API 스키마 strict 검증 ✅
  - Pydantic strict mode (`strict=True`, `extra='forbid'`)
  - `StrictBaseModel` base class 도입
  - `validate_api_response` 래퍼 함수로 에러 로깅 강화
- **AC14**: 진행률 피드백 ✅
  - `ProgressTracker` 클래스 (threshold: 5000, interval: 10%)
  - ETA 계산 및 실시간 로그
  - `export_all_articles`에 통합

### 기존 구현 (v1.0-v1.5)
- **AC1**: 파라미터 유효성 검증 (Pydantic 스키마)
- **AC9**: 재시도 로직 (최대 3회, 지수 백오프) + 타임아웃 30초
- **AC10**: 캐시 TTL (검색 5분, 기사 30분, 트렌드 10분)

테스트: `uv run pytest tests/integration/test_acceptance_criteria.py` (217 passed, 1 skipped)
