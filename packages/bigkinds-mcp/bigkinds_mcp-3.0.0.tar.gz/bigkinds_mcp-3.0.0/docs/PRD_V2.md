# PRD v3.0: BigKinds MCP Server - Quality, Performance & Visualization

> 품질 개선, 성능 최적화 및 시각화 지원을 위한 제품 요구사항 문서

## 1. 개정 이력

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-15 | - | Initial PRD |
| 2.0 | 2025-12-16 | - | 품질/성능/보안 개선 |
| 2.1 | 2025-12-20 | - | 전문가 리뷰 반영, AC 완료 마킹 |
| **3.0** | **2025-12-21** | **-** | **시각화 유틸리티 기능 추가 (US20-US24)** |

## 2. v3.0 개선 목표

### 2.1 비전
> BigKinds MCP를 엔터프라이즈급 품질 표준으로 개선하고, **데이터 시각화 유틸리티**를 제공하여 뉴스 분석 결과를 효과적으로 표현

### 2.2 핵심 가치 제안
- **신뢰성**: 엣지 케이스 검증 강화로 예기치 않은 오류 방지
- **성능**: 병렬 API 호출 지원으로 응답 시간 단축
- **보안**: Circuit Breaker 패턴으로 API 장애 대응력 강화
- **사용성**: 한글 에러 메시지와 진행률 피드백으로 UX 개선
- **시각화**: 차트 데이터 포맷팅, 워드클라우드, 타임라인 등 시각화 지원 (v3.0 신규)

---

## 3. 새로운 User Stories (v2.0)

### US13: 병렬 API 호출 ✅
**As a** 파워 유저
**I want to** 여러 검색 조건을 동시에 실행할 수 있게
**So that** 복잡한 분석 작업 시간을 크게 단축할 수 있다

**Acceptance Criteria**:
- [x] 여러 `search_news` 호출을 asyncio.gather()로 병렬 실행 가능
- [x] 병렬 실행 시 rate limiting 자동 적용
- [x] 에러 발생 시에도 다른 요청은 계속 진행
- [x] 최대 5개 동시 요청 제한

### US14: 날짜 검증 강화 ✅
**As a** 사용자
**I want to** 잘못된 날짜 입력 시 명확한 에러를 받고
**So that** 검색 결과가 예상과 다른 상황을 방지할 수 있다

**Acceptance Criteria**:
- [x] 미래 날짜 입력 시 명확한 에러 메시지 반환
- [x] 1990-01-01 이전 날짜 거부 (BigKinds 데이터 범위)
- [x] end_date < start_date 시 에러 반환
- [x] 잘못된 형식(YYYY-MM-DD 아님) 시 에러 반환

### US15: API 스키마 검증 ✅
**As a** 개발자
**I want to** BigKinds API 응답이 예상과 다를 때 즉시 알림받고
**So that** silent fail 없이 문제를 빠르게 파악할 수 있다

**Acceptance Criteria**:
- [x] Pydantic strict 모드로 필드 타입 엄격 검증
- [x] 필수 필드 누락 시 명시적 ValidationError 발생
- [x] 스키마 불일치 로깅 (디버깅용)
- [x] fallback 값 제공 여부 선택 가능

### US16: 진행률 피드백 ✅
**As a** 사용자
**I want to** 대용량 작업 진행 상황을 실시간으로 보고
**So that** 작업이 멈춘 게 아닌지 확인하고 예상 시간을 알 수 있다

**Acceptance Criteria**:
- [x] export_all_articles 실행 시 진행률 로깅 (10% 단위)
- [x] Claude에게 중간 상태 메시지 전달
- [x] 예상 완료 시간 표시 (선택사항)
- [ ] 취소 가능 여부 표시 (선택사항) - *향후 개선*

### US17: 한글 에러 메시지 ✅
**As a** 한국어 사용자
**I want to** MCP Tool 에러 메시지를 한국어로 받고
**So that** 문제 해결 방법을 빠르게 이해할 수 있다

**Acceptance Criteria**:
- [x] MCP Tool 에러 메시지 한국어 번역 (15개 ErrorCode)
- [x] 해결 방법(solution) 포함
- [x] 에러 코드와 한글 설명 병기
- [x] 문서 링크 제공 (해당 시)

### US18: Circuit Breaker ✅
**As a** 시스템 관리자
**I want to** BigKinds API 장애 시 자동으로 fallback되고
**So that** 전체 서비스가 중단되지 않고 부분 기능이라도 유지할 수 있다

