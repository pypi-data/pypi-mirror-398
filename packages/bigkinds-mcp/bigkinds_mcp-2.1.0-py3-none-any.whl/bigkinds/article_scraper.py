"""원본 기사 페이지 스크래퍼 - BigKinds에서 받은 URL로 실제 기사 내용 추출."""

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapedArticle:
    """스크래핑된 기사 데이터."""

    # 원본 정보
    source_url: str
    final_url: str | None = None

    # 메타데이터
    title: str | None = None
    description: str | None = None
    author: str | None = None
    published_date: str | None = None
    modified_date: str | None = None
    publisher: str | None = None
    section: str | None = None
    keywords: list[str] = field(default_factory=list)

    # 본문
    content: str | None = None
    content_html: str | None = None

    # 이미지
    main_image: str | None = None
    images: list[dict] = field(default_factory=list)  # [{"url": ..., "caption": ...}]

    # 추가 메타
    canonical_url: str | None = None
    language: str | None = None

    # 스크래핑 상태
    success: bool = False
    error: str | None = None
    http_status: int | None = None


class ArticleScraper:
    """원본 기사 페이지 스크래퍼."""

    # 언론사별 본문 셀렉터 (우선순위 순)
    CONTENT_SELECTORS = [
        # 일반적인 기사 본문 셀렉터
        "article .article-body",
        "article .article-content",
        "#articleBody",
        "#article-body",
        "#articeBody",
        ".article_body",
        ".article-body",
        ".news_body",
        ".news-content",
        ".view_content",
        ".story-body",
        ".entry-content",
        # 특정 언론사
        "#article_content",  # 조선일보
        ".article_txt",  # 한겨레
        "#newsct_article",  # 네이버뉴스
        ".news_end",  # 매일경제
        "#content",  # 일반
        "article",  # 폴백
    ]

    # 제목 셀렉터
    TITLE_SELECTORS = [
        "h1.article-title",
        "h1.news-title",
        "h1.view_title",
        "#articleTitle",
        ".article_title h1",
        "article h1",
        "h1",
    ]

    def __init__(
        self,
        timeout: int = 15,
        user_agent: str | None = None,
    ):
        """
        Args:
            timeout: HTTP 요청 타임아웃 (초)
            user_agent: 커스텀 User-Agent
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent
                or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            }
        )

    def scrape(self, url: str) -> ScrapedArticle:
        """
        URL에서 기사 스크래핑.

        Args:
            url: 기사 URL

        Returns:
            ScrapedArticle 객체
        """
        result = ScrapedArticle(source_url=url)

        try:
            # HTTP 요청
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            result.http_status = response.status_code
            result.final_url = response.url

            if response.status_code != 200:
                result.error = f"HTTP {response.status_code}"
                return result

            # 인코딩 처리
            response.encoding = response.apparent_encoding or "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            # 메타데이터 추출
            self._extract_metadata(soup, result)

            # 본문 추출
            self._extract_content(soup, result)

            # 이미지 추출
            self._extract_images(soup, result)

            result.success = True
            logger.debug(f"스크래핑 성공: {url}")

        except requests.Timeout:
            result.error = "요청 타임아웃"
            logger.warning(f"타임아웃: {url}")

        except requests.RequestException as e:
            result.error = f"요청 실패: {e}"
            logger.warning(f"요청 실패: {url} - {e}")

        except Exception as e:
            result.error = f"스크래핑 실패: {e}"
            logger.error(f"스크래핑 실패: {url} - {e}")

        return result

    def _extract_metadata(self, soup: BeautifulSoup, result: ScrapedArticle):
        """메타데이터 추출."""
        # Open Graph 태그
        result.title = self._get_meta(soup, "og:title") or self._get_title(soup)
        result.description = self._get_meta(soup, "og:description") or self._get_meta(
            soup, "description", "name"
        )
        result.main_image = self._get_meta(soup, "og:image")
        result.publisher = (
            self._get_meta(soup, "og:site_name")
            or self._get_meta(soup, "publisher", "name")
            or self._get_meta(soup, "application-name", "name")
        )
        result.canonical_url = self._get_meta(soup, "og:url") or self._get_canonical(soup)

        # Article 메타태그
        result.published_date = (
            self._get_meta(soup, "article:published_time")
            or self._get_meta(soup, "datePublished", "name")
            or self._get_meta(soup, "pubdate", "name")
        )
        result.modified_date = self._get_meta(soup, "article:modified_time")
        result.author = (
            self._get_meta(soup, "article:author")
            or self._get_meta(soup, "author", "name")
            or self._get_meta(soup, "dable:author", "name")
        )
        result.section = self._get_meta(soup, "article:section") or self._get_meta(
            soup, "article:tag"
        )

        # 키워드
        keywords_str = self._get_meta(soup, "keywords", "name") or self._get_meta(
            soup, "news_keywords", "name"
        )
        if keywords_str:
            result.keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

        # 언어
        html_tag = soup.find("html")
        if html_tag:
            result.language = html_tag.get("lang")

    def _extract_content(self, soup: BeautifulSoup, result: ScrapedArticle):
        """본문 추출."""
        content_elem = None

        # 셀렉터 순서대로 시도
        for selector in self.CONTENT_SELECTORS:
            content_elem = soup.select_one(selector)
            if content_elem and len(content_elem.get_text(strip=True)) > 100:
                break

        if content_elem:
            # HTML 저장
            result.content_html = str(content_elem)

            # 불필요한 요소 제거
            for tag in content_elem.select(
                "script, style, iframe, .ad, .advertisement, .social-share, .related-articles"
            ):
                tag.decompose()

            # 텍스트 추출
            text = content_elem.get_text(separator="\n", strip=True)
            # 과도한 공백 정리
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r" {2,}", " ", text)
            result.content = text.strip()

    def _extract_images(self, soup: BeautifulSoup, result: ScrapedArticle):
        """이미지 추출."""
        images = []
        seen_urls = set()

        # 메인 이미지 추가
        if result.main_image:
            images.append({"url": result.main_image, "caption": None, "is_main": True})
            seen_urls.add(result.main_image)

        # 본문 내 이미지 탐색
        img_selectors = [
            "article img",
            ".article-body img",
            ".article-content img",
            "#articleBody img",
            ".view_content img",
            ".news_body img",
        ]

        for selector in img_selectors:
            for img in soup.select(selector):
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if not src:
                    continue

                # 상대 URL 처리
                if not src.startswith(("http://", "https://")):
                    src = urljoin(result.final_url or result.source_url, src)

                # 중복 및 작은 이미지 필터링
                if src in seen_urls:
                    continue
                if any(
                    skip in src.lower()
                    for skip in ["icon", "logo", "button", "banner", "ad_", "pixel", "1x1"]
                ):
                    continue

                seen_urls.add(src)

                # 캡션 추출
                caption = None
                figcaption = img.find_parent("figure")
                if figcaption:
                    cap_elem = figcaption.find("figcaption")
                    if cap_elem:
                        caption = cap_elem.get_text(strip=True)

                if not caption:
                    caption = img.get("alt")

                images.append({"url": src, "caption": caption, "is_main": False})

        result.images = images

    def _get_meta(
        self, soup: BeautifulSoup, name: str, attr: str = "property"
    ) -> str | None:
        """메타 태그 값 추출."""
        tag = soup.find("meta", attrs={attr: name})
        if tag:
            return tag.get("content")
        return None

    def _get_title(self, soup: BeautifulSoup) -> str | None:
        """제목 추출."""
        for selector in self.TITLE_SELECTORS:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        # title 태그 폴백
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return None

    def _get_canonical(self, soup: BeautifulSoup) -> str | None:
        """Canonical URL 추출."""
        link = soup.find("link", rel="canonical")
        if link:
            return link.get("href")
        return None

    def close(self):
        """세션 종료."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def scrape_article(url: str) -> ScrapedArticle:
    """기사 스크래핑 편의 함수."""
    with ArticleScraper() as scraper:
        return scraper.scrape(url)
