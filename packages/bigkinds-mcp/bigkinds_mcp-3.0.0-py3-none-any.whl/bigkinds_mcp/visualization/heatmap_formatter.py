"""요일-시간대별 히트맵 데이터를 차트 라이브러리 포맷으로 변환하는 모듈."""

from typing import Any, Literal
from collections import defaultdict
from datetime import datetime

NormalizationMode = Literal["none", "row", "column", "global"]
ChartFormat = Literal["echarts", "plotly", "chartjs"]


def format_heatmap_data(
    data: list[dict[str, Any]],
    format: ChartFormat = "echarts",
    x_field: str = "hour",
    y_field: str = "weekday",
    value_field: str = "count",
    normalization: NormalizationMode = "none",
) -> dict[str, Any]:
    """
    시간대/요일별 데이터를 히트맵 차트 포맷으로 변환.

    Args:
        data: 원본 데이터 [{hour: 9, weekday: 0, count: 100}, ...]
        format: 출력 포맷 (echarts, plotly, chartjs)
        x_field: X축 필드명 (기본: hour)
        y_field: Y축 필드명 (기본: weekday, 0=월요일)
        value_field: 값 필드명
        normalization: 정규화 방식
            - none: 원본 값
            - row: 행별 정규화 (요일별 최대값 기준)
            - column: 열별 정규화 (시간대별 최대값 기준)
            - global: 전체 최대값 기준 정규화

    Returns:
        히트맵 차트 라이브러리 호환 데이터 구조

    Example:
        >>> data = [
        ...     {"hour": 9, "weekday": 0, "count": 100},
        ...     {"hour": 10, "weekday": 0, "count": 150}
        ... ]
        >>> result = format_heatmap_data(data, format="echarts")
        >>> print(result["series"][0]["type"])
        'heatmap'
    """
    if not data:
        return _empty_response(format)

    # 1. X, Y 축 레이블 추출
    x_labels = sorted(set(item.get(x_field) for item in data if item.get(x_field) is not None))
    y_labels = sorted(set(item.get(y_field) for item in data if item.get(y_field) is not None))

    # 2. 2D 매트릭스 생성
    matrix = _build_matrix(data, x_labels, y_labels, x_field, y_field, value_field)

    # 3. 정규화 적용
    normalized_matrix = _normalize_matrix(matrix, normalization)

    # 4. 포맷별 변환
    if format == "echarts":
        return _to_echarts(normalized_matrix, x_labels, y_labels, x_field, y_field)
    elif format == "plotly":
        return _to_plotly(normalized_matrix, x_labels, y_labels, x_field, y_field)
    elif format == "chartjs":
        return _to_chartjs(normalized_matrix, x_labels, y_labels, x_field, y_field)
    else:
        raise ValueError(f"Unknown format: {format}. Supported: echarts, plotly, chartjs")


def _empty_response(format: ChartFormat) -> dict[str, Any]:
    """빈 데이터에 대한 응답 생성."""
    if format == "echarts":
        return {
            "xAxis": {"type": "category", "data": []},
            "yAxis": {"type": "category", "data": []},
            "series": [{"type": "heatmap", "data": []}],
        }
    elif format == "plotly":
        return {"data": [], "layout": {}}
    elif format == "chartjs":
        return {"type": "matrix", "data": {"datasets": []}, "options": {}}
    return {}


def _build_matrix(
    data: list[dict],
    x_labels: list,
    y_labels: list,
    x_field: str,
    y_field: str,
    value_field: str,
) -> list[list[float]]:
    """2D 매트릭스 구성."""
    # 빈 매트릭스 초기화 (y_labels x x_labels)
    matrix = [[0.0 for _ in x_labels] for _ in y_labels]

    # 인덱스 매핑
    x_idx = {v: i for i, v in enumerate(x_labels)}
    y_idx = {v: i for i, v in enumerate(y_labels)}

    # 데이터 채우기
    for item in data:
        x = item.get(x_field)
        y = item.get(y_field)
        value = item.get(value_field, 0)

        if x in x_idx and y in y_idx:
            matrix[y_idx[y]][x_idx[x]] = float(value) if value else 0.0

    return matrix


