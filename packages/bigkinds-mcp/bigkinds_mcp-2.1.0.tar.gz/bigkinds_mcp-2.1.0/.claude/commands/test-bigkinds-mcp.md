# BigKinds MCP 종합 테스트 프롬프트

BigKinds MCP 서버의 모든 기능을 순차적으로 테스트하고 종합 리포트를 생성합니다.

---

## 테스트 시나리오

### Phase 1: 기본 설정 및 유틸리티 테스트

**1.1 현재 시간 확인**
- `get_current_korean_time` 호출하여 오늘 날짜 확인
- 이 날짜를 기준으로 이후 모든 검색에서 end_date로 사용

**1.2 메타데이터 조회**
- `list_providers`: 전체 언론사 목록 조회 (총 몇 개인지 확인)
- `list_categories`: 전체 카테고리 목록 조회
- `find_category("경향")`: 특정 언론사 검색
- `find_category("경제")`: 특정 카테고리 검색

---

### Phase 2: 기본 검색 테스트

**2.1 단순 검색**
```
search_news(
  keyword="인공지능",
  start_date="2025-12-01",
  end_date=오늘날짜,
  page=1,
  page_size=10,
  sort_by="date"
)
```
- 총 검색 결과 수 확인
- 첫 페이지 기사 제목들 확인

**2.2 필터링 검색**
```
search_news(
  keyword="AI",
  start_date="2025-12-01",
  end_date=오늘날짜,
  providers=["경향신문", "한겨레"],
  categories=["경제", "IT_과학"],
  sort_by="relevance"
)
```
- 특정 언론사와 카테고리로 필터링된 결과 확인

**2.3 정렬 방식 비교**
- `sort_by="date"`: 최신순 검색
- `sort_by="relevance"`: 관련도순 검색
- `sort_by="both"`: 병합 검색 (기본값)
- 세 가지 결과의 첫 번째 기사 비교

---

### Phase 3: 기사 상세 조회 테스트

**3.1 news_id로 기사 상세 조회**
- Phase 2에서 얻은 news_id 중 하나로 `get_article` 호출
- BigKinds API 전문 조회 확인 (source: "bigkinds_api")

**3.2 URL로 기사 스크래핑**
- Phase 2에서 얻은 URL로 `scrape_article_url` 호출
- 스크래핑 결과와 BigKinds API 결과 비교

---

### Phase 4: 집계 및 시계열 분석

**4.1 기사 수 집계**
```
get_article_count(
  keyword="인공지능",
  start_date="2025-11-01",
  end_date=오늘날짜,
  group_by="total"
)
```
- 전체 기사 수 확인

**4.2 일별 집계**
```
get_article_count(
  keyword="인공지능",
  start_date="2025-12-01",
  end_date=오늘날짜,
  group_by="day"
)
```
- 일별 기사 수 변화 패턴 분석

**4.3 월별 집계**
```
get_article_count(
  keyword="인공지능",
  start_date="2025-01-01",
  end_date=오늘날짜,
  group_by="month"
)
```
- 월별 트렌드 분석

---

### Phase 5: 키워드 비교 분석

**5.1 다중 키워드 비교**
```
compare_keywords(
  keywords=["AI", "반도체", "전기차", "배터리", "로봇"],
  start_date="2025-12-01",
  end_date=오늘날짜,
  group_by="day"
)
```
- 5개 키워드 간 기사량 순위 비교
- 가장 많이 보도된 키워드 확인
- 일별 트렌드 비교

---

### Phase 6: 오늘의 이슈 조회

> **참고**: API는 "전체"와 "AI" 카테고리만 지원합니다 (v1.7.2)

**6.1 카테고리 테스트**
```
# 1. 전체 (기본값)
get_today_issues(category="전체")

# 2. AI 선정 이슈
get_today_issues(category="AI")
```
- 각 카테고리별 성공/실패 기록

**6.2 과거 날짜 테스트**
```
# 최근 날짜들로 테스트 (API 데이터 가용성 확인)
get_today_issues(date="어제날짜", category="전체")
get_today_issues(date="3일전날짜", category="전체")
get_today_issues(date="7일전날짜", category="전체")
```
- 과거 날짜 데이터 가용성 확인

**6.3 결과 분석**
- `results` 배열이 비어있는 경우 vs 에러인 경우 구분

---

### Phase 7: 대용량 데이터 처리 테스트 (다각도 검증)

