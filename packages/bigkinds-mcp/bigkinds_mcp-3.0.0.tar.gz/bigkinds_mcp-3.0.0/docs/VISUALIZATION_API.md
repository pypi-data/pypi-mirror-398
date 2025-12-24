# BigKinds 시각화 API 엔드포인트

BigKinds 웹사이트의 시각화 기능 API 엔드포인트 분석 결과입니다.

> **주의**: 모든 시각화 API는 **로그인 필수**입니다. 세션 기반 인증이 필요합니다.

## 1. 관계도 분석 (Network Analysis)

개체(인물, 기관, 장소, 키워드) 간의 관계를 네트워크 그래프로 시각화합니다.

### 주요 API

#### `POST /news/getNetworkDataAnalysis.do`

네트워크 분석 데이터 조회

**Request Parameters:**
```javascript
{
  keyword: string,           // 검색 키워드
  startDate: string,         // 시작일 (YYYY-MM-DD)
  endDate: string,           // 종료일 (YYYY-MM-DD)
  maxNewsCount: number,      // 최대 뉴스 수 (기본: 1000)
  sectionDiv: number,        // 섹션 구분 (기본: 1000)
  resultNo: number,          // 결과 수 (기본: 100)
  normalization: number,     // 정규화 값 (기본: 10)
  isTmUsable: boolean,       // TM 사용 여부
  isNotTmUsable: boolean,    // TM 미사용 여부
  searchFtr: string,         // 검색 필터 타입
  searchScope: string,       // 검색 범위
  providerCode: string,      // 언론사 코드 (콤마 구분)
  categoryCode: string,      // 카테고리 코드
  incidentCode: string,      // 사건/사고 코드
  keywordFilterJson: string  // 필터 JSON
}
```

**Response:**
```javascript
{
  nodes: [
    {
      id: string,              // 노드 ID
      title: string,           // 표시명
      label_ne: string,        // 개체명
      category: string,        // 카테고리 (PERSON, ORGNIZATION, LOCATION, KEYWORD, NEWS, ROOT)
      weight: number,          // 가중치
      node_size: number,       // 노드 크기
      larm_knowledgebase_sn: string,  // 지식베이스 일련번호
      kb_use_yn: string,       // 지식베이스 사용 여부
      kb_service_id: string    // 지식베이스 서비스 ID
    }
  ],
  links: [
    {
      from: string,            // 출발 노드 ID
      to: string,              // 도착 노드 ID
      weight: number           // 관계 가중치
    }
  ],
  needges: [...],              // 엣지 정보
  provider2node: {...},        // 언론사-노드 매핑
  newsIds: string[],           // 관련 뉴스 ID 목록
  newsList: [...],             // 관련 뉴스 목록
  newsCluster: string,         // 뉴스 클러스터
  kbSearchPersonJson: {...}    // 지식베이스 인물 검색 결과
}
```

#### `POST /news/nodeDetailData.do`

노드 상세 정보 조회 (인물, 기관, 장소의 지식베이스 정보)

**Request Parameters:**
```javascript
{
  larm_knowledgebase_sn: string,  // 지식베이스 일련번호
  category: string,               // 카테고리
  kb_use_yn: string,              // 지식베이스 사용 여부
  label_ne: string,               // 개체명
  kb_service_id: string           // 지식베이스 서비스 ID
}
```

**Response:**
```javascript
{
  baseData: {
    BASE_NAME: string,        // 이름
    BASE_IMAGE_URL: string    // 이미지 URL
  },
  baseItem: [
    {
      ITEM_NAME: string,      // 항목명 (예: 생년월일, 소속)
      ITEM_VALUE: string      // 항목값
    }
  ]
}
```

---

## 2. 키워드 트렌드 (Keyword Trends)

키워드별 기사 수 추이를 시간축 그래프로 시각화합니다.

### 주요 API

#### `POST /api/analysis/keywordTrends.do`

키워드 트렌드 데이터 조회

**Request Parameters:**
```javascript
{
  keyword: string,           // 검색 키워드 (콤마로 여러 키워드 구분 가능)
  startDate: string,         // 시작일 (YYYY-MM-DD)
  endDate: string,           // 종료일 (YYYY-MM-DD)
  interval: number,          // 시간 단위 (1: 일간, 2: 주간, 3: 월간, 4: 연간)
  providerCode: string,      // 언론사 코드
  categoryCode: string,      // 카테고리 코드
  incidentCode: string,      // 사건/사고 코드
  isTmUsable: boolean,       // 분석기사만 사용
  isNotTmUsable: boolean     // 분석 미사용 기사
}
```

