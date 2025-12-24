"""chart_formatter 모듈 테스트."""

import pytest
from bigkinds_mcp.visualization.chart_formatter import (
    format_chart_data,
    _fill_missing_dates,
    _interpolate_nulls,
)


class TestFormatChartData:
    """format_chart_data 함수 테스트."""

    def test_empty_data(self):
        """빈 데이터 처리."""
        result = format_chart_data([], format="echarts")
        assert result["series"][0]["data"] == []

    def test_echarts_line_chart(self):
        """ECharts 라인 차트 변환."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-02", "count": 150},
        ]
        result = format_chart_data(data, format="echarts", chart_type="line")

        assert result["xAxis"]["data"] == ["2025-12-01", "2025-12-02"]
        assert result["series"][0]["data"] == [100, 150]
        assert result["series"][0]["type"] == "line"
        assert result["series"][0]["smooth"] is True

    def test_echarts_bar_chart(self):
        """ECharts 바 차트 변환."""
        data = [{"date": "2025-12-01", "count": 100}]
        result = format_chart_data(data, format="echarts", chart_type="bar")

        assert result["series"][0]["type"] == "bar"

    def test_echarts_area_chart(self):
        """ECharts 영역 차트 변환."""
        data = [{"date": "2025-12-01", "count": 100}]
        result = format_chart_data(data, format="echarts", chart_type="area")

        # area는 line 타입에 areaStyle 추가
        assert result["series"][0]["type"] == "line"
        assert "areaStyle" in result["series"][0]

    def test_plotly_line_chart(self):
        """Plotly 라인 차트 변환."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-02", "count": 150},
        ]
        result = format_chart_data(data, format="plotly", chart_type="line")

        assert result["data"][0]["x"] == ["2025-12-01", "2025-12-02"]
        assert result["data"][0]["y"] == [100, 150]
        assert result["data"][0]["type"] == "scatter"
        assert result["data"][0]["mode"] == "lines+markers"

    def test_plotly_bar_chart(self):
        """Plotly 바 차트 변환."""
        data = [{"date": "2025-12-01", "count": 100}]
        result = format_chart_data(data, format="plotly", chart_type="bar")

        assert result["data"][0]["type"] == "bar"

    def test_chartjs_line_chart(self):
        """Chart.js 라인 차트 변환."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-02", "count": 150},
        ]
        result = format_chart_data(data, format="chartjs", chart_type="line")

        assert result["type"] == "line"
        assert result["data"]["labels"] == ["2025-12-01", "2025-12-02"]
        assert result["data"]["datasets"][0]["data"] == [100, 150]

    def test_data_sorted_by_date(self):
        """데이터 날짜순 정렬 확인."""
        data = [
            {"date": "2025-12-02", "count": 150},
            {"date": "2025-12-01", "count": 100},
        ]
        result = format_chart_data(data, format="echarts")

        assert result["xAxis"]["data"] == ["2025-12-01", "2025-12-02"]
        assert result["series"][0]["data"] == [100, 150]

    def test_custom_fields(self):
        """커스텀 필드명 사용."""
        data = [{"time": "2025-12-01", "value": 100}]
        result = format_chart_data(
            data, format="echarts", x_field="time", y_field="value"
        )

        assert result["xAxis"]["data"] == ["2025-12-01"]
        assert result["series"][0]["data"] == [100]

    def test_invalid_format(self):
        """잘못된 포맷 에러."""
        with pytest.raises(ValueError, match="Unknown format"):
            format_chart_data([{"date": "2025-12-01", "count": 100}], format="invalid")


class TestFillMissingDates:
    """누락 날짜 채우기 테스트."""

    def test_null_strategy(self):
        """null 전략 - 원본 반환."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-03", "count": 150},
        ]
        result = _fill_missing_dates(data, "null", "date", "count")

        assert len(result) == 2  # 원본 그대로

    def test_zero_strategy(self):
        """zero 전략 - 누락 날짜 0으로 채우기."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-03", "count": 150},
        ]
        result = _fill_missing_dates(data, "zero", "date", "count")

        assert len(result) == 3
        assert result[1]["date"] == "2025-12-02"
        assert result[1]["count"] == 0

    def test_interpolate_strategy(self):
        """interpolate 전략 - 선형 보간."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-03", "count": 200},
        ]
        result = _fill_missing_dates(data, "interpolate", "date", "count")

        assert len(result) == 3
        assert result[1]["date"] == "2025-12-02"
        # 100과 200 사이 보간
        assert result[1]["count"] == 150

    def test_non_date_format(self):
        """날짜 형식이 아닌 경우 원본 반환."""
        data = [{"date": "not-a-date", "count": 100}]
        result = _fill_missing_dates(data, "zero", "date", "count")

        assert result == data


class TestInterpolateNulls:
    """None 값 보간 테스트."""

    def test_middle_interpolation(self):
        """중간 None 값 보간."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-02", "count": None},
            {"date": "2025-12-03", "count": 200},
        ]
        result = _interpolate_nulls(data, "count")

        assert result[1]["count"] == 150

    def test_start_fill(self):
        """시작 부분 None 채우기."""
        data = [
            {"date": "2025-12-01", "count": None},
            {"date": "2025-12-02", "count": 100},
        ]
        result = _interpolate_nulls(data, "count")

        assert result[0]["count"] == 100  # 첫 유효값으로 채움

    def test_end_fill(self):
        """끝 부분 None 채우기."""
        data = [
            {"date": "2025-12-01", "count": 100},
            {"date": "2025-12-02", "count": None},
        ]
        result = _interpolate_nulls(data, "count")

        assert result[1]["count"] == 100  # 마지막 유효값으로 채움

    def test_all_none(self):
        """모든 값이 None인 경우."""
        data = [
            {"date": "2025-12-01", "count": None},
            {"date": "2025-12-02", "count": None},
        ]
        result = _interpolate_nulls(data, "count")

        assert result[0]["count"] is None
        assert result[1]["count"] is None

    def test_empty_data(self):
        """빈 데이터."""
        result = _interpolate_nulls([], "count")
        assert result == []
