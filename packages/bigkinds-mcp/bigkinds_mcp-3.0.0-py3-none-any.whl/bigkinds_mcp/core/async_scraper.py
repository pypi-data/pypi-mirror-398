"""기존 ArticleScraper의 비동기 래퍼."""

import asyncio
from functools import partial
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bigkinds.article_scraper import ScrapedArticle


class AsyncArticleScraper:
    """ArticleScraper를 비동기로 래핑."""

    def __init__(self, **kwargs):
        # 지연 임포트로 순환 참조 방지
        from bigkinds.article_scraper import ArticleScraper

        self._scraper = ArticleScraper(**kwargs)

    async def scrape(self, url: str) -> "ScrapedArticle":
        """비동기 스크래핑."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self._scraper.scrape, url)
        )

    def close(self):
        """스크래퍼 종료."""
        self._scraper.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()