**Response:**
```javascript
{
  root: [
    {
      keyword: string,        // 키워드
      data: [
        {
          d: string,          // 날짜 (YYYY-MM-DD)
          c: number           // 기사 수
        }
      ]
    }
  ]
}
```

#### `POST /api/analysis/search/keyword.do`

키워드 분석 (형태소 분석)

**Request:**
```javascript
{
  content: string            // 분석할 텍스트
}
```

**Response:**
```javascript
{
  resultStr: string          // 분석된 키워드 문자열
}
```

---

## 3. 연관어 분석 (Related Keywords Analysis)

검색 키워드와 연관된 키워드를 워드클라우드/차트로 시각화합니다.

### 주요 API

#### `POST /api/analysis/relationalWords.do`

연관어 분석 데이터 조회

**Request Parameters:**
```javascript
{
  keyword: string,           // 검색 키워드
  startDate: string,         // 시작일 (YYYY-MM-DD)
  endDate: string,           // 종료일 (YYYY-MM-DD)
  maxNewsCount: number,      // 최대 뉴스 수 (50, 100, 200, 500, 1000)
  resultNumber: number,      // 결과 수
  analysisType: string,      // 분석 타입 ("relational_word") - REQUIRED
  sortMethod: string,        // 정렬 방법 ("score") - REQUIRED
  startNo: number,           // 시작 번호 (1) - REQUIRED
  isTmUsable: boolean,       // 분석기사만 사용 (true) - REQUIRED
  searchKey: string,         // 검색 키 (keyword와 동일) - REQUIRED ⚠️
  indexName: string,         // 인덱스 이름 ("news") - REQUIRED ⚠️
  providerCode: string,      // 언론사 코드 (선택)
  categoryCode: string,      // 카테고리 코드 (선택)
  incidentCode: string,      // 사건/사고 코드 (선택)
  searchInKey: string        // 추가 검색 키워드 (선택)
}
```

**⚠️ 중요**: `searchKey`와 `indexName` 파라미터가 누락되면 "토픽랭크 연산 중 오류가 발생하였습니다" 500 에러가 발생합니다.

**Response:**
```javascript
{
  topics: {
    data: [
      {
        name: string,         // 연관 키워드
        weight: number,       // 가중치 (TF-IDF)
        tf: number            // Term Frequency (계산됨)
      }
    ]
  },
  news: {
    documentCount: number,    // 총 문서 수
    resultList: [...]         // 뉴스 목록
  }
}
```

---

## 4. 기타 관련 API

### `POST /api/news/searchWithDetails.do`

뉴스 상세 정보 포함 검색

**Request:**
```javascript
{
  keyword: string,
  startDate: string,
  endDate: string,
  newsIds: string,           // 뉴스 ID 목록 (콤마 구분)
  resultNo: number
}
```

### `POST /api/private/analysis/create.do`

분석 결과 저장 (로그인 필수)

---

## 인증 요구사항

모든 시각화 API는 세션 기반 인증이 필요합니다:

1. BigKinds 웹사이트에서 회원가입 및 로그인
2. 로그인 후 발급되는 세션 쿠키 (`Bigkinds=...`) 필요
3. 비회원의 경우 연관어 분석에서 최대 3개월 기간 제한

## MCP 서버 구현 고려사항

현재 BigKinds MCP 서버는 공개 API만 사용합니다. 시각화 API를 구현하려면:

1. **방법 1: 사용자 인증 정보 저장**
   - 환경변수로 BigKinds 로그인 정보 받기
   - 서버 시작 시 로그인 세션 획득
   - 세션 만료 시 자동 재로그인

2. **방법 2: Playwright 연동**
   - 헤드리스 브라우저로 로그인 자동화
   - 세션 쿠키 추출 후 API 호출에 사용

3. **제한사항**
   - BigKinds 이용약관 확인 필요
   - 과도한 API 호출 시 차단 가능성
   - 세션 관리 복잡성

## 소스 파일 참조

- `/js/ptech/analysis/relationships.js` - 관계도 분석
- `/js/ptech/news/visualization/trend-chart.js` - 키워드 트렌드
- `/js/ptech/news/visualization/relational-word.js` - 연관어 분석
