# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.2] - 2025-12-15

### Fixed
- **`get_today_issues` 카테고리 버그 수정**:
  - API가 `category=전체`만 지원하는 제한 발견 및 해결
  - 클라이언트 측에서 `topic_category` 필드로 필터링하도록 변경
  - 실제 지원 카테고리 문서화: "전체", "서울", "경인강원", "충청", "경상", "전라제주", "AI"
- **`smart_sample` random 전략 버그 수정**:
  - `sample_size // page_size`가 0이 되어 빈 결과 반환하던 문제 해결
  - BigKinds API 페이지네이션 제한 (약 15-17페이지) 반영
  - 최소 1페이지 샘플링 보장 + API 페이지 제한 15로 설정

### Changed
- 테스트 통과율 88% → 99% 개선 (22/25 → 110/111)

---

## [1.5.1] - 2025-12-15

### Fixed
- **`export_all_articles` safe_keyword 변수 스코프 버그 수정**

### Changed
- **`get_keyword_trends` interval 동작 문서화**:
  - API가 날짜 범위에 따라 자동으로 granularity 조정하는 것은 API 자체 특성
  - interval 파라미터는 힌트로만 사용됨을 docstring에 명시

---

## [1.5.0] - 2025-12-15

### Added
- **대용량 분석 워크플로우 지원**:
  - `search_news` 결과에 `workflow_hint` 필드 추가 (100건 이상 시 로컬 내보내기 권장)
  - `export_all_articles` 결과에 `analysis_code` 필드 추가 (Python 분석 템플릿)
  - `large_scale_analysis` MCP Prompt 추가 (LLM 워크플로우 가이드)
- **`export_all_articles` 대용량 내보내기**: 최대 50,000건 일괄 내보내기 (JSON/CSV/JSONL)

---

## [1.4.0] - 2025-12-15

### Added
- **`get_article` BigKinds detailView API 지원**:
  - 기존: 검색 API의 200자 요약만 반환
  - 개선: `/news/detailView.do` API로 전체 본문(CONTENT) 획득
  - 실패 시 URL 스크래핑 폴백 유지
  - 응답에 `source: "bigkinds_api"` 또는 `source: "scraping"` 표시

### Changed
- `export_all_articles`의 `include_content=True` 옵션이 detailView API 활용

---

## [1.3.0] - 2025-12-15

### Added
- **로그인 필요 분석 도구 2개**:
  - `get_keyword_trends`: 키워드 트렌드 분석 (시간축 그래프)
  - `get_related_keywords`: 연관어 분석 (TF-IDF 기반)
- **유틸리티 도구**:
  - `get_current_korean_time`: 현재 한국 시간 조회 (KST)
  - `find_category`: 언론사/카테고리 코드 검색

### Changed
- 환경변수 지원: BIGKINDS_USER_ID, BIGKINDS_USER_PASSWORD

---

## [1.2.1] - 2025-12-15

### Fixed
- **기사 URL 반환 수정**: `PROVIDER_LINK_PAGE` 필드 매핑 추가로 실제 언론사 기사 URL 반환

---

## [1.2.0] - 2025-12-15

### Fixed
- **필터 기능 완전 수정** (86% → 100% 성공률)
  - 카테고리 필터: 9-digit 숫자 코드로 수정 (001000000~008000000)
  - 언론사 필터: 실제 API 응답 기준 72개 체계적 수집
  - 사용자는 여전히 친화적 이름 사용 가능 ("경향신문", "IT_과학" 등)
- **total_pages 정확도 수정**: 병합된 결과 수가 아닌 API 실제 총 개수 사용
- **ArticleSummary 스키마 보강**: provider_code, category_code 필드 추가

### Added
- **새 분석 도구 3개**:
  - `compare_keywords`: 여러 키워드 트렌드 비교 분석
  - `smart_sample`: 대용량 검색 결과에서 대표 샘플 추출 (3가지 전략)
  - `cache_stats`: 캐시 사용 현황 모니터링
- **GitHub Actions 워크플로**:
  - 자동 테스트 (test.yml)
  - PyPI 자동 배포 (publish.yml)
  - 월간 필터 검증 (filter-validation.yml)
- **PDCA 문서화**: 개선 프로세스 전체 문서화 (docs/pdca/improvement-2025-12-15/)

### Changed
- 언론사 코드 커버리지: 23개 → 72개 (종합일간지, 경제지, 지역일간지, 방송사 등)
- 테스트 커버리지 강화: 필터 관련 테스트 3개 추가

## [1.1.2] - 2025-12-10

### Fixed
- 기사 조회 시 news_id만으로 조회 가능하도록 URL 캐시 추가
- 언론사/카테고리 필터 이름→코드 자동 변환 기능 개선

## [1.1.0] - 2025-12-08

### Added
- PyPI 배포 설정 완료
- MCP 서버 전체 구현 완료

### Fixed
- 다양한 버그 수정 및 안정성 개선

## [1.0.0] - 2025-12-01

### Added
- 초기 릴리즈
- BigKinds MCP Server 기본 기능 구현
