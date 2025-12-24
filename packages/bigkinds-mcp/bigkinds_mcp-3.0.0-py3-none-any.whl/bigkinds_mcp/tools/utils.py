"""유틸리티 MCP Tools."""

from datetime import datetime
from zoneinfo import ZoneInfo

# 한국 시간대
KST = ZoneInfo("Asia/Seoul")

# BigKinds 언론사 코드 (실제 API 응답 기준, 72개)
# 2025-12-15 체계적 수집
PROVIDER_CODES = {
    # 종합일간지 (011*)
    "01100101": "경향신문",
    "01100201": "국민일보",
    "01100401": "동아일보",
    "01100501": "문화일보",
    "01100611": "서울신문",
    "01100701": "세계일보",
    "01100751": "아시아투데이",
    "01100801": "조선일보",
    "01100901": "중앙일보",
    "01101001": "한겨레",
    "01101101": "한국일보",
    # 경제지/지역일간지 (012*, 013*, 014*)
    "01200101": "경기일보",
    "01200401": "인천일보",
    "01300101": "강원도민일보",
    "01300201": "강원일보",
    "01400101": "충청타임즈",
    "01400201": "대전일보",
    "01400301": "동양일보",
    "01400401": "중부매일",
    "01400501": "중부일보",
    "01400551": "충북일보",
    "01400601": "충청일보",
    "01400801": "금강일보",
    # 경북/전라/경남/제주 지역지 (015*, 016*, 017*)
    "01500151": "경남도민일보",
    "01500201": "경북일보",
    "01500501": "대구일보",
    "01500601": "매일신문",
    "01500701": "부산일보",
    "01500801": "영남일보",
    "01501001": "대구신문",
    "01501101": "경북도민일보",
    "01501201": "경북매일신문",
    "01501301": "울산신문",
    "01600201": "광주매일신문",
    "01600451": "남도일보",
    "01600801": "전남일보",
    "01601001": "전북도민일보",
    "01601101": "전북일보",
    "01620001": "광남일보",
    "01700201": "한라일보",
    # 경제전문지 (021*)
    "02100051": "대한경제",
    "02100101": "매일경제",
    "02100201": "머니투데이",
    "02100311": "서울경제",
    "02100351": "이투데이",
    "02100401": "메트로경제",
    "02100501": "파이낸셜뉴스",
    "02100601": "한국경제",
    "02100701": "헤럴드경제",
    "02100801": "아시아경제",
    "02100851": "아주경제",
    # 인터넷신문 (041*)
    "04100058": "노컷뉴스",
    "04100078": "뉴스핌",
    "04100158": "데일리안",
    "04100608": "브레이크뉴스",
    "04100958": "EBN",
    "04101008": "이데일리",
    "04102008": "쿠키뉴스",
    "04104008": "프레시안",
    # 기타
    "05520352": "당진시대",
    "06101202": "주간한국",
    # 전문지 (071*)
    "07100251": "미디어오늘",
    "07100501": "전자신문",
    "07100502": "환경일보",
    "07101201": "디지털타임스",
    # 방송사 (081*, 082*)
    "08100101": "KBS",
    "08100301": "SBS",
    "08100401": "YTN",
    "08200101": "OBS",
    # 스포츠지 (101*)
    "10100101": "스포츠서울",
    "10100301": "스포츠한국",
    "10100401": "스포츠월드",
}

# 역매핑 (이름 -> 코드)
PROVIDER_NAME_TO_CODE = {v: k for k, v in PROVIDER_CODES.items()}

# BigKinds 카테고리 코드 (9-digit numeric format)
# User-friendly names → API numeric codes
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


def get_current_korean_time() -> dict:
    """
    현재 한국 시간(KST)을 조회합니다.

    날짜/시간 기반 검색 시 참조용으로 사용합니다.
    BigKinds API는 한국 시간대(KST, UTC+9) 기준으로 동작합니다.

    Returns:
        현재 한국 시간 정보:
            - datetime: ISO 8601 형식 (YYYY-MM-DDTHH:MM:SS+09:00)
            - date: 날짜 (YYYY-MM-DD)
            - time: 시간 (HH:MM:SS)
            - year: 연도
            - month: 월
            - day: 일
            - weekday: 요일 (한글)
            - hour: 시
            - minute: 분
            - timezone: 시간대 정보

    Example:
        검색 기간 설정 시 오늘 날짜 확인:
        >>> time_info = get_current_korean_time()
        >>> today = time_info["date"]  # "2025-12-15"
    """
    now = datetime.now(KST)

    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "weekday": weekdays[now.weekday()],
        "hour": now.hour,
        "minute": now.minute,
        "timezone": {
            "name": "Asia/Seoul",
            "abbreviation": "KST",
            "offset": "+09:00",
            "description": "Korea Standard Time",
        },
    }


