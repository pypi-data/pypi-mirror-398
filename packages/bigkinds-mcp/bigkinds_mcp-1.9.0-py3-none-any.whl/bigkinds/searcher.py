"""BigKinds high-level search interface with pagination and aggregation."""

import time
from collections import defaultdict
from collections.abc import Generator
from datetime import datetime

import pandas as pd
import logging

from .client import BigKindsClient
from .models import NewsArticle, SearchRequest, SearchResponse, SearchStats

logger = logging.getLogger(__name__)


class BigKindsSearcher:
    """High-level interface for BigKinds news search with pagination support."""

    def __init__(
        self,
        client: BigKindsClient | None = None,
        batch_size: int = 10000,
        max_total: int = 1000000,
        show_progress: bool = True,
    ):
        """
        Initialize BigKinds searcher.

        Args:
            client: BigKinds HTTP client (creates default if None)
            batch_size: Number of articles per API request
            max_total: Maximum total articles to fetch
            show_progress: Whether to show progress output
        """
        self.client = client or BigKindsClient()
        self.batch_size = min(batch_size, 10000)  # API limit is 10k per request
        self.max_total = max_total
        self.show_progress = show_progress
        self._owns_client = client is None

    def search(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        providers: list[str] | None = None,
        categories: list[str] | None = None,
        print_results: bool = True,
    ) -> SearchResponse:
        """
        Search for articles with automatic pagination.

        Args:
            keyword: Search keyword
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            providers: Provider codes to filter by
            categories: Category codes to filter by
            print_results: Whether to print results to console

        Returns:
            SearchResponse with all collected articles
        """
        stats = SearchStats()
        all_articles = []

        # Get total count first
        logger.info(f"Searching BigKinds for '{keyword}' from {start_date} to {end_date}")
        total_count = self.client.get_total_count(keyword, start_date, end_date)

        if total_count == 0:
            logger.warning("No articles found for the specified criteria")
            return SearchResponse(
                success=True,
                total_count=0,
                keyword=keyword,
                date_range=f"{start_date} to {end_date}",
            )

        stats.total_articles = total_count
        articles_to_fetch = min(total_count, self.max_total)

        if self.show_progress:
            print(f"\n📰 BigKinds Search: '{keyword}'")
            print(f"Date Range: {start_date} to {end_date}")
            print(f"Total Available: {total_count:,} articles")
            print(f"Will Fetch: {articles_to_fetch:,} articles")
            print("=" * 60)

        # Paginated search
        page = 1
        fetched = 0

        while fetched < articles_to_fetch:
            current_batch = min(self.batch_size, articles_to_fetch - fetched)

            request = SearchRequest(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                start_no=page,
                result_number=current_batch,
                provider_codes=providers or [],
                category_codes=categories or [],
            )

            if self.show_progress:
                print(f"📄 Page {page}: Requesting {current_batch:,} articles...")

            response = self.client.search(request)
            stats.pages_fetched += 1

            if not response.success:
                logger.error(f"Search failed on page {page}: {response.error_message}")
                if self.show_progress:
                    print(f"❌ Page {page} failed: {response.error_message}")
                break

            if not response.articles:
                logger.info(f"No more articles available (page {page})")
                if self.show_progress:
                    print(f"✅ Page {page}: No more articles available")
                break

            # Add articles to collection
            all_articles.extend(response.articles)
            fetched_in_batch = len(response.articles)
            fetched += fetched_in_batch
            stats.articles_fetched = fetched

            if self.show_progress:
                print(
                    f"✅ Page {page}: {fetched_in_batch:,} articles (Total: {fetched:,}/{articles_to_fetch:,})"
                )

            # Update stats
            self._update_stats(stats, response.articles)

            # Check if we got fewer articles than requested (end of results)
            if fetched_in_batch < current_batch:
                if self.show_progress:
                    print("📝 Reached end of available articles")
                break

            page += 1

            # Small delay to be respectful to API
            time.sleep(0.1)

        stats.end_time = datetime.now()

        # Create final response
        final_response = SearchResponse(
            success=True,
            total_count=total_count,
            articles=all_articles,
            keyword=keyword,
            date_range=f"{start_date} to {end_date}",
        )

        if self.show_progress:
            print("=" * 60)
            print(f"🎯 Search Complete! Fetched {len(all_articles):,}/{total_count:,} articles")
            print(f"⏱️  Duration: {stats.duration_seconds:.1f} seconds")
            print(f"📊 Collection Rate: {stats.collection_rate:.1f}%")

        if print_results:
            final_response.print_summary()
            stats.print_stats()

        return final_response

    def search_bulk(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        providers: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> Generator[SearchResponse, None, None]:
        """
        Search with bulk processing - yields responses page by page.

        Args:
            keyword: Search keyword
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            providers: Provider codes to filter by
            categories: Category codes to filter by

        Yields:
            SearchResponse for each page
        """
        total_count = self.client.get_total_count(keyword, start_date, end_date)

        if total_count == 0:
            return

        articles_to_fetch = min(total_count, self.max_total)
        page = 1
        fetched = 0

        logger.info(f"Starting bulk search: {articles_to_fetch:,} articles to fetch")

        while fetched < articles_to_fetch:
            current_batch = min(self.batch_size, articles_to_fetch - fetched)

            request = SearchRequest(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                start_no=page,
                result_number=current_batch,
                provider_codes=providers or [],
                category_codes=categories or [],
            )

            response = self.client.search(request)

            if not response.success or not response.articles:
                break

            fetched += len(response.articles)
            page += 1

            yield response

    def get_daily_counts(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        providers: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Get daily article counts for date range.

        Args:
            keyword: Search keyword
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            providers: Provider codes to filter by
            categories: Category codes to filter by

        Returns:
            DataFrame with daily article counts
        """
        logger.info(f"Aggregating daily counts for '{keyword}' from {start_date} to {end_date}")

        daily_counts = defaultdict(int)
        provider_counts = defaultdict(lambda: defaultdict(int))

        # Use bulk search to process all articles
        for response in self.search_bulk(keyword, start_date, end_date, providers, categories):
            for article in response.articles:
                # Extract date from article
                date_str = self._extract_date(article)
                if date_str:
                    daily_counts[date_str] += 1
                    if article.publisher:
                        provider_counts[date_str][article.publisher] += 1

        # Convert to DataFrame
        results = []
        for date_str in sorted(daily_counts.keys()):
            results.append(
                {
                    "date": date_str,
                    "keyword": keyword,
                    "article_count": daily_counts[date_str],
                    "top_provider": max(provider_counts[date_str].items(), key=lambda x: x[1])[0]
                    if provider_counts[date_str]
                    else None,
                    "provider_count": len(provider_counts[date_str]),
                }
            )

        return pd.DataFrame(results)

    def _extract_date(self, article: NewsArticle) -> str | None:
        """Extract date string from article in YYYY-MM-DD format."""
        if not article.news_date:
            return None

        try:
            # Handle different date formats
            date_str = article.news_date

            if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            elif len(date_str) >= 10:  # YYYY-MM-DD or longer
                return date_str[:10]

        except Exception as e:
            logger.debug(f"Failed to parse date '{article.news_date}': {e}")

        return None

    def _update_stats(self, stats: SearchStats, articles: list[NewsArticle]):
        """Update search statistics with articles."""
        for article in articles:
            # Update provider stats
            if article.publisher:
                stats.provider_stats[article.publisher] = (
                    stats.provider_stats.get(article.publisher, 0) + 1
                )

            # Update category stats
            if article.category:
                stats.category_stats[article.category] = (
                    stats.category_stats.get(article.category, 0) + 1
                )

            # Update daily counts
            date_str = self._extract_date(article)
            if date_str:
                stats.daily_counts[date_str] = stats.daily_counts.get(date_str, 0) + 1

    def close(self):
        """Close the searcher and underlying client."""
        if self._owns_client and self.client:
            self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def search_bigkinds_news(
    keyword: str,
    start_date: str,
    end_date: str,
    max_articles: int = 10000,
    providers: list[str] | None = None,
    categories: list[str] | None = None,
    print_results: bool = True,
) -> SearchResponse:
    """
    Convenience function to search BigKinds news.

    Args:
        keyword: Search keyword
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_articles: Maximum articles to fetch
        providers: Provider codes to filter by
        categories: Category codes to filter by
        print_results: Whether to print results

    Returns:
        SearchResponse with articles
    """
    with BigKindsSearcher(max_total=max_articles) as searcher:
        return searcher.search(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            providers=providers,
            categories=categories,
            print_results=print_results,
        )
