"""시계열 데이터를 차트 라이브러리 포맷으로 변환하는 모듈."""

from datetime import datetime, timedelta
from typing import Any, Literal

ChartType = Literal["line", "bar", "area"]
ChartFormat = Literal["echarts", "plotly", "chartjs"]
FillStrategy = Literal["null", "zero", "interpolate"]


def format_chart_data(
    data: list[dict[str, Any]],
    chart_type: ChartType = "line",
    format: ChartFormat = "echarts",
    fill_missing: FillStrategy = "null",
    x_field: str = "date",
    y_field: str = "count",
) -> dict[str, Any]:
    """
    시계열 데이터를 차트 라이브러리 포맷으로 변환.

    Args:
        data: 원본 데이터 [{date: "2025-12-01", count: 100}, ...]
        chart_type: 차트 유형 (line, bar, area)
        format: 출력 포맷 (echarts, plotly, chartjs)
        fill_missing: 누락 날짜 처리 (null, zero, interpolate)
        x_field: X축 필드명
        y_field: Y축 필드명

    Returns:
        차트 라이브러리 호환 데이터 구조

    Example:
        >>> data = [{"date": "2025-12-01", "count": 100}, {"date": "2025-12-02", "count": 150}]
        >>> result = format_chart_data(data, chart_type="line", format="echarts")
        >>> print(result["series"][0]["type"])
        'line'
    """
    if not data:
        return _empty_response(format)

    # 1. 데이터 정렬
    sorted_data = sorted(data, key=lambda x: x.get(x_field, ""))

    # 2. 누락 날짜 채우기
    filled_data = _fill_missing_dates(sorted_data, fill_missing, x_field, y_field)

    # 3. 포맷별 변환
    if format == "echarts":
        return _to_echarts(filled_data, chart_type, x_field, y_field)
    elif format == "plotly":
        return _to_plotly(filled_data, chart_type, x_field, y_field)
    elif format == "chartjs":
        return _to_chartjs(filled_data, chart_type, x_field, y_field)
    else:
        raise ValueError(f"Unknown format: {format}. Supported: echarts, plotly, chartjs")


def _empty_response(format: ChartFormat) -> dict[str, Any]:
    """빈 데이터에 대한 응답 생성."""
    if format == "echarts":
        return {
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [{"type": "line", "data": []}],
        }
    elif format == "plotly":
        return {"data": [], "layout": {}}
    elif format == "chartjs":
        return {"type": "line", "data": {"labels": [], "datasets": []}, "options": {}}
    return {}


def _fill_missing_dates(
    data: list[dict],
    strategy: FillStrategy,
    x_field: str,
    y_field: str,
) -> list[dict]:
    """누락 날짜 채우기."""
    if not data or strategy == "null":
        return data

    # 날짜 파싱 시도
    try:
        dates = [datetime.strptime(d[x_field], "%Y-%m-%d") for d in data]
    except (ValueError, KeyError):
        # 날짜 형식이 아니면 원본 반환
        return data

    date_values = {d[x_field]: d[y_field] for d in data}

    start, end = min(dates), max(dates)
    current = start
    filled = []

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in date_values:
            filled.append({x_field: date_str, y_field: date_values[date_str]})
        else:
            value = 0 if strategy == "zero" else None
            filled.append({x_field: date_str, y_field: value})
        current += timedelta(days=1)

    # interpolate 전략은 후처리
    if strategy == "interpolate":
        filled = _interpolate_nulls(filled, y_field)

    return filled


def _interpolate_nulls(data: list[dict], y_field: str) -> list[dict]:
    """None 값을 선형 보간으로 채우기."""
    if not data:
        return data

    result = [d.copy() for d in data]
    values = [d[y_field] for d in result]

    # 시작과 끝의 None을 가장 가까운 값으로 채우기
    first_valid = next((i for i, v in enumerate(values) if v is not None), None)
    last_valid = next((i for i, v in enumerate(reversed(values)) if v is not None), None)

    if first_valid is None:
        return result  # 모든 값이 None

    last_valid = len(values) - 1 - last_valid

    # 시작 부분 채우기
    for i in range(first_valid):
        result[i][y_field] = values[first_valid]

    # 끝 부분 채우기
    for i in range(last_valid + 1, len(values)):
        result[i][y_field] = values[last_valid]

    # 중간 None 보간
    i = first_valid
    while i < last_valid:
        if values[i] is None:
            # 다음 유효 값 찾기
            j = i + 1
            while j < len(values) and values[j] is None:
                j += 1

            if j < len(values) and values[j] is not None:
                # 선형 보간
                start_val = values[i - 1]
                end_val = values[j]
                step = (end_val - start_val) / (j - i + 1)

                for k in range(i, j):
                    result[k][y_field] = start_val + step * (k - i + 1)

            i = j
        else:
            i += 1

    return result


def _to_echarts(
    data: list[dict],
    chart_type: str,
    x_field: str,
    y_field: str,
) -> dict[str, Any]:
    """ECharts 포맷으로 변환."""
    series_type = "line" if chart_type == "area" else chart_type

    series_config: dict[str, Any] = {
        "type": series_type,
        "data": [d[y_field] for d in data],
    }

    if chart_type == "line":
        series_config["smooth"] = True
    elif chart_type == "area":
        series_config["areaStyle"] = {}
        series_config["smooth"] = True

    return {
        "xAxis": {
            "type": "category",
            "data": [d[x_field] for d in data],
        },
        "yAxis": {"type": "value"},
        "series": [series_config],
        "tooltip": {"trigger": "axis"},
    }


def _to_plotly(
    data: list[dict],
    chart_type: str,
    x_field: str,
    y_field: str,
) -> dict[str, Any]:
    """Plotly 포맷으로 변환."""
    x_values = [d[x_field] for d in data]
    y_values = [d[y_field] for d in data]

    if chart_type == "line":
        trace = {
            "x": x_values,
            "y": y_values,
            "type": "scatter",
            "mode": "lines+markers",
            "line": {"shape": "spline"},
        }
    elif chart_type == "bar":
        trace = {
            "x": x_values,
            "y": y_values,
            "type": "bar",
        }
    elif chart_type == "area":
        trace = {
            "x": x_values,
            "y": y_values,
            "type": "scatter",
            "mode": "lines",
            "fill": "tozeroy",
            "line": {"shape": "spline"},
        }
    else:
        trace = {"x": x_values, "y": y_values, "type": "scatter"}

    return {
        "data": [trace],
        "layout": {
            "xaxis": {"title": x_field},
            "yaxis": {"title": y_field},
            "hovermode": "x unified",
        },
    }


def _to_chartjs(
    data: list[dict],
    chart_type: str,
    x_field: str,
    y_field: str,
) -> dict[str, Any]:
    """Chart.js 포맷으로 변환."""
    chartjs_type = "line" if chart_type in ("line", "area") else chart_type

    dataset: dict[str, Any] = {
        "data": [d[y_field] for d in data],
        "borderColor": "rgb(75, 192, 192)",
        "backgroundColor": "rgba(75, 192, 192, 0.2)",
        "tension": 0.4,  # smooth curve
    }

    if chart_type == "area":
        dataset["fill"] = True

    return {
        "type": chartjs_type,
        "data": {
            "labels": [d[x_field] for d in data],
            "datasets": [dataset],
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {"display": False},
            },
            "scales": {
                "x": {"display": True},
                "y": {"display": True, "beginAtZero": True},
            },
        },
    }
