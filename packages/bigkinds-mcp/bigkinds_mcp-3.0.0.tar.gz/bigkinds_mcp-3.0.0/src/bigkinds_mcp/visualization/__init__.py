"""BigKinds MCP 시각화 유틸리티 모듈.

뉴스 데이터를 다양한 차트 라이브러리 포맷으로 변환합니다.

지원 라이브러리:
- ECharts (Apache ECharts)
- Plotly
- Chart.js
- D3.js (워드클라우드)
- TimelineJS
- Vis.js Timeline
- Google Charts

Example:
    >>> from bigkinds_mcp.visualization import format_chart_data, format_wordcloud_data
    >>>
    >>> # 시계열 차트
    >>> data = [{"date": "2025-12-01", "count": 100}, {"date": "2025-12-02", "count": 150}]
    >>> chart = format_chart_data(data, format="echarts", chart_type="line")
    >>>
    >>> # 워드클라우드
    >>> words = [{"word": "AI", "weight": 100}, {"word": "반도체", "weight": 80}]
    >>> wordcloud = format_wordcloud_data(words, format="d3cloud")
"""

from bigkinds_mcp.visualization.chart_formatter import (
    format_chart_data,
    ChartType,
    ChartFormat as TimeSeriesChartFormat,
    FillStrategy,
)
from bigkinds_mcp.visualization.wordcloud_formatter import (
    format_wordcloud_data,
    get_color_palette,
    WeightMode,
    WordCloudFormat,
)
from bigkinds_mcp.visualization.timeline_formatter import (
    format_timeline_data,
    create_news_timeline,
    TimelineFormat,
    MediaType,
)
from bigkinds_mcp.visualization.comparison_formatter import (
    format_comparison_data,
    format_ranking_data,
    ComparisonMode,
    ChartFormat,
)
from bigkinds_mcp.visualization.heatmap_formatter import (
    format_heatmap_data,
    aggregate_by_time,
    create_publication_heatmap,
    NormalizationMode,
)

__all__ = [
    # Chart Formatter
    "format_chart_data",
    "ChartType",
    "TimeSeriesChartFormat",
    "FillStrategy",
    # WordCloud Formatter
    "format_wordcloud_data",
    "get_color_palette",
    "WeightMode",
    "WordCloudFormat",
    # Timeline Formatter
    "format_timeline_data",
    "create_news_timeline",
    "TimelineFormat",
    "MediaType",
    # Comparison Formatter
    "format_comparison_data",
    "format_ranking_data",
    "ComparisonMode",
    "ChartFormat",
    # Heatmap Formatter
    "format_heatmap_data",
    "aggregate_by_time",
    "create_publication_heatmap",
    "NormalizationMode",
]

__version__ = "3.0.0"