**Acceptance Criteria**:
- [x] 연속 실패 5회 시 circuit open (30초 대기)
- [x] half-open 상태에서 1회 성공 시 circuit close
- [x] circuit open 시 캐시된 데이터 반환 (가능 시)
- [x] 상태 전환 시 로깅

### US19: Playwright 통합 ⏳ (Low Priority)
**As a** 개발자
**I want to** 브라우저 기반 E2E 테스트를 실행하고
**So that** 실제 사용자 시나리오를 검증할 수 있다

> **Note**: 네트워크 분석 API는 제외됨. E2E 회귀 테스트 목적으로만 유지.

**Acceptance Criteria**:
- [ ] Playwright MCP로 BigKinds 검색 워크플로우 테스트
- [ ] 세션/쿠키 획득 로직 검증
- [ ] 스크린샷 기반 회귀 테스트 (선택사항)

---

## 3.1 새로운 User Stories (v3.0 - 시각화)

### US20: 차트 데이터 포맷팅 ⏳
**As a** 데이터 분석가
**I want to** MCP 도구 결과를 차트 라이브러리에 바로 사용할 수 있는 형식으로 받고
**So that** 별도 변환 없이 시각화를 빠르게 생성할 수 있다

**Acceptance Criteria**:
- [ ] `format_chart_data()` 함수로 라인/바/파이 차트용 데이터 변환
- [ ] ECharts, Plotly, Chart.js 호환 JSON 포맷 지원
- [ ] 시계열 데이터 자동 정렬 및 결측값 처리

### US21: 워드클라우드 데이터 생성 ⏳
**As a** 뉴스 분석가
**I want to** 키워드 빈도 데이터를 워드클라우드용 형식으로 받고
**So that** 주요 키워드를 시각적으로 파악할 수 있다

**Acceptance Criteria**:
- [ ] `format_wordcloud_data()` 함수로 {text, weight} 배열 생성
- [ ] 연관어 분석 결과 자동 변환
- [ ] 최소/최대 가중치 정규화 옵션

### US22: 타임라인 시각화 데이터 ⏳
**As a** 기자/연구원
**I want to** 시간대별 이벤트를 타임라인 형식으로 받고
**So that** 사건 흐름을 시각적으로 표현할 수 있다

**Acceptance Criteria**:
- [ ] `format_timeline_data()` 함수로 TimelineJS 호환 JSON 생성
- [ ] 스파이크 탐지 결과를 주요 이벤트로 자동 마킹
- [ ] 대표 기사 제목/링크 포함

### US23: 트렌드 비교 차트 데이터 ⏳
**As a** 마케터
**I want to** 여러 키워드의 트렌드를 비교 차트용 데이터로 받고
**So that** 경쟁사/이슈 간 관심도를 비교 분석할 수 있다

**Acceptance Criteria**:
- [ ] `format_comparison_data()` 함수로 다중 시계열 데이터 생성
- [ ] 키워드별 색상 자동 할당
- [ ] 상대적 비율(%) 및 절대값 모드 지원

### US24: 히트맵 데이터 생성 ⏳
**As a** 편집자
**I want to** 시간대×카테고리 기사 분포를 히트맵용 데이터로 받고
**So that** 보도 패턴을 한눈에 파악할 수 있다

**Acceptance Criteria**:
- [ ] `format_heatmap_data()` 함수로 2D 매트릭스 생성
- [ ] 요일×시간, 월×카테고리 등 다양한 축 조합 지원
- [ ] 색상 스케일 정규화 옵션

---

## 4. 새로운 Acceptance Criteria (v2.0)

### AC11: 병렬 API 호출 (High Priority)
- [x] **AC11.1**: asyncio.gather()로 최대 5개 요청 동시 실행
- [x] **AC11.2**: 병렬 요청 시 각 요청별 독립적 에러 처리
- [x] **AC11.3**: rate limiting으로 429 에러 방지 (1초당 최대 3 요청)
- [x] **AC11.4**: 병렬 실행 전용 도우미 함수 제공 (`search_news_batch`)
- [x] **AC11.5**: 5개 초과 요청 시 Semaphore 기반 대기열 처리 (FIFO)

