# BigKinds MCP 명세서 전문가 패널 리뷰

> 생성일: 2025-12-20
> 검토 대상: PRD_V2.md, MCP_ARCHITECTURE_V2.md

---

## 전문가 패널 구성

| 전문가 | 전문 분야 | 역할 |
|--------|----------|------|
| **Karl Wiegers** | 요구사항 공학 | PRD 품질, User Story 분석 |
| **Gojko Adzic** | BDD/Specification by Example | Acceptance Criteria 검증 |
| **Martin Fowler** | 소프트웨어 아키텍처 | 시스템 설계 평가 |
| **Michael Nygard** | 시스템 복원력 | Circuit Breaker, 안정성 패턴 |
| **Sam Newman** | 마이크로서비스 | API 설계, 분리 원칙 |

---

## 1. 요구사항 품질 분석 (Karl Wiegers)

### 1.1 긍정적 평가

**User Stories 품질** ⭐⭐⭐⭐☆
- US13-US19가 "As a... I want to... So that..." 형식을 올바르게 따름
- 각 스토리에 명확한 Acceptance Criteria 첨부
- 비즈니스 가치와 사용자 관점 명확히 표현

**요구사항 추적성** ⭐⭐⭐⭐⭐
- AC11-AC18이 US와 명확히 연결됨
- 각 AC에 세부 항목(AC11.1~AC11.4) 포함
- 우선순위(High/Medium) 구분 명확

### 1.2 개선 필요 사항

**Issue #1: 비기능 요구사항 정량화 부족**
```
현재: "P2: 진행률 로깅 오버헤드 < 5%"
문제: 어떻게 측정할 것인지 불명확

권장 수정:
"P2: 진행률 로깅 오버헤드 < 5%
  - 측정 방법: export_all_articles 10,000건 기준
  - 로깅 비활성화 vs 활성화 실행 시간 비교
  - 벤치마크 스크립트: scripts/benchmark_progress.py"
```

**Issue #2: US17 에러 메시지 범위 모호**
```
현재: "모든 에러 메시지를 한국어로 받고"
문제: "모든"의 범위가 불명확

권장 수정:
"MCP Tool 반환 에러 메시지를 한국어로 받고"
또는 에러 목록 명시 (ErrorCode enum 참조)
```

**Issue #3: AC18 Playwright 테스트 ROI 불분명**
```
현재: 네트워크 분석 API 복원 목적
문제: 이미 제외된 기능에 대한 테스트 투자 정당성 불명확

권장:
- 네트워크 분석 복원 가능성 재평가 후 결정
- 또는 AC18 범위를 "E2E 회귀 테스트"로 축소
```

---

## 2. Acceptance Criteria 검증 (Gojko Adzic)

### 2.1 긍정적 평가

**Given-When-Then 변환 가능성** ⭐⭐⭐⭐☆
- 대부분의 AC가 테스트 가능한 형태
- 구체적인 값 포함 (예: "연속 실패 3회", "30초 대기")

**예시 기반 명세** ⭐⭐⭐⭐⭐
- AC14.2에 로그 형식 예시 포함: `[진행률] 1000/10000 (10%)`
- AC15.2에 에러 응답 JSON 예시 포함

### 2.2 개선 필요 사항

**Issue #4: AC11 병렬 실행 경계 조건 누락**
```
현재: "최대 5개 동시 요청 제한"
누락: 6개 이상 요청 시 동작 명세

권장 추가:
"AC11.5: 5개 초과 요청 시 대기열 처리 (FIFO)
        또는 RateLimitExceeded 에러 반환"
```

**Issue #5: AC12 날짜 경계값 테스트 케이스 필요**
```
권장 추가 시나리오:
- 1989-12-31 입력 시 → DATE_OUT_OF_RANGE
- 1990-01-01 입력 시 → 정상 처리 (경계값)
- 오늘 날짜 입력 시 → 정상 처리
- 내일 날짜 입력 시 → INVALID_DATE_RANGE
```

