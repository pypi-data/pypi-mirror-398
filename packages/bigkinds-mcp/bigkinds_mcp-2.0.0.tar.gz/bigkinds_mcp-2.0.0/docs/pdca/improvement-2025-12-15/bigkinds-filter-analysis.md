# BigKinds 필터 역공학 분석

## 분석 일시
2025-12-15

## 문제 발견
현재 구현에서 카테고리 필터가 작동하지 않음. 실제 API 호출 시 category_codes에 텍스트 이름("경제", "IT/과학" 등)을 전송하면 0건의 결과가 반환됨.

## 조사 방법
1. BigKinds 실제 API 응답 구조 분석
2. 반환되는 카테고리 코드 형식 확인
3. 숫자 코드 vs 텍스트 이름 비교 테스트

## 발견 사항

### 카테고리 파라미터 형식

#### 현재 구현 (잘못됨)
```python
CATEGORY_CODES = {
    "정치": "정치",
    "경제": "경제",
    "사회": "사회",
    "문화": "문화",
    "국제": "국제",
    "지역": "지역",
    "스포츠": "스포츠",
    "IT_과학": "IT/과학",
}
```

API 호출 시 전송되는 payload:
```json
{
  "categoryCodes": ["경제", "IT/과학"]
}
```

**결과**: 0건 (필터가 작동하지 않음)

#### 올바른 형식 (9자리 숫자 코드)

API가 실제로 반환하는 카테고리 코드:
```
CATEGORY: 008000000 008001000
008000000 008003000
002000000 002009000

CATEGORY_NAMES: IT_과학>과학<font color=Gray> | </font>IT_과학>모바일<font color=Gray> | </font>경제>반도체
```

올바른 매핑:
```python
CATEGORY_CODES = {
    "정치": "001000000",
    "경제": "002000000",
    "사회": "003000000",
    "문화": "004000000",
    "국제": "005000000",
    "지역": "006000000",
    "스포츠": "007000000",
    "IT_과학": "008000000",
}
```

API 호출 시 전송해야 하는 payload:
```json
{
  "categoryCodes": ["002000000", "008000000"]
}
```

**결과**: 정상적으로 필터링됨 (테스트 확인 완료)

### 언론사 파라미터 형식

#### 현재 구현 (정상)
```python
PROVIDER_CODES = {
    "01100001": "경향신문",
    "01100101": "국민일보",
    "01100201": "내일신문",
    ...
}

PROVIDER_NAME_TO_CODE = {v: k for k, v in PROVIDER_CODES.items()}
```

언론사 필터는 이미 올바르게 구현되어 있음:
- 사용자가 "경향신문" 입력 → "01100001"로 변환
- 사용자가 "01100001" 직접 입력 → 그대로 사용

API payload:
```json
{
  "providerCodes": ["01100001", "01100901"]
}
```

### 테스트 결과

| 필터 유형 | 입력 값 | 결과 건수 | 상태 |
|---------|--------|----------|------|
| 카테고리 (텍스트) | "경제" | 0 | ❌ 실패 |
| 카테고리 (숫자) | "002000000" | 852 | ✅ 성공 |
| 카테고리 (숫자) | "008000000" | 752 | ✅ 성공 |
| 카테고리 (다중) | ["002000000", "008000000"] | 1,277 | ✅ 성공 |
| 언론사 (이름) | "경향신문" → "01100001" | (기존 구현 정상) | ✅ 성공 |

## 현재 구현과의 차이점

### 1. 카테고리 코드 매핑 오류
- **문제**: `CATEGORY_CODES`가 텍스트 → 텍스트 매핑 (예: "경제" → "경제")
- **원인**: BigKinds API는 텍스트 이름을 받지 않고 9자리 숫자 코드만 받음
- **영향**: 모든 카테고리 필터가 작동하지 않음 (0건 반환)

### 2. 사용자 경험 불일치
- **현재**: 사용자는 "경제", "IT_과학" 같은 읽기 쉬운 이름 사용
- **API**: "002000000", "008000000" 같은 숫자 코드 필요
- **해결 필요**: 이름 → 코드 변환 로직 (언론사처럼)

## 권장 수정 사항

### 1. CATEGORY_CODES 수정 (`src/bigkinds_mcp/tools/utils.py`)

**변경 전:**
```python
CATEGORY_CODES = {
    "정치": "정치",
    "경제": "경제",
    "사회": "사회",
    "문화": "문화",
    "국제": "국제",
    "지역": "지역",
    "스포츠": "스포츠",
    "IT_과학": "IT/과학",
}
```

