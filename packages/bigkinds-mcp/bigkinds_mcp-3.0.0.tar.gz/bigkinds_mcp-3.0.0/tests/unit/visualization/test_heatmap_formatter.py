"""heatmap_formatter 모듈 테스트."""

import pytest
from bigkinds_mcp.visualization.heatmap_formatter import (
    format_heatmap_data,
    aggregate_by_time,
    create_publication_heatmap,
    _build_matrix,
    _normalize_matrix,
)


class TestFormatHeatmapData:
    """format_heatmap_data 함수 테스트."""

    def test_empty_data(self):
        """빈 데이터 처리."""
        result = format_heatmap_data([], format="echarts")
        assert result["series"][0]["data"] == []

    def test_echarts_format(self):
        """ECharts 히트맵 변환."""
        data = [
            {"hour": 9, "weekday": 0, "count": 100},
            {"hour": 10, "weekday": 0, "count": 150},
            {"hour": 9, "weekday": 1, "count": 80},
        ]
        result = format_heatmap_data(data, format="echarts")

        assert result["series"][0]["type"] == "heatmap"
        # 2x2 매트릭스 = 4셀 (빈 셀 포함)
        assert len(result["series"][0]["data"]) == 4
        assert "visualMap" in result

    def test_plotly_format(self):
        """Plotly 히트맵 변환."""
        data = [
            {"hour": 9, "weekday": 0, "count": 100},
            {"hour": 10, "weekday": 0, "count": 150},
        ]
        result = format_heatmap_data(data, format="plotly")

        assert result["data"][0]["type"] == "heatmap"
        assert "z" in result["data"][0]  # 2D 매트릭스

    def test_chartjs_format(self):
        """Chart.js Matrix 변환."""
        data = [
            {"hour": 9, "weekday": 0, "count": 100},
        ]
        result = format_heatmap_data(data, format="chartjs")

        assert result["type"] == "matrix"
        assert len(result["data"]["datasets"][0]["data"]) == 1

    def test_custom_fields(self):
        """커스텀 필드명 사용."""
        data = [{"time": 9, "day": 0, "value": 100}]
        result = format_heatmap_data(
            data,
            format="echarts",
            x_field="time",
            y_field="day",
            value_field="value",
        )

        assert result["series"][0]["data"][0][2] == 100

    def test_invalid_format(self):
        """잘못된 포맷 에러."""
        with pytest.raises(ValueError, match="Unknown format"):
            format_heatmap_data(
                [{"hour": 9, "weekday": 0, "count": 100}], format="invalid"
            )


class TestBuildMatrix:
    """2D 매트릭스 생성 테스트."""

    def test_basic_matrix(self):
        """기본 매트릭스 생성."""
        data = [
            {"hour": 0, "weekday": 0, "count": 100},
            {"hour": 1, "weekday": 0, "count": 150},
            {"hour": 0, "weekday": 1, "count": 80},
        ]
        x_labels = [0, 1]
        y_labels = [0, 1]

        matrix = _build_matrix(data, x_labels, y_labels, "hour", "weekday", "count")

        assert matrix[0][0] == 100  # weekday=0, hour=0
        assert matrix[0][1] == 150  # weekday=0, hour=1
        assert matrix[1][0] == 80   # weekday=1, hour=0
        assert matrix[1][1] == 0    # 데이터 없음

    def test_missing_data_filled_with_zero(self):
        """누락 데이터는 0으로 채움."""
        data = [{"hour": 0, "weekday": 0, "count": 100}]
        matrix = _build_matrix(data, [0, 1], [0, 1], "hour", "weekday", "count")

        assert matrix[0][1] == 0  # 없는 데이터


class TestNormalizeMatrix:
    """매트릭스 정규화 테스트."""

    def test_no_normalization(self):
        """none 모드 - 원본 반환."""
        matrix = [[100, 50], [75, 25]]
        result = _normalize_matrix(matrix, "none")

        assert result == matrix

    def test_global_normalization(self):
        """global 모드 - 전체 최대값 기준."""
        matrix = [[100, 50], [75, 25]]
        result = _normalize_matrix(matrix, "global")

        assert result[0][0] == 100.0  # 최대값
        assert result[0][1] == 50.0   # 50/100 * 100
        assert result[1][1] == 25.0   # 25/100 * 100

    def test_row_normalization(self):
        """row 모드 - 행별 최대값 기준."""
        matrix = [[100, 50], [40, 80]]
        result = _normalize_matrix(matrix, "row")

        # 첫 번째 행: max=100
        assert result[0][0] == 100.0
        assert result[0][1] == 50.0
        # 두 번째 행: max=80
        assert result[1][0] == 50.0   # 40/80 * 100
        assert result[1][1] == 100.0

    def test_column_normalization(self):
        """column 모드 - 열별 최대값 기준."""
        matrix = [[100, 40], [50, 80]]
        result = _normalize_matrix(matrix, "column")

        # 첫 번째 열: max=100
        assert result[0][0] == 100.0
        assert result[1][0] == 50.0
        # 두 번째 열: max=80
        assert result[0][1] == 50.0   # 40/80 * 100
        assert result[1][1] == 100.0


class TestAggregateByTime:
    """시간대별 집계 테스트."""

    def test_basic_aggregation(self):
        """기본 집계."""
        articles = [
            {"datetime": "2025-12-01T09:30:00"},
            {"datetime": "2025-12-01T09:45:00"},
            {"datetime": "2025-12-02T10:00:00"},
        ]
        result = aggregate_by_time(articles)

        # 월요일(0) 9시에 2건
        monday_9 = next((r for r in result if r["weekday"] == 0 and r["hour"] == 9), None)
        assert monday_9 is not None
        assert monday_9["count"] == 2

    def test_date_only_defaults_to_noon(self):
        """날짜만 있으면 정오로 설정."""
        articles = [{"date": "2025-12-01"}]
        result = aggregate_by_time(articles, datetime_field="date")

        assert result[0]["hour"] == 12

    def test_empty_articles(self):
        """빈 기사 목록."""
        result = aggregate_by_time([])
        assert result == []


class TestCreatePublicationHeatmap:
    """BigKinds 발행 시간대 히트맵 테스트."""

    def test_basic_heatmap(self):
        """기본 히트맵 생성."""
        articles = [
            {"datetime": "2025-12-01T09:30:00"},
            {"datetime": "2025-12-01T10:00:00"},
        ]
        result = create_publication_heatmap(articles, format="echarts")

        assert result["series"][0]["type"] == "heatmap"

    def test_with_normalization(self):
        """정규화 적용."""
        articles = [
            {"datetime": "2025-12-01T09:30:00"},
            {"datetime": "2025-12-01T09:45:00"},
        ]
        result = create_publication_heatmap(
            articles, format="echarts", normalization="global"
        )

        # 정규화 적용됨
        assert "visualMap" in result
