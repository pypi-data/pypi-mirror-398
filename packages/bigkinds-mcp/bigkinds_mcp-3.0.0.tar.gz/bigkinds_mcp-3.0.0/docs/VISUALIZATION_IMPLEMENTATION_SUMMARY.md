# BigKinds 시각화 Tools 구현 요약

## 구현 개요

BigKinds MCP 서버에 3개의 시각화 분석 도구를 추가했습니다. 이 도구들은 BigKinds의 시각화 API를 활용하여 뉴스 데이터를 다양한 관점에서 분석할 수 있게 합니다.

**구현 날짜**: 2024-12-15
**상태**: ✅ 구현 완료, 1/3 정상 작동

## 구현된 Tools

### 1. get_keyword_trends - 키워드 트렌드 분석

키워드별 기사 수 추이를 시간축으로 분석하는 도구입니다.

**파일 위치:**
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/core/async_client.py` (Line 256-337)
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/tools/visualization.py` (Line 192-325)
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/server.py` (Line 340-388)

**주요 기능:**
- 여러 키워드 동시 분석 (콤마로 구분)
- 시간 단위 선택 (일간/주간/월간/연간)
- 언론사/카테고리 필터링 지원
- 자동 로그인 및 세션 관리

**API 엔드포인트:**
```
POST https://www.bigkinds.or.kr/api/analysis/keywordTrends.do
```

**상태:** ⚠️ 로그인 성공, 하지만 API가 빈 결과 반환

---

### 2. get_related_keywords - 연관어 분석 ✅

검색 키워드와 연관된 키워드를 TF-IDF 기반으로 추출하는 도구입니다.

**파일 위치:**
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/core/async_client.py` (Line 339-424)
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/tools/visualization.py` (Line 328-438)
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/server.py` (Line 391-435)

**주요 기능:**
- TF-IDF 가중치 기반 연관어 추출
- 분석 뉴스 수 조절 (50~1000건)
- 상위 N개 연관어 필터링
- 언론사/카테고리 필터링 지원

**API 엔드포인트:**
```
POST https://www.bigkinds.or.kr/api/analysis/relationalWords.do
```

**상태:** ✅ **정상 작동**

**테스트 결과:**
```python
# AI 키워드로 100건 분석
분석 뉴스 수: 50
발견 연관어: 32개

상위 10개:
1. 인공지능: 43.3200
2. 생성형 AI: 9.0000
3. SK텔레콤: 6.0000
4. AI 디지털교과서: 5.8600
5. 조직개편: 4.5000
6. AI 기본법: 4.2400
7. 챗GPT: 3.6800
8. B2B: 3.5300
9. AI 시대: 3.4700
10. 생성형 인공지능: 3.2700
```

---

### 3. get_network_analysis - 네트워크 분석

개체(인물, 기관, 장소, 키워드) 간의 관계를 네트워크 그래프로 분석하는 도구입니다.

**파일 위치:**
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/core/async_client.py` (Line 167-254)
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/tools/visualization.py` (Line 23-189)
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/server.py` (Line 438-485)

**주요 기능:**
- 인물, 기관, 장소, 키워드 추출
- 개체 간 관계 링크 생성
- 카테고리별 노드 분류
- 상위 개체 자동 추출

**API 엔드포인트:**
```
POST https://www.bigkinds.or.kr/news/getNetworkDataAnalysis.do
```

**상태:** ⚠️ 로그인 성공, 하지만 API가 빈 결과 반환

---

## 인증 시스템

### 구현 방식

**자동 로그인 메커니즘:**

1. 환경변수에서 계정 정보 로드
2. 첫 API 호출 시 자동 로그인 시도
3. 세션 쿠키를 httpx.AsyncClient에 저장
4. 후속 요청에 세션 재사용

**구현 위치:**
- `/Users/sdh/Dev/01_active_projects/bigkinds/src/bigkinds_mcp/core/async_client.py` (Line 93-165)

**로그인 프로세스:**

```python
1. 메인 페이지 접속 (세션 초기화)
   GET https://www.bigkinds.or.kr/

2. 로그인 API 호출
   POST /api/account/signin.do
   POST /api/account/signin2023.do (fallback)

3. 세션 쿠키 획득
   - Bigkinds: [세션 ID]
   - LAB_SSO_COOKIE: [SSO 토큰]