**변경 후:**
```python
CATEGORY_CODES = {
    "001000000": "정치",
    "002000000": "경제",
    "003000000": "사회",
    "004000000": "문화",
    "005000000": "국제",
    "006000000": "지역",
    "007000000": "스포츠",
    "008000000": "IT_과학",
}

# 이름 → 코드 역매핑 (언론사와 동일한 패턴)
CATEGORY_NAME_TO_CODE = {v: k for k, v in CATEGORY_CODES.items()}
```

### 2. 카테고리 변환 로직 수정 (`src/bigkinds_mcp/tools/search.py`)

**변경 전:**
```python
# 카테고리 이름 정규화 (CATEGORY_CODES 딕셔너리 사용)
categories = None
if params.categories:
    categories = []
    for c in params.categories:
        # CATEGORY_CODES 매핑 사용 (없으면 그대로)
        normalized = CATEGORY_CODES.get(c, c)
        categories.append(normalized)
```

**변경 후:**
```python
# 카테고리 이름 → 코드 변환 (언론사와 동일한 패턴)
from .utils import CATEGORY_NAME_TO_CODE

categories = None
if params.categories:
    categories = []
    for c in params.categories:
        if c in CATEGORY_NAME_TO_CODE:
            # 이름이면 코드로 변환 (예: "경제" → "002000000")
            categories.append(CATEGORY_NAME_TO_CODE[c])
        else:
            # 이미 코드이거나 알 수 없는 값은 그대로
            categories.append(c)
```

### 3. 하위 카테고리 지원 고려

현재는 대분류만 지원하지만, API 응답에는 하위 카테고리도 있음:
```
002000000 002009000  (경제 > 반도체)
008000000 008001000  (IT_과학 > 과학)
```

향후 확장 시 하위 카테고리 코드 추가 고려:
```python
CATEGORY_CODES = {
    # 대분류
    "001000000": "정치",
    "002000000": "경제",
    "008000000": "IT_과학",

    # 하위 카테고리 (예시)
    "002009000": "경제>반도체",
    "008001000": "IT_과학>과학",
    "008003000": "IT_과학>모바일",
    ...
}
```

## 검증 방법

수정 후 다음 테스트로 검증:
```bash
uv run python test_numeric_categories.py
```

예상 결과:
- "경제" 입력 → "002000000"로 변환 → 정상 검색
- "008000000" 직접 입력 → 그대로 사용 → 정상 검색
- 다중 카테고리 → 모두 정상 작동

## 참고 자료

- BigKinds 공식 사이트: https://www.bigkinds.or.kr
- API 엔드포인트: https://www.bigkinds.or.kr/api/news/search.do
- 테스트 스크립트:
  - `test_api_payload.py`: API payload 구조 확인
  - `test_live_filter.py`: 필터 작동 검증
  - `test_inspect_response.py`: API 응답 구조 분석
  - `test_numeric_categories.py`: 숫자 코드 테스트

## 결론

1. **즉시 수정 필요**: 카테고리 필터가 현재 전혀 작동하지 않음
2. **수정 범위**:
   - `utils.py`: CATEGORY_CODES 매핑 수정
   - `search.py`: 이름→코드 변환 로직 추가
3. **영향 범위**:
   - MCP Tools: `search_news`, `get_article_count`
   - 기존 테스트: 카테고리 필터 사용 시 모두 0건 반환됨
4. **하위 호환성**:
   - 사용자는 여전히 "경제", "IT_과학" 같은 이름 사용 가능
   - 내부적으로 숫자 코드로 자동 변환

## 추가 발견 사항

### 카테고리 응답 형식
BigKinds API가 반환하는 카테고리 정보는 두 가지 형식:
1. `CATEGORY`: 숫자 코드 (공백 구분, 여러 줄 가능)
   - 예: `"008000000 008001000\n008000000 008003000\n002000000 002009000"`
2. `CATEGORY_NAMES`: 사람이 읽을 수 있는 이름 (HTML 포함)
   - 예: `"IT_과학>과학<font color=Gray> | </font>IT_과학>모바일<font color=Gray> | </font>경제>반도체"`

현재 `models.py`의 `NewsArticle.from_api_response()`는 `CATEGORY` 필드를 그대로 저장하므로,
카테고리 표시 시 파싱이나 정리가 필요할 수 있음.