def _normalize_matrix(
    matrix: list[list[float]],
    mode: NormalizationMode,
) -> list[list[float]]:
    """매트릭스 정규화."""
    if not matrix or mode == "none":
        return matrix

    rows = len(matrix)
    cols = len(matrix[0]) if matrix else 0

    result = [[0.0 for _ in range(cols)] for _ in range(rows)]

    if mode == "global":
        max_val = max(max(row) for row in matrix) if matrix else 1
        if max_val == 0:
            max_val = 1
        for i in range(rows):
            for j in range(cols):
                result[i][j] = round(matrix[i][j] / max_val * 100, 1)

    elif mode == "row":
        for i in range(rows):
            max_val = max(matrix[i]) if matrix[i] else 1
            if max_val == 0:
                max_val = 1
            for j in range(cols):
                result[i][j] = round(matrix[i][j] / max_val * 100, 1)

    elif mode == "column":
        for j in range(cols):
            max_val = max(matrix[i][j] for i in range(rows)) if rows > 0 else 1
            if max_val == 0:
                max_val = 1
            for i in range(rows):
                result[i][j] = round(matrix[i][j] / max_val * 100, 1)

    return result


def _format_x_label(value: Any, field: str) -> str:
    """X축 레이블 포맷팅."""
    if field == "hour":
        return f"{value}시"
    return str(value)


def _format_y_label(value: Any, field: str) -> str:
    """Y축 레이블 포맷팅."""
    if field == "weekday":
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        try:
            return weekdays[int(value)]
        except (ValueError, IndexError):
            return str(value)
    return str(value)


def _to_echarts(
    matrix: list[list[float]],
    x_labels: list,
    y_labels: list,
    x_field: str,
    y_field: str,
) -> dict[str, Any]:
    """ECharts 히트맵 포맷으로 변환."""
    # ECharts 히트맵 데이터는 [x_idx, y_idx, value] 형태
    heatmap_data = []
    for y_idx, row in enumerate(matrix):
        for x_idx, value in enumerate(row):
            heatmap_data.append([x_idx, y_idx, value])

    # 최대값 계산 (visualMap용)
    max_val = max(max(row) for row in matrix) if matrix else 100

    return {
        "tooltip": {
            "position": "top",
            "formatter": "{c}",
        },
        "grid": {
            "height": "60%",
            "top": "10%",
        },
        "xAxis": {
            "type": "category",
            "data": [_format_x_label(v, x_field) for v in x_labels],
            "splitArea": {"show": True},
        },
        "yAxis": {
            "type": "category",
            "data": [_format_y_label(v, y_field) for v in y_labels],
            "splitArea": {"show": True},
        },
        "visualMap": {
            "min": 0,
            "max": max_val,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "5%",
            "inRange": {
                "color": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1",
                         "#6baed6", "#4292c6", "#2171b5", "#084594"],
            },
        },
        "series": [{
            "name": "기사 수",
            "type": "heatmap",
            "data": heatmap_data,
            "label": {
                "show": True,
                "fontSize": 10,
            },
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                },
            },
        }],
    }


def _to_plotly(
    matrix: list[list[float]],
    x_labels: list,
    y_labels: list,
    x_field: str,
    y_field: str,
) -> dict[str, Any]:
    """Plotly 히트맵 포맷으로 변환."""
    return {
        "data": [{
            "z": matrix,
            "x": [_format_x_label(v, x_field) for v in x_labels],
            "y": [_format_y_label(v, y_field) for v in y_labels],
            "type": "heatmap",
            "colorscale": "Blues",
            "hoverongaps": False,
            "showscale": True,
        }],
        "layout": {
            "xaxis": {"title": x_field, "side": "top"},
            "yaxis": {"title": y_field, "autorange": "reversed"},
            "annotations": _generate_annotations(matrix, x_labels, y_labels, x_field, y_field),
        },
    }


def _generate_annotations(
    matrix: list[list[float]],
    x_labels: list,
    y_labels: list,
    x_field: str,
    y_field: str,
) -> list[dict[str, Any]]:
    """Plotly 히트맵 셀 값 표시용 어노테이션 생성."""
    annotations = []
    for y_idx, row in enumerate(matrix):
        for x_idx, value in enumerate(row):
            annotations.append({
                "x": _format_x_label(x_labels[x_idx], x_field),
                "y": _format_y_label(y_labels[y_idx], y_field),
                "text": str(int(value)) if value == int(value) else str(round(value, 1)),
                "font": {"color": "white" if value > 50 else "black"},
                "showarrow": False,
            })
    return annotations


