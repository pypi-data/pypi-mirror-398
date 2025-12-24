# BigKinds MCP 다이어그램

> README와 문서에 사용할 수 있는 Mermaid 다이어그램 모음

## 아키텍처 다이어그램

### 전체 아키텍처

```mermaid
graph TB
    User[👤 사용자] --> Claude[Claude Desktop]
    Claude <--> MCP[BigKinds MCP Server]
    MCP <--> BigKinds[BigKinds API]

    MCP --> Search[search_news]
    MCP --> Article[get_article]
    MCP --> Trends[get_keyword_trends]
    MCP --> Export[export_all_articles]

    BigKinds --> DB[(890,000+ Articles)]

    style Claude fill:#9f6
    style MCP fill:#f96
    style BigKinds fill:#69f
```

---

## 워크플로우 다이어그램

### 뉴스 검색 흐름

```mermaid
sequenceDiagram
    actor User
    participant Claude
    participant MCP as BigKinds MCP
    participant API as BigKinds API

    User->>Claude: "오늘 AI 뉴스 검색해줘"
    Claude->>MCP: search_news(keyword="AI", ...)
    MCP->>API: POST /api/news/search.do
    API-->>MCP: 200 OK (JSON)
    MCP-->>Claude: 검색 결과 반환
    Claude-->>User: 요약 및 분석 제공

    Note over User,API: 총 소요 시간: ~10초
```

---

### 대용량 데이터 처리 흐름

```mermaid
graph LR
    A[사용자 요청] --> B{기사 수 확인}
    B -->|100건 미만| C[직접 검색]
    B -->|100-1000건| D[smart_sample]
    B -->|1000건 이상| E[export_all_articles]

    C --> F[Claude에서 즉시 분석]
    D --> F
    E --> G[로컬 파일 저장]
    G --> H[Python 분석 코드 생성]
    H --> I[사용자가 로컬에서 분석]

    style B fill:#ff9
    style E fill:#f96
    style I fill:#9f6
```

---

## 기능 맵

### 14개 MCP Tools

```mermaid
mindmap
  root((BigKinds MCP))
    검색 도구
      search_news
      get_article_count
    기사 조회
      get_article
      scrape_article_url
    분석 도구
      get_today_issues
      compare_keywords
      get_keyword_trends*
      get_related_keywords*
    유틸리티
      smart_sample
      export_all_articles
      find_category
      list_providers
      list_categories
      get_current_korean_time
```

*: 로그인 필요

---

## 사용자 여정 (User Journey)

### 첫 사용자

```mermaid
journey
    title 첫 사용자의 BigKinds MCP 여정
    section 발견
      홍보 글 발견: 3: User
      README 읽기: 4: User
    section 설치
      uv 설치: 5: User
      설정 파일 수정: 4: User
      Claude 재시작: 5: User
    section 첫 사용
      간단한 검색 시도: 5: User
      결과에 감탄: 5: User
    section 심화 사용
      트렌드 분석: 5: User
      대용량 내보내기: 5: User
      업무에 적용: 5: User
```

---

## 시간 절약 효과

### Before/After

```mermaid
gantt
    title 업무 시간 비교 (Before vs After)
    dateFormat X
    axisFormat %s

    section 과거 기사 검색
    Before (30분)    : 0, 1800s
    After (10초)     : 0, 10s

    section 트렌드 리포트
    Before (3시간)   : 0, 10800s
    After (30분)     : 0, 1800s

    section 대용량 수집
    Before (2일)     : 0, 172800s
    After (5분)      : 0, 300s
```

---

## 데이터 흐름

### 기사 전문 추출

```mermaid
graph TD
    Start[시작] --> Search[search_news]
    Search --> Summary[200자 요약 획득]

    Summary --> Need{전문 필요?}
    Need -->|예| GetArticle[get_article 호출]
    Need -->|아니오| End[종료]

    GetArticle --> TryAPI[detailView API 시도]
    TryAPI --> APISuccess{성공?}

    APISuccess -->|예| ReturnAPI[전체 본문 반환<br/>source: bigkinds_api]
    APISuccess -->|아니오| TryScrape[URL 스크래핑 시도]

    TryScrape --> ScrapSuccess{성공?}
    ScrapSuccess -->|예| ReturnScrape[스크래핑 본문 반환<br/>source: scraping]
    ScrapSuccess -->|아니오| ReturnError[오류 반환]

    ReturnAPI --> End
    ReturnScrape --> End
    ReturnError --> End

    style GetArticle fill:#f96
    style ReturnAPI fill:#9f6
    style ReturnScrape fill:#ff9
```

