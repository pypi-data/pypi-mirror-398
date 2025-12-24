"""Data models for BigKinds news API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NewsArticle(BaseModel):
    """Model for a single news article."""

    # Core article info
    news_id: str | None = Field(None, description="Article ID")
    title: str = Field(..., description="Article title")
    content: str | None = Field(None, description="Article content/summary")

    # Publication details
    publisher: str | None = Field(None, description="Publisher name")
    provider_code: str | None = Field(None, description="Provider code")
    category: str | None = Field(None, description="News category")
    category_code: str | None = Field(None, description="Category code")

    # Date/time
    news_date: str | None = Field(None, description="Publication date")

    # URL and source
    url: str | None = Field(None, description="Article URL")
    byline: str | None = Field(None, description="Author/reporter")

    # Analysis flags
    analysis_flag: str | None = Field(None, description="Analysis availability flag")
    is_analysis: bool | None = Field(None, description="Whether article is analyzed")

    # Raw data preservation
    raw_data: dict | None = Field(None, description="Original API response data")

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_api_response(cls, data: dict) -> "NewsArticle":
        """Create NewsArticle from API response data."""
        # Map common field variations to our model
        mapped = {
            "news_id": data.get("NEWS_ID") or data.get("newsId"),
            "title": data.get("TITLE") or data.get("title", ""),
            "content": data.get("CONTENT") or data.get("content") or data.get("SUMMARY"),
            "publisher": data.get("PROVIDER") or data.get("PUBLISHER") or data.get("publisher"),
            "provider_code": data.get("PROVIDER_CODE") or data.get("providerCode"),
            "category": data.get("CATEGORY") or data.get("category"),
            "category_code": data.get("CATEGORY_CODE") or data.get("categoryCode"),
            "news_date": data.get("NEWS_DATE") or data.get("DATE") or data.get("newsDate"),
            "url": data.get("PROVIDER_LINK_PAGE") or data.get("URL") or data.get("url"),
            "byline": data.get("BYLINE") or data.get("byline") or data.get("byLine"),
            "analysis_flag": data.get("ANALYSIS_FLAG") or data.get("analysisFlag"),
            "is_analysis": data.get("IS_ANALYSIS") or data.get("isAnalysis"),
            "raw_data": data,
        }
        return cls(**{k: v for k, v in mapped.items() if v is not None})

    def __str__(self) -> str:
        """String representation for console output."""
        date_str = (
            self.news_date[:10] if self.news_date and len(self.news_date) >= 10 else "Unknown"
        )
        publisher_str = self.publisher[:15] if self.publisher else "Unknown"
        title_str = self.title[:50] + "..." if len(self.title) > 50 else self.title
        return f"{date_str} | {publisher_str:15s} | {title_str}"


class SearchRequest(BaseModel):
    """Model for BigKinds API search request."""

    # Search parameters
    keyword: str = Field(..., description="Search keyword")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")

    # Pagination
    start_no: int = Field(1, description="Starting page number")
    result_number: int = Field(10000, description="Number of results per page")

    # Filtering
    provider_codes: list[str] = Field(default_factory=list, description="Provider codes filter")
    category_codes: list[str] = Field(default_factory=list, description="Category codes filter")

    # Search options
    search_scope_type: str = Field("1", description="Search scope type")
    search_filter_type: str = Field("1", description="Search filter type")
    sort_method: str = Field("date", description="Sort method")

    # Analysis options
    is_tm_usable: bool = Field(False, description="Text mining usable")
    is_not_tm_usable: bool = Field(False, description="Text mining not usable")
    editorial_is: bool = Field(False, description="Editorial filter")

    model_config = ConfigDict()

    def to_api_payload(self) -> dict[str, Any]:
        """Convert to BigKinds API payload format."""
        return {
            "indexName": "news",
            "searchKey": self.keyword,
            "searchKeys": [{}],
            "byLine": "",
            "searchFilterType": self.search_filter_type,
            "searchScopeType": self.search_scope_type,
            "searchSortType": "date",
            "sortMethod": self.sort_method,
            "mainTodayPersonYn": "",
            "startDate": self.start_date,
            "endDate": self.end_date,
            "newsIds": [],
            "categoryCodes": self.category_codes,
            "providerCodes": self.provider_codes,
            "incidentCodes": [],
            "networkNodeType": "",
            "topicOrigin": "",
            "dateCodes": [],
            "editorialIs": self.editorial_is,
            "startNo": self.start_no,
            "resultNumber": self.result_number,
            "isTmUsable": self.is_tm_usable,
            "isNotTmUsable": self.is_not_tm_usable,
        }


class SearchResponse(BaseModel):
    """Model for BigKinds API search response."""

    success: bool = Field(..., description="Request success status")
    total_count: int = Field(0, description="Total number of articles found")
    articles: list[NewsArticle] = Field(default_factory=list, description="List of articles")

    # Pagination info
    page_number: int = Field(1, description="Current page number")
    per_page: int = Field(10000, description="Results per page")

    # Request info
    keyword: str | None = Field(None, description="Search keyword")
    date_range: str | None = Field(None, description="Date range searched")
    search_time: datetime = Field(
        default_factory=datetime.now, description="When search was performed"
    )

    # Error info
    error_message: str | None = Field(None, description="Error message if failed")
    error_code: str | None = Field(None, description="Error code if failed")

    # Raw data
    raw_response: dict | None = Field(None, description="Original API response")

    model_config = ConfigDict()

    @classmethod
    def from_api_response(
        cls, data: dict, request: SearchRequest, raw_response: dict | None = None
    ) -> "SearchResponse":
        """Create SearchResponse from API response data."""
        articles = []
        if data.get("resultList"):
            articles = [
                NewsArticle.from_api_response(article_data) for article_data in data["resultList"]
            ]

        return cls(
            success=data.get("success", False),
            total_count=data.get("totalCount", 0),
            articles=articles,
            page_number=request.start_no,
            per_page=request.result_number,
            keyword=request.keyword,
            date_range=f"{request.start_date} to {request.end_date}",
            error_message=data.get("errorMessage"),
            error_code=data.get("errorCode"),
            raw_response=raw_response or data,
        )

    def print_summary(self, show_articles: int = 10):
        """Print summary to console."""
        print("\n" + "=" * 80)
        print(f"BigKinds News Search - {self.search_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Keyword: '{self.keyword}' | Date Range: {self.date_range}")
        print(
            f"Total Articles: {self.total_count:,} | Page: {self.page_number} ({len(self.articles)} shown)"
        )
        print("=" * 80)

        if self.success and self.articles:
            print(f"\nShowing {min(show_articles, len(self.articles))} articles:")
            print("-" * 80)
            for i, article in enumerate(self.articles[:show_articles], 1):
                print(f"{i:3d}. {article}")
        elif not self.success:
            print(f"\n❌ Search failed: {self.error_message}")
        else:
            print("\nNo articles found.")

        print("=" * 80 + "\n")


class SearchStats(BaseModel):
    """Statistics for search operations."""

    total_articles: int = Field(0, description="Total articles found")
    pages_fetched: int = Field(0, description="Number of pages fetched")
    articles_fetched: int = Field(0, description="Number of articles actually fetched")

    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = Field(None)

    # Provider/category breakdown
    provider_stats: dict[str, int] = Field(default_factory=dict)
    category_stats: dict[str, int] = Field(default_factory=dict)

    # Date range stats
    daily_counts: dict[str, int] = Field(default_factory=dict)

    model_config = ConfigDict()

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def collection_rate(self) -> float:
        """Calculate collection rate percentage."""
        if self.total_articles > 0:
            return (self.articles_fetched / self.total_articles) * 100
        return 0.0

    def print_stats(self):
        """Print statistics to console."""
        print("\n" + "=" * 60)
        print("BigKinds Search Statistics")
        print("=" * 60)
        print(f"Duration: {self.duration_seconds:.1f} seconds")
        print(f"Total Found: {self.total_articles:,} articles")
        print(f"Pages Fetched: {self.pages_fetched}")
        print(f"Articles Collected: {self.articles_fetched:,}")
        print(f"Collection Rate: {self.collection_rate:.1f}%")

        if self.provider_stats:
            print("\nTop Providers:")
            for provider, count in sorted(
                self.provider_stats.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                print(f"  {provider}: {count:,} articles")

        if self.daily_counts:
            avg_daily = sum(self.daily_counts.values()) / len(self.daily_counts)
            max_day = max(self.daily_counts.items(), key=lambda x: x[1])
            print("\nDaily Stats:")
            print(f"  Average: {avg_daily:.1f} articles/day")
            print(f"  Peak: {max_day[1]:,} articles on {max_day[0]}")

        print("=" * 60 + "\n")
