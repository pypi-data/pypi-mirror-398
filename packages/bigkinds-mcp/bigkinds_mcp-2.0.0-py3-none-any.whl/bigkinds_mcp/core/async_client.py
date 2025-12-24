"""기존 BigKindsClient의 비동기 래퍼.

PRD AC9 충족:
- 재시도 로직 (최대 3회)
- 타임아웃 핸들링 (30초)

PRD AC16 충족:
- Circuit Breaker 패턴 적용
- API 장애 시 자동 차단 및 캐시 fallback
"""

import asyncio
import logging
import os
from functools import partial, wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import httpx

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from bigkinds.models import SearchRequest, SearchResponse


# ============================================================
# 환경변수 기반 설정 (PRD AC9)
# ============================================================
TIMEOUT = float(os.getenv("BIGKINDS_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("BIGKINDS_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("BIGKINDS_RETRY_DELAY", "1.0"))


# ============================================================
# 재시도 데코레이터 (PRD AC9)
# ============================================================
T = TypeVar("T")


def retry_async(
    max_attempts: int = MAX_RETRIES,
    delay: float = RETRY_DELAY,
    exceptions: tuple = (httpx.RequestError, httpx.HTTPStatusError),
) -> Callable:
    """비동기 함수용 재시도 데코레이터.

    Args:
        max_attempts: 최대 시도 횟수 (기본: 3)
        delay: 재시도 간격 (기본: 1초, 지수 백오프 적용)
        exceptions: 재시도할 예외 유형
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        # 지수 백오프: 1초, 2초, 4초...
                        wait_time = delay * (2 ** attempt)
                        await asyncio.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator


class AsyncBigKindsClient:
    """BigKindsClient를 비동기로 래핑.

    PRD AC16: Circuit Breaker 패턴 적용
    """

    def __init__(self, **kwargs):
        # 지연 임포트로 순환 참조 방지
        from bigkinds.client import BigKindsClient

        self._client = BigKindsClient(**kwargs)

        # 로그인 세션용 httpx client (visualization API 전용)
        self._auth_client: httpx.AsyncClient | None = None
        self._is_logged_in = False

        # Circuit Breakers (PRD AC16)
        self.search_circuit = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            recovery_timeout=30,
            name="search_api",
        )
        self.detail_circuit = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            recovery_timeout=30,
            name="detail_api",
        )
        self.visualization_circuit = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            recovery_timeout=30,
            name="visualization_api",
        )

        # 캐시 (Circuit Breaker fallback용)
        from .cache import MCPCache

        self._cache = MCPCache()

    async def search(self, request: "SearchRequest") -> "SearchResponse":
        """비동기 검색 (Circuit Breaker 적용)."""
        cache_key = f"search_{request.keyword}_{request.start_date}_{request.end_date}_{request.start_no}"

        async def _search_internal():
            """실제 검색 로직."""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, partial(self._client.search, request))

        try:
            # Circuit Breaker를 통해 API 호출
            result = await self.search_circuit.call(_search_internal)
            # 성공 시 캐시 저장
            self._cache.set_search(result, keyword=request.keyword, start_date=request.start_date, end_date=request.end_date, start_no=request.start_no)
            return result
        except CircuitBreakerOpenError:
            # Circuit open 시 캐시 데이터 반환 시도
            cached = self._cache.get_search(keyword=request.keyword, start_date=request.start_date, end_date=request.end_date, start_no=request.start_no)
            if cached:
                logger.info(f"[CircuitBreaker] Returning cached data for {cache_key}")
                return cached
            else:
                # 캐시도 없으면 에러 발생
                raise

    async def get_total_count(
        self, keyword: str, start_date: str, end_date: str
    ) -> int:
        """비동기 총 개수 조회."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self._client.get_total_count, keyword, start_date, end_date),
        )

    async def health_check(self) -> bool:
        """비동기 헬스 체크."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._client.health_check)

    async def close(self):
        """클라이언트 종료."""
        self._client.close()
        if self._auth_client:
            await self._auth_client.aclose()

    @retry_async()
    async def get_today_issues(
        self,
        date: str | None = None,
    ) -> dict[str, Any]:
        """
        오늘/특정 날짜의 인기 이슈(Top 뉴스) 조회.

        Args:
            date: 조회할 날짜 (YYYY-MM-DD). None이면 오늘

        Returns:
            인기 이슈 목록 (모든 카테고리 포함, 클라이언트에서 필터링 필요)

        Note:
            BigKinds API는 category=전체만 지원합니다.
            카테고리별 필터링은 응답의 topic_category 필드를 사용해
            클라이언트 측에서 수행해야 합니다.
        """
        from datetime import datetime

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        url = "https://www.bigkinds.or.kr/search/trendReportData2.do"
        # API는 category=전체만 지원 (다른 값 전달 시 에러 발생)
        params = {"SEARCH_DATE": date, "category": "전체"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bigkinds.or.kr/v2/news/weekendNews.do",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }

        async with httpx.AsyncClient(
            verify=False,  # BigKinds API에서 SSL 인증서 검증 비활성화 필요
            follow_redirects=True,
            timeout=httpx.Timeout(TIMEOUT, connect=10.0),
        ) as client:
            # 세션/쿠키 획득을 위해 먼저 메인 페이지 접속
            await client.get("https://www.bigkinds.or.kr/", headers=headers)

            # API 호출
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    async def login(self, user_id: str | None = None, password: str | None = None) -> bool:
        """
        BigKinds에 로그인하여 인증 세션 획득.

        Args:
            user_id: 사용자 ID (없으면 환경변수 BIGKINDS_USER_ID 사용)
            password: 비밀번호 (없으면 환경변수 BIGKINDS_USER_PASSWORD 사용)

        Returns:
            로그인 성공 여부
        """
        user_id = user_id or os.getenv("BIGKINDS_USER_ID", "")
        password = password or os.getenv("BIGKINDS_USER_PASSWORD", "")

        if not user_id or not password:
            return False

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "Origin": "https://www.bigkinds.or.kr",
            "Referer": "https://www.bigkinds.or.kr/v2/member/login.do",
            "X-Requested-With": "XMLHttpRequest",
        }

        # httpx client 생성 (세션 유지, PRD AC9 타임아웃)
        if not self._auth_client:
            self._auth_client = httpx.AsyncClient(
                verify=False,
                follow_redirects=True,
                timeout=httpx.Timeout(TIMEOUT, connect=10.0),
            )

        try:
            # 메인 페이지 접속 (세션 초기화)
            await self._auth_client.get("https://www.bigkinds.or.kr/", headers=headers)

            # 로그인 시도
            login_data = {
                "userId": user_id,
                "userPassword": password,
            }

            login_endpoints = [
                "/api/account/signin.do",
                "/api/account/signin2023.do",
            ]

            for endpoint in login_endpoints:
                url = f"https://www.bigkinds.or.kr{endpoint}"

                try:
                    login_resp = await self._auth_client.post(
                        url,
                        json=login_data,
                        headers=headers,
                    )

                    if login_resp.status_code == 200:
                        try:
                            result = login_resp.json()
                            # Success check: userSn exists in response (user info returned)
                            if result.get("userSn") or result.get("success") or result.get("result") == "success":
                                self._is_logged_in = True
                                return True
                        except Exception as e:
                            logger.debug(f"Login response parsing failed: {e}")
                except Exception as e:
                    logger.debug(f"Login attempt to {endpoint} failed: {e}")

            return False
        except Exception as e:
            logger.warning(f"Login failed with exception: {e}")
            return False

    # ================================================================
    # DEPRECATED: get_network_analysis
    # 사유: /news/getNetworkDataAnalysis.do API는 브라우저 전용
    #       httpx 직접 호출 시 302 → /err/error400.do 리다이렉트
    # ================================================================

    @retry_async()
    async def get_keyword_trends(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        interval: int = 1,
        provider_code: str = "",
        category_code: str = "",
        incident_code: str = "",
        is_tm_usable: bool = False,
        is_not_tm_usable: bool = False,
    ) -> dict[str, Any]:
        """
        키워드 트렌드 데이터 조회 (로그인 필수).

        키워드별 기사 수 추이를 시간축 그래프로 분석.

        Args:
            keyword: 검색 키워드 (콤마로 여러 키워드 구분 가능)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            interval: 시간 단위 힌트 (1: 일간, 2: 주간, 3: 월간, 4: 연간)
                      참고: API가 날짜 범위에 따라 자동으로 granularity 조정
            provider_code: 언론사 코드
            category_code: 카테고리 코드
            incident_code: 사건/사고 코드
            is_tm_usable: 분석기사만 사용
            is_not_tm_usable: 분석 미사용 기사

        Returns:
            키워드 트렌드 결과:
                - root: [{keyword: str, data: [{d: str, c: int}]}]
        """
        # 로그인 필요
        if not self._is_logged_in:
            login_success = await self.login()
            if not login_success:
                return {
                    "error": "Login required. Please set BIGKINDS_USER_ID and BIGKINDS_USER_PASSWORD environment variables.",
                    "root": [],
                }

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "Origin": "https://www.bigkinds.or.kr",
            "Referer": "https://www.bigkinds.or.kr/v2/news/visualize.do",
            "X-Requested-With": "XMLHttpRequest",
        }

        data = {
            "keyword": keyword,
            "startDate": start_date,
            "endDate": end_date,
            "interval": interval,
            "searchKey": keyword,   # 필수 파라미터
            "indexName": "news",    # 필수 파라미터
            "isTmUsable": is_tm_usable,
            "isNotTmUsable": is_not_tm_usable,
        }

        # 선택적 파라미터 추가
        if provider_code:
            data["providerCode"] = provider_code
        if category_code:
            data["categoryCode"] = category_code
        if incident_code:
            data["incidentCode"] = incident_code

        try:
            response = await self._auth_client.post(
                "https://www.bigkinds.or.kr/api/analysis/keywordTrends.do",
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "root": [],
            }

    @retry_async()
    async def get_related_keywords(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        max_news_count: int = 100,
        result_number: int = 50,
        provider_code: str = "",
        category_code: str = "",
        incident_code: str = "",
        is_tm_usable: bool = False,
    ) -> dict[str, Any]:
        """
        연관어 분석 데이터 조회 (로그인 필수).

        검색 키워드와 연관된 키워드를 TF-IDF 기반으로 분석.

        Args:
            keyword: 검색 키워드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            max_news_count: 최대 뉴스 수 (50, 100, 200, 500, 1000 중 선택)
            result_number: 결과 수
            provider_code: 언론사 코드
            category_code: 카테고리 코드
            incident_code: 사건/사고 코드
            is_tm_usable: 분석기사만 사용

        Returns:
            연관어 분석 결과:
                - topics: {data: [{name, weight, tf}]}
                - news: {documentCount, resultList}
        """
        # 로그인 필요
        if not self._is_logged_in:
            login_success = await self.login()
            if not login_success:
                return {
                    "error": "Login required. Please set BIGKINDS_USER_ID and BIGKINDS_USER_PASSWORD environment variables.",
                    "topics": {"data": []},
                    "news": {"documentCount": 0},
                }

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "Origin": "https://www.bigkinds.or.kr",
            "Referer": "https://www.bigkinds.or.kr/v2/news/visualize.do",
            "X-Requested-With": "XMLHttpRequest",
        }

        data = {
            "keyword": keyword,
            "startDate": start_date,
            "endDate": end_date,
            "maxNewsCount": max_news_count,
            "resultNumber": result_number,
            "analysisType": "relational_word",
            "sortMethod": "score",
            "startNo": 1,
            "isTmUsable": True,
            "searchKey": keyword,  # Required parameter
            "indexName": "news",   # Required parameter
        }

        # 선택적 파라미터
        if provider_code:
            data["providerCode"] = provider_code
        if category_code:
            data["categoryCode"] = category_code
        if incident_code:
            data["incidentCode"] = incident_code
        # isTmUsable is already set to True by default above

        try:
            response = await self._auth_client.post(
                "https://www.bigkinds.or.kr/api/analysis/relationalWords.do",
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "topics": {"data": []},
                "news": {"documentCount": 0},
            }

    async def get_article_detail(
        self,
        news_id: str,
    ) -> dict[str, Any]:
        """
        BigKinds에서 기사 상세 정보(전체 본문 포함) 조회.

        검색 API는 200자 요약만 반환하지만, 이 API는 전체 본문(CONTENT)을 반환합니다.

        PRD AC16: Circuit Breaker 적용 및 캐시 fallback

        Args:
            news_id: BigKinds 기사 ID (예: "02100101.20251215174513002")

        Returns:
            기사 상세 정보:
                - detail: {TITLE, CONTENT, BYLINE, PROVIDER, ...}
                - lawsInfo: 관련 법률 정보
        """
        # 캐시 확인
        cached = self._cache.get_article(news_id)
        if cached:
            logger.debug(f"[Cache Hit] Article detail for {news_id}")
            return cached

        @retry_async()
        async def _fetch_detail():
            """실제 API 호출 로직."""
            # 브라우저와 동일한 헤더
            base_headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
            }

            ajax_headers = {
                **base_headers,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }

            async with httpx.AsyncClient(
                verify=False,  # BigKinds API에서 SSL 인증서 검증 비활성화 필요
                follow_redirects=True,
                timeout=httpx.Timeout(TIMEOUT, connect=10.0),
            ) as client:
                # 1. 메인 페이지 방문 (세션 쿠키 획득)
                await client.get(
                    "https://www.bigkinds.or.kr/",
                    headers=base_headers,
                )

                # 2. 최신뉴스 페이지 방문 (브라우저 Referer와 동일)
                await client.get(
                    "https://www.bigkinds.or.kr/v2/news/recentNews.do",
                    headers=base_headers,
                )

                # 3. 기사 상세 API 호출
                detail_headers = {
                    **ajax_headers,
                    "Referer": "https://www.bigkinds.or.kr/v2/news/recentNews.do",
                }

                url = "https://www.bigkinds.or.kr/news/detailView.do"
                params = {
                    "docId": news_id,
                    "returnCnt": 1,
                    "sectionDiv": 1000,
                }

                response = await client.get(url, params=params, headers=detail_headers)

                # 에러 페이지 확인
                if "error" in str(response.url).lower():
                    return {
                        "success": False,
                        "error": "SESSION_ERROR",
                        "message": "세션 초기화 실패. 다시 시도해주세요.",
                        "url": str(response.url),
                    }

                response.raise_for_status()

                try:
                    data = await response.json()
                except Exception:
                    return {
                        "success": False,
                        "error": "PARSE_ERROR",
                        "message": "응답 파싱 실패",
                        "raw_text": response.text[:500],
                    }

                # detail 필드 확인
                if "detail" in data and data["detail"]:
                    return {
                        "success": True,
                        **data,
                    }
                else:
                    return {
                        "success": False,
                        "error": "NO_DETAIL",
                        "message": "기사 상세 정보를 찾을 수 없습니다.",
                        "raw": data,
                    }

        # Circuit Breaker를 통해 API 호출
        try:
            result = await self.detail_circuit.call(_fetch_detail)
            # 성공 시 캐시 저장
            if result.get("success"):
                self._cache.set_article(news_id, result)
            return result
        except CircuitBreakerOpenError:
            # Circuit open 시 캐시 데이터 반환 시도
            if cached:
                logger.info(f"[CircuitBreaker] Returning cached article for {news_id}")
                return cached
            else:
                # 캐시도 없으면 에러 발생
                raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