> **이슈 발견**: export_all_articles에서 safe_keyword 변수 스코프 버그
> 다양한 시나리오로 테스트하여 버그 수정 여부 확인

**7.1 샘플링 테스트 (3가지 전략)**
```
# 1. Stratified (계층화) - 기본 전략
smart_sample(
  keyword="정치",
  start_date="2025-01-01",
  end_date=오늘날짜,
  sample_size=50,
  strategy="stratified"
)

# 2. Latest (최신순)
smart_sample(
  keyword="정치",
  start_date="2025-01-01",
  end_date=오늘날짜,
  sample_size=50,
  strategy="latest"
)

# 3. Random (무작위)
smart_sample(
  keyword="정치",
  start_date="2025-01-01",
  end_date=오늘날짜,
  sample_size=50,
  strategy="random"
)
```
- 각 전략별 샘플링 결과 비교
- coverage 비율 확인

**7.2 전체 내보내기 테스트 (다양한 시나리오)**
```
# 시나리오 1: output_path 지정 (이전에 실패한 케이스)
export_all_articles(
  keyword="AI 스타트업",
  start_date="2025-12-01",
  end_date=오늘날짜,
  output_format="json",
  output_path="data/ai_startup_test.json",
  max_articles=100
)

# 시나리오 2: output_path 미지정 (자동 생성)
export_all_articles(
  keyword="양자컴퓨터",
  start_date="2025-12-01",
  end_date=오늘날짜,
  output_format="json",
  max_articles=50
)

# 시나리오 3: CSV 형식
export_all_articles(
  keyword="반도체",
  start_date="2025-12-01",
  end_date=오늘날짜,
  output_format="csv",
  output_path="data/semiconductor_test.csv",
  max_articles=50
)

# 시나리오 4: JSONL 형식
export_all_articles(
  keyword="전기차",
  start_date="2025-12-01",
  end_date=오늘날짜,
  output_format="jsonl",
  output_path="data/ev_test.jsonl",
  max_articles=50
)
```
- 각 시나리오별 성공/실패 기록
- 파일 저장 확인 (절대 경로)
- analysis_code 템플릿 반환 확인
- next_steps 안내 확인

**7.3 에러 케이스 테스트**
```
# 잘못된 형식
export_all_articles(
  keyword="테스트",
  start_date="2025-12-01",
  end_date=오늘날짜,
  output_format="xml",  # 지원하지 않는 형식
  max_articles=10
)

# 과도한 max_articles
export_all_articles(
  keyword="테스트",
  start_date="2025-12-01",
  end_date=오늘날짜,
  max_articles=100000  # 50000 초과
)
```
- 에러 핸들링 확인

---

### Phase 8: 로그인 필요 기능 테스트 (다각도 검증)

> **이슈 발견**: get_keyword_trends에서 interval=1(일간)로 호출했으나 연도별 데이터만 반환
> 다양한 interval 값으로 테스트하여 정확한 동작 확인

> 환경변수 `BIGKINDS_USER_ID`, `BIGKINDS_USER_PASSWORD` 설정 필요

**8.1 키워드 트렌드 - Interval 테스트**
```
# 1. 일간 (interval=1) - 짧은 기간
get_keyword_trends(
  keyword="AI",
  start_date="2025-12-08",
  end_date=오늘날짜,
  interval=1
)

# 2. 일간 (interval=1) - 긴 기간
get_keyword_trends(
  keyword="AI",
  start_date="2025-12-01",
  end_date=오늘날짜,
  interval=1
)

# 3. 주간 (interval=2)
get_keyword_trends(
  keyword="AI",
  start_date="2025-11-01",
  end_date=오늘날짜,
  interval=2
)

# 4. 월간 (interval=3)
get_keyword_trends(
  keyword="AI",
  start_date="2025-01-01",
  end_date=오늘날짜,
  interval=3
)

# 5. 연간 (interval=4)
get_keyword_trends(
  keyword="AI",
  start_date="2024-01-01",
  end_date=오늘날짜,
  interval=4
)
```
- 각 interval별 `data` 배열의 `date` 형식 확인
  - 일간: "2025-12-01" 형식이어야 함
  - 주간: "2025-W49" 또는 날짜 형식
  - 월간: "2025-12" 형식
  - 연간: "2025" 형식
- `total_data_points`가 기간에 맞게 증가하는지 확인