4. 후속 API 호출에 세션 사용
```

### 환경변수

`.env` 파일 설정:
```env
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password
```

---

## 파일 구조

### 신규 생성 파일

```
bigkinds/
├── src/bigkinds_mcp/
│   ├── core/
│   │   └── async_client.py          # 로그인 + 시각화 API 메서드 추가
│   └── tools/
│       └── visualization.py          # 시각화 MCP Tools (기존 파일 확장)
├── tests/
│   ├── test_auth_api.py              # 로그인 테스트
│   ├── test_keyword_trends.py        # 키워드 트렌드 파라미터 테스트
│   └── test_visualization_tools.py   # MCP Tools 통합 테스트
└── docs/
    ├── VISUALIZATION_API.md           # API 스펙 문서
    ├── VISUALIZATION_TOOLS.md         # Tools 사용 가이드
    └── VISUALIZATION_IMPLEMENTATION_SUMMARY.md  # 이 문서
```

### 수정된 파일

```
bigkinds/
├── src/bigkinds_mcp/
│   ├── server.py                     # 3개 Tool 등록
│   └── core/
│       └── async_client.py           # 로그인 + 3개 API 메서드 추가
├── CLAUDE.md                          # 프로젝트 문서 업데이트
└── .env                               # 계정 정보 (기존)
```

---

## 코드 구조

### 1. AsyncBigKindsClient (core/async_client.py)

```python
class AsyncBigKindsClient:
    # 세션 관리
    _auth_client: httpx.AsyncClient | None
    _is_logged_in: bool

    # 인증
    async def login(user_id, password) -> bool

    # 시각화 API
    async def get_keyword_trends(...) -> dict
    async def get_related_keywords(...) -> dict
    async def get_network_analysis(...) -> dict
```

### 2. visualization.py (tools/visualization.py)

```python
# 초기화
def init_visualization_tools(client, cache)

# MCP Tools
async def get_keyword_trends(...) -> dict
async def get_related_keywords(...) -> dict
async def get_network_analysis(...) -> dict
```

### 3. server.py (src/bigkinds_mcp/server.py)

```python
# FastMCP Tool 등록
@mcp.tool()
async def get_keyword_trends(...) -> dict

@mcp.tool()
async def get_related_keywords(...) -> dict

@mcp.tool()
async def get_network_analysis(...) -> dict
```

---

## API 파라미터 분석

### 공통 파라미터

모든 시각화 API는 다음 파라미터를 공유합니다:

```python
keyword: str           # 검색 키워드
startDate: str         # 시작일 (YYYY-MM-DD)
endDate: str           # 종료일 (YYYY-MM-DD)
providerCode: str      # 언론사 코드 (선택)
categoryCode: str      # 카테고리 코드 (선택)
incidentCode: str      # 사건/사고 코드 (선택)
```

### Tool별 고유 파라미터

**get_keyword_trends:**
```python
interval: int          # 1=일간, 2=주간, 3=월간, 4=연간
isTmUsable: bool       # 분석기사만 사용
isNotTmUsable: bool    # 분석 미사용 기사
```

**get_related_keywords:**
```python
maxNewsCount: int      # 최대 뉴스 수 (50, 100, 200, 500, 1000)
resultNumber: int      # 연관어 결과 수
analysisType: str      # "relational_word" (고정)
startNo: int           # 시작 번호 (고정: 0)
```

**get_network_analysis:**
```python
maxNewsCount: int      # 최대 뉴스 수
sectionDiv: int        # 섹션 구분 (고정: 1000)
resultNo: int          # 결과 노드 수
normalization: int     # 정규화 값
```

---

## 테스트 방법

### 1. 인증 테스트

```bash
uv run python tests/test_auth_api.py
```

**확인 사항:**
- 로그인 성공 여부
- 세션 쿠키 획득
- 시각화 API 접근 가능 여부

### 2. 파라미터 테스트

```bash
uv run python tests/test_keyword_trends.py
```

**확인 사항:**
- 다양한 날짜/키워드 조합
- interval 파라미터
- 필터 파라미터

### 3. MCP Tools 통합 테스트

```bash
uv run python tests/test_visualization_tools.py
```

**확인 사항:**
- 3개 Tool 모두 호출
- 응답 구조 검증
- 에러 처리

---

## 알려진 이슈 및 해결 방안

### 이슈 1: 키워드 트렌드 API 빈 결과

**증상:**
- 로그인 성공 (200 OK)
- API 응답 성공 (200 OK)
- 하지만 `{"root": []}` 반환

**원인 추정:**
1. 계정 권한 부족 (무료 vs 유료 계정)
2. 데이터가 실제로 없는 기간
3. API 내부 오류

**테스트한 조합:**
- 다양한 날짜 범위 (2024, 2025)
- 다양한 키워드 ("AI", "대통령", "AI,인공지능")
- 다양한 interval (1, 2, 3, 4)
- 필터 옵션 추가/제거

**모두 동일한 결과**: `{"root": []}`

**해결 방안:**
1. 다른 BigKinds 계정으로 테스트
2. 유료 계정 확인
3. BigKinds 고객센터 문의
4. API 구조 재분석 (누락된 필수 파라미터?)

### 이슈 2: 네트워크 분석 API 빈 결과

**증상:**
키워드 트렌드와 동일

**해결 방안:**
키워드 트렌드와 동일

### 성공 사례: 연관어 분석 API

**정상 작동하는 이유 분석:**

1. **다른 API 엔드포인트**: `/api/analysis/relationalWords.do`
2. **다른 파라미터 구조**: `analysisType`, `searchKey`, `indexName` 등
3. **더 관대한 권한**: 무료 계정에도 허용?

**성공 요인:**
- 로그인 정상
- API 파라미터 정확
- 응답 데이터 존재

---

## 캐싱 전략

### 구현 방식

```python
# 캐시 키 생성
cache_key = f"trends_{hash(str(cache_params))}"

