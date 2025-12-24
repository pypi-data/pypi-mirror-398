"""연관어 데이터를 워드클라우드 라이브러리 포맷으로 변환하는 모듈."""

from typing import Any, Literal

WeightMode = Literal["linear", "sqrt", "log"]
WordCloudFormat = Literal["d3cloud", "wordcloud2", "echarts"]


def format_wordcloud_data(
    words: list[dict[str, Any]],
    format: WordCloudFormat = "d3cloud",
    weight_mode: WeightMode = "sqrt",
    min_size: int = 12,
    max_size: int = 80,
    word_field: str = "word",
    weight_field: str = "weight",
    max_words: int = 100,
) -> dict[str, Any]:
    """
    연관어 데이터를 워드클라우드 라이브러리 포맷으로 변환.

    Args:
        words: 원본 데이터 [{word: "AI", weight: 100}, ...]
        format: 출력 포맷 (d3cloud, wordcloud2, echarts)
        weight_mode: 가중치 변환 (linear, sqrt, log)
        min_size: 최소 폰트 크기
        max_size: 최대 폰트 크기
        word_field: 단어 필드명
        weight_field: 가중치 필드명
        max_words: 최대 단어 수

    Returns:
        워드클라우드 라이브러리 호환 데이터 구조

    Example:
        >>> words = [{"word": "AI", "weight": 100}, {"word": "반도체", "weight": 80}]
        >>> result = format_wordcloud_data(words, format="d3cloud")
        >>> print(result["words"][0]["text"])
        'AI'
    """
    if not words:
        return _empty_response(format)

    # 1. 상위 N개 단어만 선택
    sorted_words = sorted(
        words, key=lambda x: x.get(weight_field, 0), reverse=True
    )[:max_words]

    # 2. 가중치 정규화
    normalized = _normalize_weights(
        sorted_words, weight_mode, min_size, max_size, weight_field
    )

    # 3. 포맷별 변환
    if format == "d3cloud":
        return _to_d3cloud(normalized, word_field)
    elif format == "wordcloud2":
        return _to_wordcloud2(normalized, word_field)
    elif format == "echarts":
        return _to_echarts(normalized, word_field)
    else:
        raise ValueError(f"Unknown format: {format}. Supported: d3cloud, wordcloud2, echarts")


def _empty_response(format: WordCloudFormat) -> dict[str, Any]:
    """빈 데이터에 대한 응답 생성."""
    if format == "d3cloud":
        return {"words": [], "config": {}}
    elif format == "wordcloud2":
        return {"list": [], "options": {}}
    elif format == "echarts":
        return {
            "series": [{"type": "wordCloud", "data": []}],
        }
    return {}


def _normalize_weights(
    words: list[dict],
    mode: WeightMode,
    min_size: int,
    max_size: int,
    weight_field: str,
) -> list[dict]:
    """가중치를 폰트 크기로 정규화."""
    import math

    if not words:
        return []

    # 가중치 추출
    weights = [w.get(weight_field, 0) for w in words]
    min_weight = min(weights)
    max_weight = max(weights)

    # 변환 함수
    def transform(value: float) -> float:
        if mode == "linear":
            return value
        elif mode == "sqrt":
            return math.sqrt(value) if value > 0 else 0
        elif mode == "log":
            return math.log(value + 1)
        return value

    # 변환된 값
    transformed = [transform(w) for w in weights]
    t_min = min(transformed)
    t_max = max(transformed)

    # 크기 범위 매핑
    result = []
    for i, word in enumerate(words):
        if t_max == t_min:
            size = (min_size + max_size) / 2
        else:
            ratio = (transformed[i] - t_min) / (t_max - t_min)
            size = min_size + ratio * (max_size - min_size)

        result.append({
            **word,
            "_size": round(size, 1),
            "_original_weight": weights[i],
        })

    return result


def _to_d3cloud(data: list[dict], word_field: str) -> dict[str, Any]:
    """D3 Cloud 포맷으로 변환.

    D3 Cloud (d3-cloud): https://github.com/jasondavies/d3-cloud
    """
    words = []
    for item in data:
        words.append({
            "text": item.get(word_field, ""),
            "size": item["_size"],
            "weight": item["_original_weight"],
        })

    return {
        "words": words,
        "config": {
            "fontFamily": "sans-serif",
            "rotations": [0, 90],
            "rotationProbability": 0.5,
            "spiral": "archimedean",
        },
    }


def _to_wordcloud2(data: list[dict], word_field: str) -> dict[str, Any]:
    """WordCloud2.js 포맷으로 변환.

    WordCloud2.js: https://github.com/timdream/wordcloud2.js
    """
    # WordCloud2는 [word, size] 형태의 2차원 배열 사용
    word_list = []
    for item in data:
        word_list.append([
            item.get(word_field, ""),
            item["_size"],
        ])

    return {
        "list": word_list,
        "options": {
            "fontFamily": "sans-serif",
            "color": "random-dark",
            "backgroundColor": "#ffffff",
            "rotateRatio": 0.3,
            "rotationSteps": 2,
            "shuffle": True,
        },
        "metadata": {
            "word_weights": {
                item.get(word_field, ""): item["_original_weight"]
                for item in data
            },
        },
    }


def _to_echarts(data: list[dict], word_field: str) -> dict[str, Any]:
    """ECharts WordCloud 포맷으로 변환.

    ECharts WordCloud: https://github.com/ecomfe/echarts-wordcloud
    """
    series_data = []
    for item in data:
        series_data.append({
            "name": item.get(word_field, ""),
            "value": item["_original_weight"],
            "textStyle": {
                "fontSize": item["_size"],
            },
        })

    return {
        "tooltip": {
            "show": True,
            "formatter": "{b}: {c}",
        },
        "series": [{
            "type": "wordCloud",
            "shape": "circle",
            "sizeRange": [12, 80],
            "rotationRange": [-45, 45],
            "rotationStep": 45,
            "gridSize": 8,
            "drawOutOfBound": False,
            "textStyle": {
                "fontFamily": "sans-serif",
                "fontWeight": "bold",
            },
            "emphasis": {
                "focus": "self",
                "textStyle": {
                    "shadowBlur": 10,
                    "shadowColor": "#333",
                },
            },
            "data": series_data,
        }],
    }


def get_color_palette(palette: str = "default") -> list[str]:
    """워드클라우드용 색상 팔레트 반환.

    Args:
        palette: 팔레트 이름 (default, warm, cool, monochrome, news)

    Returns:
        색상 코드 리스트
    """
    palettes = {
        "default": [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        ],
        "warm": [
            "#d73027", "#f46d43", "#fdae61", "#fee090", "#ffffbf",
            "#fc8d59", "#ef6548", "#d7301f", "#b30000", "#7f0000",
        ],
        "cool": [
            "#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8",
            "#5e4fa2", "#3288bd", "#66c2a5", "#abdda4", "#e6f598",
        ],
        "monochrome": [
            "#000000", "#1a1a1a", "#333333", "#4d4d4d", "#666666",
            "#808080", "#999999", "#b3b3b3", "#cccccc", "#e6e6e6",
        ],
        "news": [
            "#003366", "#0066cc", "#3399ff", "#66b3ff", "#99ccff",
            "#cc0000", "#ff3333", "#ff6666", "#ff9999", "#ffcccc",
        ],
    }
    return palettes.get(palette, palettes["default"])
