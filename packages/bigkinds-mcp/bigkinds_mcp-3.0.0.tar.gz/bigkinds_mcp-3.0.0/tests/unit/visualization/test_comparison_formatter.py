"""comparison_formatter 모듈 테스트."""

import pytest
from bigkinds_mcp.visualization.comparison_formatter import (
    format_comparison_data,
    format_ranking_data,
    _transform_by_mode,
)


class TestFormatComparisonData:
    """format_comparison_data 함수 테스트."""

    def test_empty_data(self):
        """빈 데이터 처리."""
        result = format_comparison_data([], ["AI", "반도체"], format="echarts")
        assert result["series"] == []

    def test_empty_keywords(self):
        """빈 키워드 목록."""
        result = format_comparison_data(
            [{"date": "2025-12-01", "AI": 100}], [], format="echarts"
        )
        assert result["series"] == []

    def test_echarts_format(self):
        """ECharts 비교 차트 변환."""
        data = [
            {"date": "2025-12-01", "AI": 100, "반도체": 80},
            {"date": "2025-12-02", "AI": 120, "반도체": 90},
        ]
        result = format_comparison_data(data, ["AI", "반도체"], format="echarts")

        assert len(result["series"]) == 2
        assert result["series"][0]["name"] == "AI"
        assert result["series"][0]["data"] == [100, 120]
        assert result["series"][1]["name"] == "반도체"
        assert result["legend"]["data"] == ["AI", "반도체"]

    def test_plotly_format(self):
        """Plotly 비교 차트 변환."""
        data = [
            {"date": "2025-12-01", "AI": 100, "반도체": 80},
        ]
        result = format_comparison_data(data, ["AI", "반도체"], format="plotly")

        assert len(result["data"]) == 2
        assert result["data"][0]["name"] == "AI"
        assert result["data"][0]["y"] == [100]

    def test_chartjs_format(self):
        """Chart.js 비교 차트 변환."""
        data = [
            {"date": "2025-12-01", "AI": 100, "반도체": 80},
        ]
        result = format_comparison_data(data, ["AI", "반도체"], format="chartjs")

        assert result["type"] == "line"
        assert len(result["data"]["datasets"]) == 2
        assert result["data"]["datasets"][0]["label"] == "AI"

    def test_stacked_chart(self):
        """스택 차트."""
        data = [{"date": "2025-12-01", "AI": 100, "반도체": 80}]
        result = format_comparison_data(
            data, ["AI", "반도체"], format="echarts", stacked=True
        )

        assert result["series"][0]["stack"] == "total"
        assert "areaStyle" in result["series"][0]

    def test_legend_hidden(self):
        """범례 숨김."""
        data = [{"date": "2025-12-01", "AI": 100}]
        result = format_comparison_data(
            data, ["AI"], format="echarts", show_legend=False
        )

        assert result["legend"]["show"] is False

    def test_invalid_format(self):
        """잘못된 포맷 에러."""
        with pytest.raises(ValueError, match="Unknown format"):
            format_comparison_data(
                [{"date": "2025-12-01", "AI": 100}], ["AI"], format="invalid"
            )


class TestTransformByMode:
    """값 변환 모드 테스트."""

    def test_absolute_mode(self):
        """absolute 모드 - 원본 값."""
        data = [
            {"date": "2025-12-01", "AI": 100, "반도체": 80},
            {"date": "2025-12-02", "AI": 150, "반도체": 100},
        ]
        result = _transform_by_mode(data, ["AI", "반도체"], "absolute")

        assert result == data

    def test_relative_mode(self):
        """relative 모드 - 첫 번째 값 대비 백분율."""
        data = [
            {"date": "2025-12-01", "AI": 100, "반도체": 80},
            {"date": "2025-12-02", "AI": 150, "반도체": 100},
        ]
        result = _transform_by_mode(data, ["AI", "반도체"], "relative")

        # AI: 100 -> 100%, 150 -> 150%
        assert result[0]["AI"] == 100.0
        assert result[1]["AI"] == 150.0
        # 반도체: 80 -> 100%, 100 -> 125%
        assert result[0]["반도체"] == 100.0
        assert result[1]["반도체"] == 125.0

    def test_normalized_mode(self):
        """normalized 모드 - 0-100 스케일."""
        data = [
            {"date": "2025-12-01", "AI": 100, "반도체": 0},
            {"date": "2025-12-02", "AI": 200, "반도체": 100},
        ]
        result = _transform_by_mode(data, ["AI", "반도체"], "normalized")

        # AI: min=100, max=200 -> 100->0, 200->100
        assert result[0]["AI"] == 0.0
        assert result[1]["AI"] == 100.0
        # 반도체: min=0, max=100 -> 0->0, 100->100
        assert result[0]["반도체"] == 0.0
        assert result[1]["반도체"] == 100.0

    def test_relative_with_zero_base(self):
        """relative 모드에서 첫 값이 0인 경우."""
        data = [
            {"date": "2025-12-01", "AI": 0},
            {"date": "2025-12-02", "AI": 100},
        ]
        result = _transform_by_mode(data, ["AI"], "relative")

        # 0 나누기 방지 - 첫 번째 0이 아닌 값 사용
        assert result[1]["AI"] == 100.0


class TestFormatRankingData:
    """format_ranking_data 함수 테스트."""

    def test_echarts_horizontal_ranking(self):
        """ECharts 가로 순위 차트."""
        data = {"AI": 100, "반도체": 80, "전기차": 60}
        result = format_ranking_data(data, format="echarts", horizontal=True)

        # 가로 차트는 yAxis가 category
        assert result["yAxis"]["type"] == "category"
        assert result["xAxis"]["type"] == "value"
        # 역순 (높은 값이 위로)
        assert result["yAxis"]["data"][-1] == "AI"

    def test_echarts_vertical_ranking(self):
        """ECharts 세로 순위 차트."""
        data = {"AI": 100, "반도체": 80}
        result = format_ranking_data(data, format="echarts", horizontal=False)

        assert result["xAxis"]["type"] == "category"
        assert result["yAxis"]["type"] == "value"

    def test_plotly_ranking(self):
        """Plotly 순위 차트."""
        data = {"AI": 100, "반도체": 80}
        result = format_ranking_data(data, format="plotly", horizontal=True)

        assert result["data"][0]["orientation"] == "h"

    def test_chartjs_ranking(self):
        """Chart.js 순위 차트."""
        data = {"AI": 100, "반도체": 80}
        result = format_ranking_data(data, format="chartjs", horizontal=True)

        assert result["options"]["indexAxis"] == "y"

    def test_top_n_limit(self):
        """상위 N개 제한."""
        data = {f"kw{i}": 100 - i for i in range(20)}
        result = format_ranking_data(data, format="echarts", top_n=5)

        assert len(result["yAxis"]["data"]) == 5