def find_category(
    query: str,
    category_type: str = "all",
) -> dict:
    """
    언론사 또는 카테고리 코드를 검색합니다.

    BigKinds 검색 시 providers나 categories 파라미터에 사용할 값을 찾습니다.

    Args:
        query: 검색어 (예: "경향", "한겨레", "경제", "IT")
        category_type: 검색 대상
            - "all" (기본값): 언론사와 카테고리 모두 검색
            - "provider": 언론사만 검색
            - "category": 카테고리만 검색

    Returns:
        검색 결과:
            - providers: 매칭된 언론사 목록 [{code, name}]
            - categories: 매칭된 카테고리 목록 [{code, name}]
            - query: 검색어
            - total_matches: 총 매칭 수

    Example:
        >>> find_category("한겨레")
        {"providers": [{"code": "01100901", "name": "한겨레"}], "categories": [], ...}

        >>> find_category("경제")
        {"providers": [{"code": "01101101", "name": "매일경제"}, ...], "categories": [{"code": "경제", "name": "경제"}], ...}
    """
    query_lower = query.lower()
    results = {
        "providers": [],
        "categories": [],
        "query": query,
        "total_matches": 0,
    }

    # 언론사 검색
    if category_type in ("all", "provider"):
        for code, name in PROVIDER_CODES.items():
            if query_lower in name.lower() or query_lower in code:
                results["providers"].append({"code": code, "name": name})

    # 카테고리 검색
    if category_type in ("all", "category"):
        # CATEGORY_CODES는 {display_name: numeric_code} 형태
        for display_name, numeric_code in CATEGORY_CODES.items():
            if query_lower in display_name.lower() or query_lower in numeric_code.lower():
                results["categories"].append({"code": numeric_code, "name": display_name})

    results["total_matches"] = len(results["providers"]) + len(results["categories"])

    return results


def list_providers() -> dict:
    """
    사용 가능한 모든 언론사 코드 목록을 반환합니다.

    Returns:
        언론사 목록:
            - providers: 모든 언론사 [{code, name}]
            - total: 총 언론사 수
            - groups: 그룹별 분류 (신문, 방송 등)

    Example:
        검색 시 특정 언론사만 필터링하려면:
        >>> providers = list_providers()
        >>> search_news(keyword="AI", providers=["경향신문", "한겨레"], ...)
    """
    providers = [{"code": code, "name": name} for code, name in sorted(PROVIDER_CODES.items(), key=lambda x: x[1])]

    # 그룹별 분류
    newspapers = [p for p in providers if p["code"].startswith("011")]
    broadcasters = [p for p in providers if p["code"].startswith("02")]
    tech_papers = [p for p in providers if p["code"].startswith("012")]

    return {
        "providers": providers,
        "total": len(providers),
        "groups": {
            "newspapers": {"name": "종합일간지", "count": len(newspapers), "items": newspapers},
            "tech_papers": {"name": "전문지", "count": len(tech_papers), "items": tech_papers},
            "broadcasters": {"name": "방송사", "count": len(broadcasters), "items": broadcasters},
        },
    }


def list_categories() -> dict:
    """
    사용 가능한 모든 카테고리 코드 목록을 반환합니다.

    Returns:
        카테고리 목록:
            - categories: 모든 카테고리 [{code, name}]
            - total: 총 카테고리 수

    Example:
        검색 시 특정 카테고리만 필터링하려면:
        >>> categories = list_categories()
        >>> search_news(keyword="AI", categories=["경제", "IT_과학"], ...)
    """
    categories = [{"code": code, "name": name} for code, name in sorted(CATEGORY_CODES.items())]

    return {
        "categories": categories,
        "total": len(categories),
    }


def generate_bigkinds_url(news_id: str) -> str:
    """
    news_id로 BigKinds 기사 상세 페이지 URL을 생성합니다.

    Args:
        news_id: BigKinds 기사 ID (예: "02100101.20251215172508001")

    Returns:
        BigKinds 기사 상세 페이지 URL

    Example:
        >>> generate_bigkinds_url("02100101.20251215172508001")
        "https://www.bigkinds.or.kr/v2/news/newsDetail.do?newsId=02100101.20251215172508001"
    """
    if not news_id:
        return None
    return f"https://www.bigkinds.or.kr/v2/news/newsDetail.do?newsId={news_id}"
