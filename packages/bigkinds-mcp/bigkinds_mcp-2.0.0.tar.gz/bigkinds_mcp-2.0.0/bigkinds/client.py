"""BigKinds HTTP API client."""

import time

import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout
import logging
from urllib3.util.retry import Retry

from .models import SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

# Disable SSL warnings for BigKinds API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BigKindsClient:
    """HTTP client for BigKinds news API."""

    BASE_URL = "https://www.bigkinds.or.kr"
    API_URL = f"{BASE_URL}/api/news/search.do"

    def __init__(
        self,
        timeout: int = 120,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        rate_limit_delay: float = 0.5,
    ):
        """
        Initialize BigKinds API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            rate_limit_delay: Delay between requests to avoid rate limiting
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.rate_limit_delay = rate_limit_delay

        # Setup session with retry strategy
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers (from legacy implementation)
        self.session.headers.update(
            {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "ko-KR,ko;q=0.9",
                "Connection": "keep-alive",
                "Content-Type": "application/json;charset=UTF-8",
                "Host": "www.bigkinds.or.kr",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/v2/news/index.do",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Sec-GPC": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
        )

    def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform a search request to BigKinds API.

        Args:
            request: Search request parameters

        Returns:
            Search response with articles

        Raises:
            RequestException: If API request fails after retries
        """
        payload = request.to_api_payload()

        logger.debug(
            f"BigKinds API request: keyword='{request.keyword}', "
            f"page={request.start_no}, count={request.result_number}"
        )

        try:
            # Apply rate limiting delay
            time.sleep(self.rate_limit_delay)

            response = self.session.post(
                self.API_URL,
                json=payload,
                timeout=self.timeout,
                verify=False,  # BigKinds API has SSL certificate issues
            )

            response.raise_for_status()
            data = response.json()

            # Create response object
            search_response = SearchResponse.from_api_response(data, request, raw_response=data)

            logger.debug(
                f"BigKinds API response: success={search_response.success}, "
                f"total={search_response.total_count}, "
                f"fetched={len(search_response.articles)}"
            )

            if not search_response.success:
                logger.warning(
                    f"BigKinds API returned error: {search_response.error_message} "
                    f"(code: {search_response.error_code})"
                )

            return search_response

        except Timeout:
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            return SearchResponse(
                success=False,
                error_message=error_msg,
                keyword=request.keyword,
                date_range=f"{request.start_date} to {request.end_date}",
            )

        except RequestException as e:
            error_msg = f"Request failed: {e}"
            logger.error(error_msg)

            # Check for specific error patterns
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    if error_data.get("errorMessage"):
                        error_msg = error_data["errorMessage"]
                except Exception:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"

            return SearchResponse(
                success=False,
                error_message=error_msg,
                keyword=request.keyword,
                date_range=f"{request.start_date} to {request.end_date}",
            )

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return SearchResponse(
                success=False,
                error_message=error_msg,
                keyword=request.keyword,
                date_range=f"{request.start_date} to {request.end_date}",
            )

    def get_total_count(self, keyword: str, start_date: str, end_date: str) -> int:
        """
        Get total count of articles without fetching them.

        Args:
            keyword: Search keyword
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Total number of articles available
        """
        request = SearchRequest(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            start_no=1,
            result_number=1,  # Minimal request to get count
        )

        response = self.search(request)
        return response.total_count if response.success else 0

    def health_check(self) -> bool:
        """
        Check if BigKinds API is accessible.

        Returns:
            True if API is responsive
        """
        try:
            # Simple test search
            test_request = SearchRequest(
                keyword="test",
                start_date="2024-01-01",
                end_date="2024-01-02",
                result_number=1,
            )

            response = self.search(test_request)
            return response.success

        except Exception as e:
            logger.warning(f"BigKinds API health check failed: {e}")
            return False

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            logger.debug("BigKinds client session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