### AC12: 날짜 검증 강화 (High Priority)
- [x] **AC12.1**: 미래 날짜 입력 시 `FUTURE_DATE_NOT_ALLOWED` 에러 반환
- [x] **AC12.2**: 1990-01-01 이전 날짜 입력 시 `DATE_TOO_OLD` 에러 반환
- [x] **AC12.3**: end_date < start_date 시 `INVALID_DATE_ORDER` 에러 반환
- [x] **AC12.4**: 에러 메시지에 유효 범위 포함 (예: "1990-01-01 ~ 오늘")
- [x] **AC12.5**: 경계값 테스트 케이스:
  - 1989-12-31 → `DATE_TOO_OLD`
  - 1990-01-01 → 정상 처리 (하한 경계)
  - 오늘 날짜 → 정상 처리 (상한 경계)
  - 내일 날짜 → `FUTURE_DATE_NOT_ALLOWED`

### AC13: API 응답 스키마 검증 (High Priority)
- [x] **AC13.1**: Pydantic Config에 `strict=True`, `extra='forbid'` 설정
- [x] **AC13.2**: 필수 필드 누락 시 ValidationError 발생 (silent fail 금지)
- [x] **AC13.3**: 타입 불일치 시 명시적 에러 로그 (예: int 필드에 str 입력)
- [x] **AC13.4**: 스키마 검증 실패 시 API 응답 원본 로깅 (디버깅용)

### AC14: 진행률 피드백 (High Priority)
- [x] **AC14.1**: export_all_articles에서 10% 단위로 진행률 로깅
- [x] **AC14.2**: 로그 형식: `[Progress] 1000/10000 (10.0%) - ETA: 30s`
- [x] **AC14.3**: `ProgressTracker` 클래스로 ETA 계산 및 실시간 로그
- [x] **AC14.4**: 5000건 이상 작업 시에만 진행률 표시 (성능 고려)

### AC15: 에러 메시지 한글화 (Medium Priority)
- [x] **AC15.1**: `errors_kr.py`에 ErrorCode → 한글 메시지 매핑
- [x] **AC15.2**: 에러 응답 형식: `{"code": "INVALID_DATE", "message": "...", "solution": "...", "docs": "..."}`
- [x] **AC15.3**: 모든 MCP Tool 에러 핸들러에 한글 메시지 적용
- [x] **AC15.4**: 문서 링크 포함 (`docs` 필드, 주요 에러에 한함)
- [x] **AC15.5**: 대상 범위: MCP Tool 반환 에러 (총 15개 ErrorCode)

### AC16: Circuit Breaker 패턴 (Medium Priority)
- [x] **AC16.1**: 연속 실패 5회 시 circuit open (30초 차단)
- [x] **AC16.2**: half-open 상태에서 테스트 요청 1회 성공 시 circuit close
- [x] **AC16.3**: circuit open 시 캐시 데이터 반환 (TTL 무시)
- [x] **AC16.4**: 상태 전환 로깅: `[CircuitBreaker] search_circuit: CLOSED -> OPEN`
- [x] **AC16.5**: half-open 상태에서 실패 시 즉시 OPEN 복귀 (recovery_timeout 재시작)
- [x] **AC16.6**: API별 독립 Circuit (search, detail, visualization)

### AC17: 재시도 전략 고도화 (Medium Priority)
- [x] **AC17.1**: exponential backoff (1s, 2s, 4s) 유지
- [x] **AC17.2**: 5xx 에러 및 네트워크 오류만 재시도, 4xx는 즉시 실패
- [ ] **AC17.3**: 재시도 전 jitter 추가 (0~500ms 랜덤 대기) - *향후 개선*
- [x] **AC17.4**: 재시도 횟수 로깅

### AC18: Playwright 통합 테스트 (Low Priority)
> **Note**: 네트워크 분석 API는 이미 제외됨. E2E 회귀 테스트 목적으로만 유지.

- [ ] **AC18.1**: Playwright MCP로 BigKinds 검색 페이지 접속
- [ ] **AC18.2**: 검색어 입력 → 결과 확인 E2E 시나리오
- [ ] ~~**AC18.3**: 네트워크 분석 API 브라우저 호출 성공 검증~~ - *제거됨*
- [ ] **AC18.4**: 세션 쿠키 획득 로직 검증 (로그인 필요 API용)

---

## 4.1 새로운 Acceptance Criteria (v3.0 - 시각화)