**Issue #6: AC16 Circuit Breaker 복구 시나리오 불완전**
```
현재: "half-open 상태에서 1회 성공 시 circuit close"
누락: half-open에서 실패 시 동작

권장 추가:
"AC16.5: half-open 상태에서 실패 시 즉시 OPEN으로 복귀
        (recovery_timeout 재시작)"
```

---

## 3. 아키텍처 설계 평가 (Martin Fowler)

### 3.1 긍정적 평가

**계층 분리** ⭐⭐⭐⭐⭐
```
Tools → Core → External APIs
     ↓
  Resources/Prompts
```
- 명확한 책임 분리
- 의존성 방향 일관성 유지

**캐싱 전략** ⭐⭐⭐⭐☆
- TTL 기반 캐싱으로 신선도 보장
- 데이터 유형별 차등 TTL 적용

### 3.2 개선 필요 사항

**Issue #7: 캐시 무효화 전략 부재**
```
현재: TTL 만료에만 의존
문제: 데이터 변경 시 오래된 캐시 반환 가능

권장 추가:
- cache.invalidate(pattern="search_*") 메서드
- 수동 캐시 클리어 API 제공
- export_all_articles 시 관련 캐시 갱신
```

**Issue #8: 모듈 구조와 실제 구현 불일치**
```
아키텍처 문서 (11개 Tools):
- search.py: search_news, get_article_count
- article.py: get_article, scrape_article_url
- analysis.py: get_keyword_trends, get_related_keywords
- utils.py: 유틸리티

실제 구현 (14개 Tools):
- compare_keywords, smart_sample, export_all_articles 누락
- visualization.py 모듈 미언급

권장: 문서 동기화 또는 모듈 재구성
```

**Issue #9: 에러 처리 계층 단순화 필요**
```
현재 예외 클래스:
- BigKindsError (base)
- AuthenticationError
- RateLimitError
- APIError
- ScrapingError

실제 사용:
- ValueError, ValidationError도 혼용

권장:
- errors.py에 모든 예외 통합
- MCP 반환 시 일관된 에러 응답 형식 보장
```

---

## 4. 시스템 복원력 평가 (Michael Nygard)

### 4.1 긍정적 평가

**Circuit Breaker 설계** ⭐⭐⭐⭐⭐
- 3-state machine (CLOSED, OPEN, HALF_OPEN) 올바른 구현
- 캐시 fallback 전략 포함
- 상태 전환 로깅

**재시도 전략** ⭐⭐⭐⭐☆
- Exponential backoff 적용
- Jitter 추가로 thundering herd 방지

### 4.2 개선 필요 사항

**Issue #10: Bulkhead 패턴 부재**
```
현재: 모든 요청이 동일한 httpx 클라이언트 공유
위험: 하나의 느린 요청이 전체 시스템 블로킹

권장:
- 검색 API용 클라이언트 풀
- 분석 API용 클라이언트 풀
- 각 풀별 독립적인 Circuit Breaker
```

**Issue #11: Timeout 계층화 필요**
```
현재: 단일 BIGKINDS_TIMEOUT=30초
문제: 모든 API에 동일 타임아웃 부적절

권장:
- 검색 API: 10초 (빠른 응답 기대)
- 분석 API: 30초 (복잡한 처리)
- 스크래핑: 15초 (외부 사이트 의존)
- 전체 요청: 60초 (최대 상한)
```

**Issue #12: 부분 실패 처리 미흡**
```
현재: export_all_articles에서 일부 페이지 실패 시?
누락: 부분 성공 시나리오 명세

권장:
- 실패한 페이지 재시도 로직
- 부분 결과 반환 옵션
- 실패 건수/성공 건수 리포트
```

---

## 5. API 설계 평가 (Sam Newman)

### 5.1 긍정적 평가

