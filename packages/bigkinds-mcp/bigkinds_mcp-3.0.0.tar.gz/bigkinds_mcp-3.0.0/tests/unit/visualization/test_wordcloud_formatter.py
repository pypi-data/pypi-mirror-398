"""wordcloud_formatter 모듈 테스트."""

import pytest
from bigkinds_mcp.visualization.wordcloud_formatter import (
    format_wordcloud_data,
    get_color_palette,
    _normalize_weights,
)


class TestFormatWordcloudData:
    """format_wordcloud_data 함수 테스트."""

    def test_empty_data(self):
        """빈 데이터 처리."""
        result = format_wordcloud_data([], format="d3cloud")
        assert result["words"] == []

    def test_d3cloud_format(self):
        """D3 Cloud 포맷 변환."""
        words = [
            {"word": "AI", "weight": 100},
            {"word": "반도체", "weight": 80},
        ]
        result = format_wordcloud_data(words, format="d3cloud")

        assert len(result["words"]) == 2
        assert result["words"][0]["text"] == "AI"
        assert "size" in result["words"][0]
        assert "config" in result

    def test_wordcloud2_format(self):
        """WordCloud2 포맷 변환."""
        words = [
            {"word": "AI", "weight": 100},
            {"word": "반도체", "weight": 80},
        ]
        result = format_wordcloud_data(words, format="wordcloud2")

        # WordCloud2는 [word, size] 2차원 배열
        assert len(result["list"]) == 2
        assert result["list"][0][0] == "AI"
        assert isinstance(result["list"][0][1], float)
        assert "options" in result

    def test_echarts_format(self):
        """ECharts 워드클라우드 포맷 변환."""
        words = [
            {"word": "AI", "weight": 100},
            {"word": "반도체", "weight": 80},
        ]
        result = format_wordcloud_data(words, format="echarts")

        assert result["series"][0]["type"] == "wordCloud"
        assert len(result["series"][0]["data"]) == 2
        assert result["series"][0]["data"][0]["name"] == "AI"
        assert result["series"][0]["data"][0]["value"] == 100

    def test_max_words_limit(self):
        """최대 단어 수 제한."""
        words = [{"word": f"word{i}", "weight": 100 - i} for i in range(150)]
        result = format_wordcloud_data(words, format="d3cloud", max_words=50)

        assert len(result["words"]) == 50

    def test_custom_fields(self):
        """커스텀 필드명 사용."""
        words = [{"term": "AI", "count": 100}]
        result = format_wordcloud_data(
            words, format="d3cloud", word_field="term", weight_field="count"
        )

        assert result["words"][0]["text"] == "AI"

    def test_invalid_format(self):
        """잘못된 포맷 에러."""
        with pytest.raises(ValueError, match="Unknown format"):
            format_wordcloud_data([{"word": "AI", "weight": 100}], format="invalid")


class TestNormalizeWeights:
    """가중치 정규화 테스트."""

    def test_linear_mode(self):
        """linear 모드 - 선형 스케일링."""
        words = [
            {"word": "AI", "weight": 100},
            {"word": "반도체", "weight": 50},
        ]
        result = _normalize_weights(words, "linear", 12, 80, "weight")

        # 최대값(100)은 80, 최소값(50)은 12
        assert result[0]["_size"] == 80
        assert result[1]["_size"] == 12  # min_size (ratio=0)

    def test_sqrt_mode(self):
        """sqrt 모드 - 제곱근 스케일링."""
        words = [
            {"word": "AI", "weight": 100},
            {"word": "반도체", "weight": 25},
        ]
        result = _normalize_weights(words, "sqrt", 12, 80, "weight")

        # sqrt로 변환 후 정규화
        assert result[0]["_size"] == 80
        assert result[1]["_size"] < 80  # sqrt(25)/sqrt(100) = 0.5

    def test_log_mode(self):
        """log 모드 - 로그 스케일링."""
        words = [
            {"word": "AI", "weight": 1000},
            {"word": "반도체", "weight": 10},
        ]
        result = _normalize_weights(words, "log", 12, 80, "weight")

        # log로 변환 후 정규화: log(1001)=6.9, log(11)=2.4
        # 최대값(1000)은 80, 최소값(10)은 12
        assert result[0]["_size"] == 80
        assert result[1]["_size"] == 12

    def test_single_value(self):
        """단일 값은 중간 크기."""
        words = [{"word": "AI", "weight": 100}]
        result = _normalize_weights(words, "linear", 12, 80, "weight")

        assert result[0]["_size"] == 46  # (12 + 80) / 2


class TestGetColorPalette:
    """색상 팔레트 테스트."""

    def test_default_palette(self):
        """기본 팔레트 반환."""
        colors = get_color_palette("default")
        assert len(colors) == 10
        assert all(c.startswith("#") for c in colors)

    def test_warm_palette(self):
        """따뜻한 색상 팔레트."""
        colors = get_color_palette("warm")
        assert len(colors) == 10

    def test_cool_palette(self):
        """시원한 색상 팔레트."""
        colors = get_color_palette("cool")
        assert len(colors) == 10

    def test_news_palette(self):
        """뉴스용 색상 팔레트."""
        colors = get_color_palette("news")
        assert len(colors) == 10

    def test_unknown_palette_fallback(self):
        """알 수 없는 팔레트는 기본값 반환."""
        colors = get_color_palette("unknown")
        assert colors == get_color_palette("default")
