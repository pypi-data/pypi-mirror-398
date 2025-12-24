# Do: BigKinds MCP 개선 실험 로그

> 작성일: 2025-12-15

## Phase 0: 근본 원인 조사 (10:00-11:30)

### 이슈 1: 필터 기능 미작동

#### 조사 과정

**10:00 - 사용자 힌트**
- 사용자 제보: "토픽은 IT_기술이 아니라 IT/기술 등으로 필터되는거 같았어"
- → 카테고리 명명 규칙 문제 가능성

**10:15 - 코드 리뷰**

파일 분석:
1. `src/bigkinds_mcp/tools/utils.py:40-49`
```python
CATEGORY_CODES = {
    "정치": "정치",
    "경제": "경제",
    "사회": "사회",
    "문화": "문화",
    "국제": "국제",
    "지역": "지역",
    "스포츠": "스포츠",
    "IT_과학": "IT/과학",  # ← 유일한 변환 케이스
}
```
- 매핑 정의는 있지만 **사용되지 않음**

2. `src/bigkinds_mcp/tools/search.py:105-112`
```python
# 카테고리 이름 정규화 (IT_과학 → IT/과학)
categories = None
if params.categories:
    categories = []
    for c in params.categories:
        # IT_과학 → IT/과학 변환
        normalized = c.replace("_", "/")  # ← 단순 replace만 사용
        categories.append(normalized)
```
- `CATEGORY_CODES` 딕셔너리 무시
- 모든 언더스코어를 슬래시로 치환

3. `bigkinds/models.py:113`
```python
"categoryCodes": self.category_codes,  # API로 그대로 전달
```

#### 근본 원인 (Root Cause)

**RC1: 카테고리 매핑 불일치**
- 정의된 `CATEGORY_CODES` 딕셔너리를 사용하지 않음
- 단순 `replace("_", "/")`는 모든 카테고리에 적용되지만, 대부분은 변환 불필요
- 예: "정치" 입력 → "정치" 그대로 (OK)
- 예: "IT_과학" 입력 → "IT/과학" 변환 (OK by accident)
- **문제**: 사용자가 "IT/과학"을 직접 입력하면? → "IT//과학" (이중 슬래시 버그 가능성)

**RC2: 언론사 필터 미검증**
- `search.py:94-103`에서 `PROVIDER_NAME_TO_CODE` 사용
- 하지만 실제 API가 이 코드를 인식하는지 미검증
- 테스트 리포트: 코드 직접 입력 시 일부 작동

### 이슈 2: total_pages 계산 오류

**조사 필요** (다음 단계)
- `search.py`에서 sort_by="both" 병합 후 total_pages 재계산 로직 확인

### 이슈 3: news_id 조회 제한

**조사 필요** (다음 단계)
- BigKinds API에 news_id 기반 조회 엔드포인트 존재 여부 확인

---

## Phase 1 수정 계획 (Draft)

### 1.1 카테고리 필터 수정

**Before (현재)**:
```python
for c in params.categories:
    normalized = c.replace("_", "/")
    categories.append(normalized)
```

**After (수정안)**:
```python
for c in params.categories:
    # CATEGORY_CODES 딕셔너리 사용
    normalized = CATEGORY_CODES.get(c, c)  # 매핑에 없으면 그대로
    categories.append(normalized)
```

**장점**:
- 명시적 매핑 사용 (의도 명확)
- 이중 슬래시 버그 방지
- 향후 카테고리 추가 시 유지보수 용이

### 1.2 언론사 필터 검증

**TODO**:
1. 실제 BigKinds API 요청/응답 로깅 추가
2. 언론사 코드가 API에서 인식되는지 확인
3. 필터 실패 시 fallback 로직:
   ```python
   if response.total_count == 0 and (providers or categories):
       # 경고 메시지 반환 + 필터 없이 재시도
       logger.warning("필터가 0건 반환, 전체 결과로 fallback")
   ```

### 1.3 통합 테스트 케이스 작성

**테스트 시나리오**:
- [ ] 카테고리: "정치" → API 인식 확인
- [ ] 카테고리: "IT_과학" → "IT/과학" 변환 확인
- [ ] 카테고리: "IT/과학" 직접 입력 → 이중 슬래시 방지 확인
- [ ] 언론사: "경향신문" → 코드 변환 → API 인식 확인
- [ ] 언론사: "01100001" 직접 입력 → API 인식 확인
- [ ] 복합 필터: providers + categories 동시 사용

---

## Learning (중간 학습)

### L1: 매핑 딕셔너리는 정의만으로는 부족
- 정의된 매핑을 실제 코드에서 사용해야 함
- `CATEGORY_CODES` 딕셔너리가 있었지만 무시됨
- **교훈**: 코드 리뷰 시 사용되지 않는 상수/매핑 확인 필요

### L2: 단순 replace의 위험성
- `replace("_", "/")`는 모든 언더스코어를 치환
- 엣지 케이스 (이중 슬래시, 예상치 못한 입력) 고려 안 됨
- **교훈**: 명시적 매핑이 단순 변환보다 안전

### L3: 사용자 피드백의 가치
- 테스트 리포트에는 "0건 반환"만 기록
- 사용자가 "IT/기술"이라는 힌트 제공
- **교훈**: 실제 사용 경험이 디버깅의 핵심 단서

---

**Next Step**: Phase 1 수정 착수 (카테고리 매핑 우선)
