"""키워드 비교 데이터를 차트 라이브러리 포맷으로 변환하는 모듈."""

from typing import Any, Literal

ComparisonMode = Literal["absolute", "relative", "normalized"]
ChartFormat = Literal["echarts", "plotly", "chartjs"]


def format_comparison_data(
    data: list[dict[str, Any]],
    keywords: list[str],
    format: ChartFormat = "echarts",
    mode: ComparisonMode = "absolute",
    x_field: str = "date",
    show_legend: bool = True,
    stacked: bool = False,
) -> dict[str, Any]:
    """
    키워드 비교 데이터를 차트 라이브러리 포맷으로 변환.

    Args:
        data: 원본 데이터 [{date: "2025-12-01", AI: 100, 반도체: 80}, ...]
        keywords: 비교할 키워드 목록 ["AI", "반도체", ...]
        format: 출력 포맷 (echarts, plotly, chartjs)
        mode: 값 표시 모드
            - absolute: 원본 값 그대로
            - relative: 첫 번째 데이터 대비 상대값 (%)
            - normalized: 0-100 정규화
        x_field: X축 필드명
        show_legend: 범례 표시 여부
        stacked: 스택 차트 여부

    Returns:
        차트 라이브러리 호환 데이터 구조

    Example:
        >>> data = [
        ...     {"date": "2025-12-01", "AI": 100, "반도체": 80},
        ...     {"date": "2025-12-02", "AI": 120, "반도체": 90}
        ... ]
        >>> result = format_comparison_data(data, ["AI", "반도체"], format="echarts")
        >>> len(result["series"])
        2
    """
    if not data or not keywords:
        return _empty_response(format)

    # 1. 데이터 정렬
    sorted_data = sorted(data, key=lambda x: x.get(x_field, ""))

    # 2. 모드에 따른 값 변환
    transformed_data = _transform_by_mode(sorted_data, keywords, mode)

    # 3. 포맷별 변환
    if format == "echarts":
        return _to_echarts(transformed_data, keywords, x_field, show_legend, stacked, mode)
    elif format == "plotly":
        return _to_plotly(transformed_data, keywords, x_field, show_legend, stacked, mode)
    elif format == "chartjs":
        return _to_chartjs(transformed_data, keywords, x_field, show_legend, stacked, mode)
    else:
        raise ValueError(f"Unknown format: {format}. Supported: echarts, plotly, chartjs")


def _empty_response(format: ChartFormat) -> dict[str, Any]:
    """빈 데이터에 대한 응답 생성."""
    if format == "echarts":
        return {
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "value"},
            "series": [],
            "legend": {"data": []},
        }
    elif format == "plotly":
        return {"data": [], "layout": {}}
    elif format == "chartjs":
        return {"type": "line", "data": {"labels": [], "datasets": []}, "options": {}}
    return {}


def _transform_by_mode(
    data: list[dict],
    keywords: list[str],
    mode: ComparisonMode,
) -> list[dict]:
    """모드에 따른 값 변환."""
    if mode == "absolute":
        return data

    result = []

    # relative: 첫 번째 값 대비 백분율
    if mode == "relative":
        base_values = {}
        for kw in keywords:
            for item in data:
                if item.get(kw) is not None and item[kw] > 0:
                    base_values[kw] = item[kw]
                    break
            if kw not in base_values:
                base_values[kw] = 1  # 0 나누기 방지

        for item in data:
            new_item = {k: v for k, v in item.items() if k not in keywords}
            for kw in keywords:
                value = item.get(kw)
                if value is not None:
                    new_item[kw] = round((value / base_values[kw]) * 100, 1)
                else:
                    new_item[kw] = None
            result.append(new_item)

    # normalized: 0-100 스케일
    elif mode == "normalized":
        min_vals = {}
        max_vals = {}

        for kw in keywords:
            values = [item.get(kw) for item in data if item.get(kw) is not None]
            if values:
                min_vals[kw] = min(values)
                max_vals[kw] = max(values)
            else:
                min_vals[kw] = 0
                max_vals[kw] = 1

        for item in data:
            new_item = {k: v for k, v in item.items() if k not in keywords}
            for kw in keywords:
                value = item.get(kw)
                if value is not None:
                    range_val = max_vals[kw] - min_vals[kw]
                    if range_val > 0:
                        new_item[kw] = round(
                            ((value - min_vals[kw]) / range_val) * 100, 1
                        )
                    else:
                        new_item[kw] = 50  # 모든 값이 같으면 중간값
                else:
                    new_item[kw] = None
            result.append(new_item)

    return result if result else data


def _get_color_palette() -> list[str]:
    """비교 차트용 색상 팔레트."""
    return [
        "#5470c6",  # 파랑
        "#91cc75",  # 초록
        "#fac858",  # 노랑
        "#ee6666",  # 빨강
        "#73c0de",  # 하늘
        "#3ba272",  # 진초록
        "#fc8452",  # 주황
        "#9a60b4",  # 보라
        "#ea7ccc",  # 분홍
        "#5470c6",  # 파랑 (반복)
    ]