def _to_chartjs(
    matrix: list[list[float]],
    x_labels: list,
    y_labels: list,
    x_field: str,
    y_field: str,
) -> dict[str, Any]:
    """Chart.js Matrix 포맷으로 변환.

    Note: Chart.js 히트맵은 chartjs-chart-matrix 플러그인 필요
    https://www.chartjs.org/chartjs-chart-matrix/
    """
    # Chart.js Matrix 형식: {x, y, v}
    data_points = []
    for y_idx, row in enumerate(matrix):
        for x_idx, value in enumerate(row):
            data_points.append({
                "x": _format_x_label(x_labels[x_idx], x_field),
                "y": _format_y_label(y_labels[y_idx], y_field),
                "v": value,
            })

    max_val = max(max(row) for row in matrix) if matrix else 100

    return {
        "type": "matrix",
        "data": {
            "datasets": [{
                "label": "기사 수",
                "data": data_points,
                "backgroundColor": _get_chartjs_color_fn(),
                "borderWidth": 1,
                "borderColor": "#ffffff",
                "width": 30,
                "height": 30,
            }],
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {"display": False},
                "tooltip": {
                    "callbacks": {
                        "title": lambda ctx: "",
                        "label": lambda ctx: f"{ctx['raw']['v']}건",
                    },
                },
            },
            "scales": {
                "x": {
                    "type": "category",
                    "labels": [_format_x_label(v, x_field) for v in x_labels],
                    "offset": True,
                    "position": "top",
                },
                "y": {
                    "type": "category",
                    "labels": [_format_y_label(v, y_field) for v in y_labels],
                    "offset": True,
                },
            },
        },
        "_metadata": {
            "max_value": max_val,
            "color_scale": "blues",
        },
    }


def _get_chartjs_color_fn() -> str:
    """Chart.js 색상 함수 문자열 반환."""
    # JavaScript 함수로 변환될 문자열
    return """function(context) {
        const value = context.dataset.data[context.dataIndex].v;
        const max = 100;
        const alpha = Math.min(value / max, 1);
        return `rgba(66, 146, 198, ${0.1 + alpha * 0.9})`;
    }"""


def aggregate_by_time(
    articles: list[dict[str, Any]],
    date_field: str = "date",
    datetime_field: str = "datetime",
) -> list[dict[str, Any]]:
    """
    기사 목록을 요일-시간대별로 집계.

    Args:
        articles: 기사 목록 [{date: "2025-12-01", datetime: "2025-12-01T09:30:00", ...}, ...]
        date_field: 날짜 필드명
        datetime_field: 시간 필드명 (datetime 또는 시간 정보 포함)

    Returns:
        요일-시간대별 집계 [{weekday: 0, hour: 9, count: 100}, ...]
    """
    counts: dict[tuple[int, int], int] = defaultdict(int)

    for article in articles:
        dt_str = article.get(datetime_field) or article.get(date_field)
        if not dt_str:
            continue

        try:
            # 다양한 형식 파싱
            if "T" in dt_str:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
                dt = dt.replace(hour=12)  # 날짜만 있으면 정오로 설정

            weekday = dt.weekday()  # 0=월요일
            hour = dt.hour

            counts[(weekday, hour)] += 1
        except (ValueError, AttributeError):
            continue

    result = [
        {"weekday": weekday, "hour": hour, "count": count}
        for (weekday, hour), count in counts.items()
    ]

    return sorted(result, key=lambda x: (x["weekday"], x["hour"]))


def create_publication_heatmap(
    articles: list[dict[str, Any]],
    format: ChartFormat = "echarts",
    normalization: NormalizationMode = "none",
) -> dict[str, Any]:
    """
    BigKinds 기사 목록에서 발행 시간대 히트맵 생성.

    Args:
        articles: BigKinds 검색 결과 기사 목록
        format: 출력 포맷
        normalization: 정규화 방식

    Returns:
        히트맵 데이터
    """
    aggregated = aggregate_by_time(articles)
    return format_heatmap_data(
        data=aggregated,
        format=format,
        normalization=normalization,
    )