---

## 캐시 전략

```mermaid
graph LR
    Request[API 요청] --> Cache{캐시 확인}

    Cache -->|Hit| ReturnCache[캐시 반환<br/>⚡️ 즉시]
    Cache -->|Miss| CallAPI[API 호출]

    CallAPI --> Store[캐시 저장]
    Store --> ReturnAPI[API 결과 반환]

    ReturnCache --> TTL[TTL 체크]
    TTL -->|만료| Evict[캐시 삭제]

    style ReturnCache fill:#9f6
    style CallAPI fill:#f96

    subgraph TTL 설정
        S[검색: 5분]
        A[기사: 30분]
        T[트렌드: 10분]
    end
```

---

## 에러 처리

```mermaid
graph TD
    Start[요청 시작] --> Try[API 호출]

    Try --> Success{성공?}
    Success -->|예| Return[결과 반환]
    Success -->|아니오| CheckRetry{재시도 가능?}

    CheckRetry -->|예| Wait[지수 백오프<br/>1초, 2초, 4초]
    CheckRetry -->|아니오| Error[에러 반환]

    Wait --> Count{시도 횟수}
    Count -->|< 3| Try
    Count -->|>= 3| Error

    Return --> End[종료]
    Error --> End

    style Return fill:#9f6
    style Error fill:#f66
```

---

## 사용자 유형별 활용

```mermaid
pie title 사용자 유형별 활용 비율
    "기자/언론인" : 25
    "마케터/PR" : 20
    "투자자/애널리스트" : 20
    "학생/연구자" : 15
    "개발자" : 12
    "기업 경영진" : 8
```

---

## 기능별 인기도

```mermaid
%%{init: {'theme':'base'}}%%
graph LR
    subgraph 인기 TOP 5
        A[search_news<br/>⭐⭐⭐⭐⭐]
        B[get_article_count<br/>⭐⭐⭐⭐]
        C[export_all_articles<br/>⭐⭐⭐⭐]
        D[compare_keywords<br/>⭐⭐⭐]
        E[get_today_issues<br/>⭐⭐⭐]
    end

    style A fill:#ff6
    style B fill:#ff9
    style C fill:#ff9
```

---

## README용 플로우 차트 (간단 버전)

```
┌────────────┐
│   사용자    │
│  "AI 뉴스"  │
└─────┬──────┘
      │
      ▼
┌────────────┐
│   Claude   │
│  Desktop   │
└─────┬──────┘
      │
      ▼
┌────────────┐
│  BigKinds  │
│   MCP      │ ◄─── Python 3.12 + FastMCP
└─────┬──────┘
      │
      ▼
┌────────────┐
│  BigKinds  │
│    API     │ ◄─── 890,000+ 기사
└─────┬──────┘
      │
      ▼
┌────────────┐
│  검색 결과  │
│  10초 완료  │
└────────────┘
```

---

## ASCII 다이어그램 (텍스트 전용)

### 아키텍처 (간단)

```
   User
    │
    ▼
┌──────────────────┐
│  Claude Desktop  │
└────────┬─────────┘
         │ MCP Protocol
         ▼
┌──────────────────┐     ┌──────────────┐
│ BigKinds MCP     │────▶│ BigKinds API │
│                  │     │              │
│ • search_news    │◀────│ 890K+ News   │
│ • get_article    │     └──────────────┘
│ • trends         │
│ • export         │
└──────────────────┘
```

### 시간 비교

```
과거 기사 검색
Before: ████████████████████████████████ 30분
After:  █ 10초
       └─────────────────────────────────┘
         180배 빠름

트렌드 리포트
Before: ████████████████████████████████ 3시간
After:  ████ 30분
       └─────────────────────────────────┘
         6배 빠름
```

---

## 사용 가능 형식

### Mermaid (GitHub/GitLab/Notion)

GitHub README에 바로 삽입 가능:

````markdown
```mermaid
graph TB
    User --> Claude
    Claude --> MCP
    MCP --> BigKinds
```
````

### Draw.io / Excalidraw

위 다이어그램을 시각 도구로 재작성 가능

### PowerPoint / Keynote

발표 자료용으로 다시 디자인

### Figma

고퀄리티 프로모션 이미지 제작