**8.2 키워드 트렌드 - 다중 키워드**
```
get_keyword_trends(
  keyword="AI,인공지능,ChatGPT",
  start_date="2025-12-01",
  end_date=오늘날짜,
  interval=1
)
```
- 여러 키워드가 각각 분리되어 반환되는지 확인
- `trends` 배열에 3개 항목이 있는지 확인

**8.3 연관어 분석 - 다양한 파라미터**
```
# 1. 기본
get_related_keywords(
  keyword="AI",
  start_date="2025-12-01",
  end_date=오늘날짜,
  max_news_count=100,
  result_number=30
)

# 2. 더 많은 뉴스 분석
get_related_keywords(
  keyword="AI",
  start_date="2025-12-01",
  end_date=오늘날짜,
  max_news_count=500,
  result_number=50
)

# 3. 필터링 적용
get_related_keywords(
  keyword="AI",
  start_date="2025-12-01",
  end_date=오늘날짜,
  max_news_count=100,
  result_number=30,
  categories=["경제", "IT_과학"]
)
```
- max_news_count 증가에 따른 연관어 변화 확인
- 필터링 적용 시 결과 차이 확인

---

### Phase 9: 캐시 상태 확인

```
cache_stats()
```
- 각 캐시(search, article, count, generic)의 사용률 확인
- 이전 테스트들로 인한 캐시 적중률 예상

---

### Phase 10: 엣지 케이스 및 에러 핸들링 테스트

**10.1 빈 결과 테스트**
```
# 존재하지 않을 가능성이 높은 키워드
search_news(
  keyword="가나다라마바사아자차카타파하1234567890",
  start_date="2025-12-01",
  end_date=오늘날짜
)
```
- 빈 결과 처리 확인

**10.2 날짜 범위 테스트**
```
# 미래 날짜
search_news(
  keyword="AI",
  start_date="2025-12-20",
  end_date="2025-12-31"
)

# 과거 날짜 (먼 과거)
search_news(
  keyword="AI",
  start_date="2020-01-01",
  end_date="2020-01-31"
)
```
- 날짜 범위별 데이터 가용성 확인

**10.3 특수문자 키워드**
```
search_news(
  keyword="AI & 인공지능",
  start_date="2025-12-01",
  end_date=오늘날짜
)

search_news(
  keyword="\"인공지능\"",
  start_date="2025-12-01",
  end_date=오늘날짜
)
```
- 특수문자 포함 키워드 처리 확인

---

## 종합 리포트 생성

위 테스트 결과를 바탕으로 다음 형식의 리포트를 마크다운으로 생성해주세요:

```markdown
# BigKinds MCP 테스트 리포트

## 테스트 일시
- 날짜: YYYY-MM-DD
- 시간: HH:MM:SS KST

## 1. 유틸리티 기능 (Phase 1)
- [ ] get_current_korean_time: OK/FAIL
- [ ] list_providers: OK/FAIL (총 N개)
- [ ] list_categories: OK/FAIL (총 N개)
- [ ] find_category: OK/FAIL

## 2. 검색 기능 (Phase 2-3)
- [ ] search_news (기본): OK/FAIL
- [ ] search_news (필터링): OK/FAIL
- [ ] search_news (정렬비교): OK/FAIL
- [ ] get_article: OK/FAIL
- [ ] scrape_article_url: OK/FAIL

## 3. 집계 기능 (Phase 4)
- [ ] get_article_count (total): OK/FAIL
- [ ] get_article_count (day): OK/FAIL
- [ ] get_article_count (month): OK/FAIL

## 4. 분석 기능 (Phase 5)
- [ ] compare_keywords: OK/FAIL

## 5. 오늘의 이슈 (Phase 6) - 상세
| 카테고리 | 결과 | 비고 |
|---------|------|------|
| 전체 | OK/FAIL | |
| AI | OK/FAIL | |

## 6. 대용량 처리 (Phase 7) - 상세
### smart_sample
| 전략 | 결과 | 샘플 수 | 커버리지 |
|------|------|--------|---------|
| stratified | OK/FAIL | N건 | N% |
| latest | OK/FAIL | N건 | N% |
| random | OK/FAIL | N건 | N% |

### export_all_articles
| 시나리오 | 결과 | 파일명 | 크기 |
|---------|------|--------|-----|
| JSON (path 지정) | OK/FAIL | | |
| JSON (자동) | OK/FAIL | | |
| CSV | OK/FAIL | | |
| JSONL | OK/FAIL | | |

## 7. 로그인 필요 기능 (Phase 8) - 상세
### get_keyword_trends - Interval 테스트
| Interval | 기간 | 결과 | data_points | date 형식 |
|----------|------|------|-------------|----------|
| 1 (일간) | 7일 | OK/FAIL | N | |
| 1 (일간) | 15일 | OK/FAIL | N | |
| 2 (주간) | 6주 | OK/FAIL | N | |
| 3 (월간) | 12개월 | OK/FAIL | N | |
| 4 (연간) | 2년 | OK/FAIL | N | |

### get_related_keywords
| max_news_count | 결과 | 연관어 수 |
|----------------|------|----------|
| 100 | OK/FAIL | N개 |
| 500 | OK/FAIL | N개 |

## 8. 캐시 상태 (Phase 9)
- [ ] cache_stats: OK/FAIL
- search: N/1000 (N%)
- article: N/1000 (N%)
- count: N/1000 (N%)
- generic: N/1000 (N%)

## 9. 엣지 케이스 (Phase 10)
- [ ] 빈 결과 처리: OK/FAIL
- [ ] 미래 날짜 처리: OK/FAIL
- [ ] 과거 날짜 처리: OK/FAIL
- [ ] 특수문자 키워드: OK/FAIL

---

## 이슈 분석

### Issue #1: get_today_issues 카테고리 (해결됨 v1.7.2)
- **현상**: 지역 카테고리(서울, 경인강원 등)에서 빈 결과 반환
- **원인**: API가 "전체"와 "AI" 카테고리만 지원
- **해결**: v1.7.2에서 지원 카테고리를 "전체", "AI"로 제한하고 유효성 검증 추가

### Issue #2: get_keyword_trends Interval
- **현상**: interval=1(일간)에서 연도별 데이터만 반환
- **원인 분석**: (테스트 결과 기반 분석)
- **해결 방안**: (필요시 제안)

### Issue #3: export_all_articles safe_keyword
- **현상**: output_path 지정 시 에러
- **수정 여부**: 확인됨/미확인
- **재테스트 결과**: OK/FAIL

---

## 주요 발견 사항

### 성공한 테스트
- ...

### 실패한 테스트
- ...

### 개선 필요 사항
- ...

## 성능 메트릭
- 총 API 호출 수: N회
- 평균 응답 시간: N초
- 캐시 적중률: N%

## 결론
테스트 통과율: N/M (N%)

### 권장 후속 조치
1. ...
2. ...
```

---

## 추가 지시사항

1. **순차 실행**: 각 Phase를 순서대로 실행하고, 이전 결과를 다음 테스트에 활용
2. **에러 상세 기록**: 실패 시 정확한 에러 메시지, 응답 구조, 상황을 상세히 기록
3. **데이터 저장**: export_all_articles 결과물은 `data/` 디렉토리에 저장
4. **리포트 저장**: 최종 리포트를 `data/bigkinds_test_report_YYYYMMDD.md`로 저장
5. **환경 확인**: 로그인 필요 기능은 환경변수 설정 여부 먼저 확인 후 진행
6. **API 응답 분석**: 이슈 발생 시 raw 응답 데이터 구조를 분석하여 원인 파악
7. **비교 분석**: 성공 케이스와 실패 케이스의 차이점 분석

---

## 테스트 키워드 제안

실제 테스트 시 아래 키워드들을 활용하면 다양한 시나리오 검증 가능:

- **대용량**: "정치", "경제", "대통령" (수만~수십만 건)
- **중간 규모**: "AI", "인공지능", "반도체" (수천~수만 건)
- **소규모**: "AI 스타트업", "양자컴퓨터" (수백~수천 건)
- **시의성**: "비상계엄", "탄핵" (최근 이슈)

---

## 버전 히스토리

- **v1.0** (2025-12-15): 초기 버전
- **v1.1** (2025-12-15): 이슈 심층 분석 추가
  - Phase 6: get_today_issues 모든 카테고리 순차 테스트
  - Phase 7: export_all_articles 다양한 시나리오 (4종)
  - Phase 8: get_keyword_trends 모든 interval 테스트 (5종)
  - Phase 10: 엣지 케이스 및 에러 핸들링 추가
  - 리포트 템플릿 상세화 (표 형식 추가)