def _to_echarts(
    data: list[dict],
    keywords: list[str],
    x_field: str,
    show_legend: bool,
    stacked: bool,
    mode: ComparisonMode,
) -> dict[str, Any]:
    """ECharts 포맷으로 변환."""
    colors = _get_color_palette()

    x_data = [item.get(x_field, "") for item in data]

    series = []
    for i, kw in enumerate(keywords):
        series_item: dict[str, Any] = {
            "name": kw,
            "type": "line",
            "data": [item.get(kw) for item in data],
            "smooth": True,
            "symbol": "circle",
            "symbolSize": 6,
        }

        if stacked:
            series_item["stack"] = "total"
            series_item["areaStyle"] = {"opacity": 0.3}

        series.append(series_item)

    y_axis_name = {
        "absolute": "기사 수",
        "relative": "상대값 (%)",
        "normalized": "정규화 (0-100)",
    }.get(mode, "")

    return {
        "color": colors[:len(keywords)],
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
        },
        "legend": {
            "data": keywords,
            "show": show_legend,
            "top": "top",
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True,
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": x_data,
        },
        "yAxis": {
            "type": "value",
            "name": y_axis_name,
        },
        "series": series,
    }


def _to_plotly(
    data: list[dict],
    keywords: list[str],
    x_field: str,
    show_legend: bool,
    stacked: bool,
    mode: ComparisonMode,
) -> dict[str, Any]:
    """Plotly 포맷으로 변환."""
    colors = _get_color_palette()
    x_values = [item.get(x_field, "") for item in data]

    traces = []
    for i, kw in enumerate(keywords):
        y_values = [item.get(kw) for item in data]

        trace: dict[str, Any] = {
            "x": x_values,
            "y": y_values,
            "name": kw,
            "type": "scatter",
            "mode": "lines+markers",
            "line": {"shape": "spline", "color": colors[i % len(colors)]},
            "marker": {"size": 6},
        }

        if stacked:
            trace["stackgroup"] = "one"
            trace["fill"] = "tonexty"

        traces.append(trace)

    y_axis_title = {
        "absolute": "기사 수",
        "relative": "상대값 (%)",
        "normalized": "정규화 (0-100)",
    }.get(mode, "")

    return {
        "data": traces,
        "layout": {
            "xaxis": {"title": x_field},
            "yaxis": {"title": y_axis_title},
            "hovermode": "x unified",
            "showlegend": show_legend,
            "legend": {"orientation": "h", "y": -0.15},
        },
    }


def _to_chartjs(
    data: list[dict],
    keywords: list[str],
    x_field: str,
    show_legend: bool,
    stacked: bool,
    mode: ComparisonMode,
) -> dict[str, Any]:
    """Chart.js 포맷으로 변환."""
    colors = _get_color_palette()
    labels = [item.get(x_field, "") for item in data]

    datasets = []
    for i, kw in enumerate(keywords):
        color = colors[i % len(colors)]

        dataset: dict[str, Any] = {
            "label": kw,
            "data": [item.get(kw) for item in data],
            "borderColor": color,
            "backgroundColor": f"{color}33",  # 20% 투명도
            "tension": 0.4,
            "fill": stacked,
        }

        datasets.append(dataset)

    y_axis_title = {
        "absolute": "기사 수",
        "relative": "상대값 (%)",
        "normalized": "정규화 (0-100)",
    }.get(mode, "")

    return {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "interaction": {
                "mode": "index",
                "intersect": False,
            },
            "plugins": {
                "legend": {
                    "display": show_legend,
                    "position": "top",
                },
                "title": {
                    "display": False,
                },
            },
            "scales": {
                "x": {
                    "display": True,
                    "stacked": stacked,
                },
                "y": {
                    "display": True,
                    "stacked": stacked,
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": y_axis_title,
                    },
                },
            },
        },
    }


def format_ranking_data(
    data: dict[str, int],
    format: ChartFormat = "echarts",
    top_n: int = 10,
    horizontal: bool = True,
) -> dict[str, Any]:
    """
    키워드별 총 기사 수를 순위 차트로 변환.

    Args:
        data: {키워드: 기사수} 딕셔너리
        format: 출력 포맷
        top_n: 상위 N개만 표시
        horizontal: 가로 막대 차트 여부

    Returns:
        순위 차트 데이터
    """
    # 정렬 및 상위 N개 선택
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:top_n]
    keywords = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    if horizontal:
        # 가로 차트는 역순으로 표시 (상위가 위로)
        keywords = keywords[::-1]
        values = values[::-1]

    if format == "echarts":
        axis_config = {
            "xAxis": {"type": "value"},
            "yAxis": {"type": "category", "data": keywords},
        } if horizontal else {
            "xAxis": {"type": "category", "data": keywords},
            "yAxis": {"type": "value"},
        }

        return {
            **axis_config,
            "series": [{
                "type": "bar",
                "data": values,
                "itemStyle": {"color": "#5470c6"},
                "label": {
                    "show": True,
                    "position": "right" if horizontal else "top",
                },
            }],
            "tooltip": {"trigger": "axis"},
        }

    elif format == "plotly":
        orientation = "h" if horizontal else "v"
        return {
            "data": [{
                "x": values if horizontal else keywords,
                "y": keywords if horizontal else values,
                "type": "bar",
                "orientation": orientation,
                "marker": {"color": "#5470c6"},
                "text": values,
                "textposition": "outside",
            }],
            "layout": {
                "xaxis": {"title": "기사 수" if horizontal else ""},
                "yaxis": {"title": "" if horizontal else "기사 수"},
            },
        }

    elif format == "chartjs":
        return {
            "type": "bar",
            "data": {
                "labels": keywords,
                "datasets": [{
                    "data": values,
                    "backgroundColor": "#5470c6",
                }],
            },
            "options": {
                "indexAxis": "y" if horizontal else "x",
                "plugins": {"legend": {"display": False}},
            },
        }

    return {}