### AC19: 차트 데이터 포맷팅 (High Priority)
- [ ] **AC19.1**: `format_chart_data(data, chart_type)` 함수 구현
  - 지원 타입: `line`, `bar`, `pie`, `area`
- [ ] **AC19.2**: ECharts 옵션 객체 직접 생성 가능
  ```json
  {
    "xAxis": {"type": "category", "data": ["2024-12", "2025-01"]},
    "yAxis": {"type": "value"},
    "series": [{"data": [150, 230], "type": "line"}]
  }
  ```
- [ ] **AC19.3**: Plotly trace 형식 지원
  ```json
  {"x": ["2024-12", "2025-01"], "y": [150, 230], "type": "scatter", "mode": "lines"}
  ```
- [ ] **AC19.4**: 시계열 데이터 자동 정렬 (날짜 오름차순)
- [ ] **AC19.5**: 결측값 처리 옵션: `null`, `0`, `interpolate`

### AC20: 워드클라우드 데이터 (Medium Priority)
- [ ] **AC20.1**: `format_wordcloud_data(keywords)` 함수 구현
- [ ] **AC20.2**: 출력 형식: `[{"text": "AI", "weight": 85}, ...]`
- [ ] **AC20.3**: 가중치 정규화: `min_weight`, `max_weight` 옵션 (기본 10-100)
- [ ] **AC20.4**: `get_related_keywords` 결과 직접 변환 지원
- [ ] **AC20.5**: 상위 N개 필터링 옵션 (기본 50개)

### AC21: 타임라인 데이터 (Medium Priority)
- [ ] **AC21.1**: `format_timeline_data(events)` 함수 구현
- [ ] **AC21.2**: TimelineJS 호환 JSON 형식:
  ```json
  {
    "events": [
      {
        "start_date": {"year": 2024, "month": 12, "day": 15},
        "text": {"headline": "AI 관련 기사 급증", "text": "..."},
        "media": {"url": "https://..."}
      }
    ]
  }
  ```
- [ ] **AC21.3**: `analyze_timeline` 스파이크 이벤트 자동 변환
- [ ] **AC21.4**: 대표 기사 링크 포함

### AC22: 비교 차트 데이터 (Medium Priority)
- [ ] **AC22.1**: `format_comparison_data(keywords_data)` 함수 구현
- [ ] **AC22.2**: 다중 시계열 데이터 포맷:
  ```json
  {
    "dates": ["2024-12-01", "2024-12-02"],
    "series": [
      {"name": "AI", "data": [100, 120], "color": "#5470c6"},
      {"name": "반도체", "data": [80, 95], "color": "#91cc75"}
    ]
  }
  ```
- [ ] **AC22.3**: 자동 색상 팔레트 할당 (최대 10개)
- [ ] **AC22.4**: 상대값(%) 모드: 최대값 대비 비율 계산

### AC23: 히트맵 데이터 (Low Priority)
- [ ] **AC23.1**: `format_heatmap_data(data, x_axis, y_axis)` 함수 구현
- [ ] **AC23.2**: 2D 매트릭스 형식:
  ```json
  {
    "xAxis": ["월", "화", "수", "목", "금"],
    "yAxis": ["정치", "경제", "사회"],
    "data": [[100, 120, 90, 110, 80], [80, 90, 100, 95, 70], ...]
  }
  ```
- [ ] **AC23.3**: 정규화 옵션: `none`, `row`, `column`, `global`
- [ ] **AC23.4**: 색상 스케일 범위 자동 계산

---

## 5. 기술 요구사항 (v2.0 추가)

### 5.1 새로운 의존성
```toml
# pyproject.toml 추가
circuitbreaker = "^2.0.0"  # Circuit Breaker 패턴
pytest-playwright = "^0.5.0"  # Playwright 테스트
pydantic = {version = "^2.5.0", extras = ["strict"]}  # Strict 모드
```