# 캐시 확인
cached = _cache.get(cache_key)
if cached:
    return cached

# API 호출 후 캐시 저장
_cache.set(cache_key, result, ttl=600)  # 10분
```

### 캐시 TTL

- **시각화 API**: 10분 (600초)
- **검색 API**: 5분 (300초)

### 캐시 키 파라미터

모든 입력 파라미터의 조합으로 캐시 키 생성:
- keyword
- start_date
- end_date
- interval (트렌드)
- max_news_count (연관어, 네트워크)
- providers
- categories

---

## 성능 최적화

### 1. 비동기 처리

모든 API 호출은 `async/await` 패턴 사용:
```python
async def get_keyword_trends(...) -> dict:
    response = await self._auth_client.post(...)
```

### 2. 세션 재사용

httpx.AsyncClient를 재사용하여 연결 오버헤드 감소:
```python
self._auth_client = httpx.AsyncClient(
    verify=False,
    follow_redirects=True,
    timeout=30.0,
)
```

### 3. 캐싱

자주 요청되는 결과를 메모리에 캐싱하여 API 호출 최소화

---

## 향후 개선 사항

### 1. API 빈 결과 문제 해결

- [ ] 다른 계정으로 테스트
- [ ] BigKinds 고객센터 문의
- [ ] API 파라미터 재분석
- [ ] 브라우저 DevTools로 실제 요청 캡처

### 2. 추가 시각화 API

- [ ] 감성 분석 API (sentiment analysis)
- [ ] 토픽 모델링 API
- [ ] 시계열 예측 API

### 3. 에러 핸들링 개선

- [ ] 더 상세한 에러 메시지
- [ ] 재시도 로직 (exponential backoff)
- [ ] 로그인 실패 시 자동 재시도

### 4. 문서화

- [ ] API 응답 예시 추가
- [ ] 사용 사례 튜토리얼
- [ ] 트러블슈팅 가이드 확장

---

## 참고 자료

### 문서
- [VISUALIZATION_API.md](./VISUALIZATION_API.md): API 스펙
- [VISUALIZATION_TOOLS.md](./VISUALIZATION_TOOLS.md): Tools 사용 가이드
- [CLAUDE.md](../CLAUDE.md): 프로젝트 전체 문서

### 테스트 파일
- `tests/test_auth_api.py`: 인증 테스트
- `tests/test_keyword_trends.py`: 파라미터 테스트
- `tests/test_visualization_tools.py`: 통합 테스트

### 핵심 구현 파일
- `src/bigkinds_mcp/core/async_client.py`: 인증 + API 클라이언트
- `src/bigkinds_mcp/tools/visualization.py`: MCP Tools
- `src/bigkinds_mcp/server.py`: FastMCP 등록

---

## 요약

### 구현 완료 항목

✅ **3개 시각화 Tools 구현**
- get_keyword_trends
- get_related_keywords ⭐ 정상 작동
- get_network_analysis

✅ **자동 로그인 시스템**
- 환경변수 기반 인증
- 세션 관리
- 자동 재로그인

✅ **캐싱 시스템**
- 10분 TTL
- 파라미터 기반 캐시 키

✅ **테스트 코드**
- 인증 테스트
- 파라미터 테스트
- 통합 테스트

✅ **문서화**
- API 스펙
- 사용 가이드
- 구현 요약

### 남은 과제

⚠️ **API 빈 결과 문제**
- 키워드 트렌드: 로그인 OK, 데이터 없음
- 네트워크 분석: 로그인 OK, 데이터 없음

**다음 단계:**
1. 다른 계정으로 테스트
2. BigKinds 문의
3. API 파라미터 재분석

---

**작성일**: 2024-12-15
**작성자**: Claude (Anthropic)
**상태**: 구현 완료, 1/3 정상 작동