**RESTful 원칙** ⭐⭐⭐⭐☆
- 리소스 기반 URI 설계 (news://, article://)
- 일관된 응답 형식 (success, error 필드)

**버전 관리** ⭐⭐⭐⭐☆
- pyproject.toml 버전 관리
- CHANGELOG 유지

### 5.2 개선 필요 사항

**Issue #13: API 버전 전략 부재**
```
현재: 버전 정보가 health check에만 포함
문제: Breaking change 시 하위 호환성 문제

권장:
- MCP Tool 이름에 버전 접미사 고려 (search_news_v2)
- 또는 서버 레벨 버전 협상
```

**Issue #14: 페이지네이션 일관성**
```
현재:
- search_news: page, page_size
- export_all_articles: max_articles

권장:
- 통일된 페이지네이션 파라미터 명명
- cursor 기반 페이지네이션 고려 (대용량 처리 시)
```

**Issue #15: 응답 크기 제한 미명세**
```
문제: 대용량 응답 시 클라이언트 메모리 문제

권장:
- 최대 응답 크기 제한 (예: 10MB)
- 스트리밍 응답 지원 (export 시)
- 압축 옵션 (gzip)
```

---

## 6. 종합 평가 및 권고사항

### 6.1 우선순위별 개선 목록

#### 🔴 High Priority (구현 전 수정 필요)
| # | Issue | 담당 | 예상 공수 |
|---|-------|------|----------|
| 4 | AC11 병렬 실행 경계 조건 | PRD | 0.5h |
| 6 | AC16 Circuit Breaker 복구 시나리오 | PRD | 0.5h |
| 8 | 모듈 구조 문서 동기화 | Architecture | 1h |

#### 🟡 Medium Priority (Phase 완료 후 수정)
| # | Issue | 담당 | 예상 공수 |
|---|-------|------|----------|
| 1 | 비기능 요구사항 정량화 | PRD | 1h |
| 5 | 날짜 경계값 테스트 케이스 | PRD | 0.5h |
| 7 | 캐시 무효화 전략 | Architecture | 2h |
| 11 | Timeout 계층화 | Implementation | 1h |

#### 🟢 Low Priority (향후 개선)
| # | Issue | 담당 | 예상 공수 |
|---|-------|------|----------|
| 2 | US17 에러 범위 명확화 | PRD | 0.5h |
| 3 | AC18 Playwright ROI 재평가 | PRD | 1h |
| 9 | 에러 처리 계층 통합 | Implementation | 2h |
| 10 | Bulkhead 패턴 | Implementation | 3h |
| 12 | 부분 실패 처리 | Implementation | 2h |
| 13 | API 버전 전략 | Architecture | 1h |
| 14 | 페이지네이션 일관성 | Implementation | 1h |
| 15 | 응답 크기 제한 | Implementation | 1h |

### 6.2 전체 품질 점수

| 영역 | 점수 | 평가 |
|------|------|------|
| 요구사항 명확성 | 8.5/10 | 양호, 일부 모호성 존재 |
| AC 테스트 가능성 | 9.0/10 | 우수, 경계 조건 보강 필요 |
| 아키텍처 일관성 | 7.5/10 | 문서-구현 간 불일치 |
| 복원력 설계 | 8.0/10 | 양호, 부분 실패 처리 필요 |
| API 설계 | 8.0/10 | 양호, 버전 전략 부재 |
| **종합** | **8.2/10** | **프로덕션 준비 수준** |

### 6.3 결론

BigKinds MCP Server의 PRD_V2와 Architecture_V2 문서는 **프로덕션 품질 수준**에 근접합니다.

**강점:**
- User Story와 Acceptance Criteria 연결이 명확
- Circuit Breaker 등 복원력 패턴 적절히 설계
- 캐싱 전략과 우선순위 구분이 실용적

**개선 필요:**
- 문서와 실제 구현 간 동기화 필요 (14개 Tools vs 11개 문서화)
- 경계 조건 및 실패 시나리오 보강
- Bulkhead 패턴 등 추가 복원력 패턴 고려

**권장 다음 단계:**
1. High Priority 이슈 3건 즉시 수정
2. 문서-구현 동기화 스크립트 작성
3. AC18 (Playwright) ROI 재평가 회의

---

*본 리뷰는 소프트웨어 명세서 분야 전문가들의 관점을 종합하여 작성되었습니다.*