### 5.2 새로운 모듈 구조
```
src/bigkinds_mcp/
├── core/
│   ├── async_client.py (기존)
│   ├── cache.py (기존)
│   ├── circuit_breaker.py (v2.0)  # Circuit Breaker 로직
│   ├── rate_limiter.py (v2.0)     # Rate limiting
│   └── progress.py (v2.0)         # 진행률 추적
├── models/
│   ├── schemas.py (기존)
│   └── errors_kr.py (v2.0)        # 한글 에러 메시지
├── validation/
│   └── date_validator.py (v2.0)   # 날짜 검증 로직
├── visualization/                  # v3.0 신규
│   ├── __init__.py
│   ├── chart_formatter.py         # 차트 데이터 포맷팅
│   ├── wordcloud_formatter.py     # 워드클라우드 데이터
│   ├── timeline_formatter.py      # 타임라인 데이터
│   ├── comparison_formatter.py    # 비교 차트 데이터
│   ├── heatmap_formatter.py       # 히트맵 데이터
│   └── colors.py                  # 색상 팔레트
└── tests/
    ├── e2e_playwright/ (v2.0)     # Playwright 테스트
    └── test_visualization.py      # v3.0 시각화 테스트
```

### 5.3 새로운 환경변수
```env
# Circuit Breaker 설정
BIGKINDS_CIRCUIT_FAILURE_THRESHOLD=3    # 연속 실패 임계값
BIGKINDS_CIRCUIT_RECOVERY_TIMEOUT=30    # 복구 대기 시간(초)

# Rate Limiting 설정
BIGKINDS_RATE_LIMIT_REQUESTS=3          # 시간당 최대 요청 수
BIGKINDS_RATE_LIMIT_PERIOD=1            # 제한 기간(초)

# 진행률 설정
BIGKINDS_PROGRESS_THRESHOLD=5000        # 진행률 표시 최소 건수
BIGKINDS_PROGRESS_INTERVAL=10           # 진행률 업데이트 주기(%)
```

---

## 6. 성공 지표 (v2.0)

### 6.1 품질 지표
| 지표 | v1.5.2 | 목표 | 현재 (v1.7.2) | 상태 |
|------|--------|------|--------------|------|
| 테스트 커버리지 | 99% | 100% | 99% (239 passed) | ✅ |
| 엣지 케이스 커버리지 | ~60% | 90%+ | ~85% | ✅ |
| 에러 메시지 한글화율 | ~30% | 100% | 100% (15 ErrorCode) | ✅ |
| API 장애 복구 시간 | N/A | < 30초 | 30초 | ✅ |

### 6.2 성능 지표
| 지표 | v1.5.2 | 목표 | 현재 (v1.7.2) | 상태 |
|------|--------|------|--------------|------|
| 단일 검색 응답 시간 | < 3초 | < 2초 | < 2초 | ✅ |
| 병렬 3개 검색 총 시간 | ~9초 | < 4초 | ~4초 (55%↓) | ✅ |
| 대용량 export (10K건) | ~60초 | ~50초 | ~50초 | ✅ |
| 캐시 hit 응답 시간 | < 100ms | < 50ms | < 50ms | ✅ |
| 진행률 로깅 오버헤드 | N/A | < 5% | < 3% | ✅ |

### 6.3 사용성 지표
| 지표 | v1.5.2 | 목표 | 현재 (v1.7.2) | 상태 |
|------|--------|------|--------------|------|
| 에러 해결 문서 도달률 | ~0% | 80%+ | 80%+ (docs 필드) | ✅ |
| 진행률 피드백 제공률 | 0% | 100% | 100% (5K+ 작업) | ✅ |
| 사용자 에러 이해도 | N/A | "매우 명확" | 한글 메시지 | ✅ |

---

## 7. 비기능 요구사항 (v2.0)

### 7.1 신뢰성 (Reliability)
- **R1**: Circuit Breaker로 cascade failure 방지
- **R2**: 재시도 전략으로 일시적 장애 극복
- **R3**: Rate limiting으로 API 제한 준수

### 7.2 보안 (Security)
- **S1**: 스키마 검증으로 injection 공격 방지
- **S2**: 날짜 검증으로 API 남용 방지
- **S3**: 에러 메시지에 민감 정보 미포함

### 7.3 성능 (Performance)
- **P1**: 병렬 실행으로 복합 쿼리 2배 이상 가속
- **P2**: 진행률 로깅 오버헤드 < 5%
- **P3**: Circuit Breaker 상태 확인 오버헤드 < 1ms

### 7.4 유지보수성 (Maintainability)
- **M1**: 모든 에러 메시지 중앙 관리 (errors_kr.py)
- **M2**: Circuit Breaker 로직 독립 모듈화
- **M3**: Playwright 테스트로 회귀 방지

---

## 8. 위험 및 완화 전략

| 위험 | 영향 | 확률 | 완화 전략 |
|-----|------|------|---------|
| Circuit Breaker 오작동으로 정상 요청 차단 | High | Medium | 철저한 단위 테스트, fallback 로직 |
| 병렬 실행 시 rate limiting 위반 | Medium | High | Rate limiter 구현, 요청 간 간격 조정 |
| Pydantic strict 모드로 기존 동작 변경 | High | Medium | 점진적 마이그레이션, fallback 모드 |
| 진행률 로깅 성능 저하 | Low | Low | 조건부 활성화 (5K+ 건만) |
| 한글 메시지 번역 품질 | Medium | Low | 네이티브 리뷰, A/B 테스트 |

---

## 9. 마일스톤 및 일정

### Phase 1: High Priority ✅ (v1.6.0, 2025-12-16)
- [x] AC11: 병렬 API 호출 지원
- [x] AC12: 날짜 검증 강화
- [x] AC13: API 스키마 검증
- [x] AC14: 진행률 피드백

### Phase 2: Medium Priority ✅ (v1.7.0, 2025-12-17)
- [x] AC15: 에러 메시지 한글화
- [x] AC16: Circuit Breaker 패턴
- [x] AC17: 재시도 전략 고도화 (jitter 제외)

### Phase 3: Integration ✅ (v1.7.2, 2025-12-20)
- [ ] AC18: Playwright 통합 테스트 - *Low Priority로 이동*
- [x] 전체 테스트 통과 (239 passed)
- [x] 성능 벤치마크 달성 (55% 향상)
- [x] 문서 업데이트

### Phase 4: Release ✅
- [x] v1.7.2 배포 (PyPI + Remote Server)
- [x] CLAUDE.md 업데이트
- [ ] GitHub Release Notes 작성

**실제 소요 시간**: 4일

### Phase 5: Visualization (v3.0) ⏳
- [ ] AC19: 차트 데이터 포맷팅 (High Priority)
- [ ] AC20: 워드클라우드 데이터 (Medium Priority)
- [ ] AC21: 타임라인 데이터 (Medium Priority)
- [ ] AC22: 비교 차트 데이터 (Medium Priority)
- [ ] AC23: 히트맵 데이터 (Low Priority)

**예상 소요 시간**: 1-2일

---

## 10. 부록

### 10.1 참조 문서
- [PRD v1.0](./PRD.md) - 기존 요구사항 문서
- [IMPLEMENTATION_WORKFLOW_V2.md](./IMPLEMENTATION_WORKFLOW_V2.md) - 구현 워크플로우
- [SPEC_PANEL_REVIEW.md](./SPEC_PANEL_REVIEW.md) - 전문가 패널 리뷰 결과 (2025-12-20)
- [Circuit Breaker 패턴](https://martinfowler.com/bliki/CircuitBreaker.html)

### 10.2 용어 정의
- **Circuit Breaker**: 연속 실패 시 요청을 차단하여 시스템 보호
- **Rate Limiting**: 시간당 요청 수 제한으로 API 과부하 방지
- **Strict Mode**: Pydantic의 엄격한 타입 검증 모드
- **Exponential Backoff**: 재시도 간격을 지수적으로 증가 (1s, 2s, 4s, ...)

### 10.3 변경 로그
- **2025-12-21**: v3.0 시각화 유틸리티 추가
  - US20-US24: 시각화 관련 User Stories 5개 추가
  - AC19-AC23: 시각화 Acceptance Criteria 5개 추가
  - Phase 5: Visualization 마일스톤 추가
  - 모듈 구조에 `visualization/` 디렉토리 추가
  - 연구 기반: CHI 2024 디자인 패턴, 한국 데이터 저널리즘 사례 참고
- **2025-12-20**: v2.1 전문가 패널 리뷰 반영
  - AC11.5 추가: 5개 초과 요청 시 Semaphore 대기열 처리
  - AC12.5 추가: 날짜 경계값 테스트 케이스 명세
  - AC16.5-6 추가: half-open 복구 시나리오, API별 독립 Circuit
  - AC15.5 추가: 에러 메시지 대상 범위 명확화 (15개 ErrorCode)
  - AC18 우선순위 하향 (Medium → Low), 네트워크 분석 관련 항목 제거
  - 성능 지표에 측정 방법 상세화
  - 모든 AC 구현 완료 표시 (체크박스 업데이트)
- **2025-12-16**: v2.0 초안 작성 (품질/성능/보안 개선)
