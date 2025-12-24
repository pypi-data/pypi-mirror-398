"""timeline_formatter 모듈 테스트."""

import pytest
from bigkinds_mcp.visualization.timeline_formatter import (
    format_timeline_data,
    create_news_timeline,
    _parse_date,
)


class TestFormatTimelineData:
    """format_timeline_data 함수 테스트."""

    def test_empty_data(self):
        """빈 데이터 처리."""
        result = format_timeline_data([], format="timelinejs")
        assert result["events"] == []

    def test_timelinejs_format(self):
        """TimelineJS 포맷 변환."""
        events = [
            {"title": "AI 규제안 발표", "date": "2025-12-01", "content": "내용..."},
            {"title": "반도체 수출 호조", "date": "2025-12-05", "content": "내용2..."},
        ]
        result = format_timeline_data(events, format="timelinejs")

        assert len(result["events"]) == 2
        assert result["events"][0]["text"]["headline"] == "AI 규제안 발표"
        assert result["events"][0]["start_date"]["year"] == 2025
        assert result["events"][0]["start_date"]["month"] == 12
        assert result["events"][0]["start_date"]["day"] == 1

    def test_vis_timeline_format(self):
        """Vis.js Timeline 포맷 변환."""
        events = [
            {"title": "AI 규제안 발표", "date": "2025-12-01", "content": "내용..."},
        ]
        result = format_timeline_data(events, format="vis-timeline")

        assert len(result["items"]) == 1
        assert result["items"][0]["content"] == "AI 규제안 발표"
        assert "start" in result["items"][0]
        assert "options" in result

    def test_google_charts_format(self):
        """Google Charts Timeline 포맷 변환."""
        events = [
            {"title": "AI 규제안 발표", "date": "2025-12-01", "content": "내용..."},
        ]
        result = format_timeline_data(events, format="google-charts")

        assert len(result["cols"]) == 4  # Category, Title, Start, End
        assert len(result["rows"]) == 1

    def test_events_sorted_by_date(self):
        """이벤트 날짜순 정렬."""
        events = [
            {"title": "두 번째", "date": "2025-12-05", "content": "..."},
            {"title": "첫 번째", "date": "2025-12-01", "content": "..."},
        ]
        result = format_timeline_data(events, format="timelinejs")

        assert result["events"][0]["text"]["headline"] == "첫 번째"
        assert result["events"][1]["text"]["headline"] == "두 번째"

    def test_media_field(self):
        """미디어 필드 포함."""
        events = [
            {
                "title": "이벤트",
                "date": "2025-12-01",
                "content": "내용",
                "image": "https://example.com/image.jpg",
            },
        ]
        result = format_timeline_data(
            events, format="timelinejs", media_field="image"
        )

        assert "media" in result["events"][0]
        assert result["events"][0]["media"]["url"] == "https://example.com/image.jpg"

    def test_group_field(self):
        """그룹 필드 포함."""
        events = [
            {"title": "이벤트", "date": "2025-12-01", "content": "내용", "category": "경제"},
        ]
        result = format_timeline_data(
            events, format="vis-timeline", group_field="category"
        )

        assert result["items"][0]["group"] == "경제"
        assert len(result["groups"]) == 1
        assert result["groups"][0]["id"] == "경제"

    def test_invalid_format(self):
        """잘못된 포맷 에러."""
        with pytest.raises(ValueError, match="Unknown format"):
            format_timeline_data(
                [{"title": "이벤트", "date": "2025-12-01", "content": "내용"}],
                format="invalid",
            )


class TestParseDate:
    """날짜 파싱 테스트."""

    def test_iso_format(self):
        """ISO 형식 파싱."""
        dt = _parse_date("2025-12-01")
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 1

    def test_iso_datetime_format(self):
        """ISO 날짜시간 형식 파싱."""
        dt = _parse_date("2025-12-01T09:30:00")
        assert dt.hour == 9
        assert dt.minute == 30

    def test_slash_format(self):
        """슬래시 형식 파싱."""
        dt = _parse_date("2025/12/01")
        assert dt.year == 2025

    def test_dot_format(self):
        """점 형식 파싱."""
        dt = _parse_date("2025.12.01")
        assert dt.year == 2025

    def test_invalid_format_fallback(self):
        """잘못된 형식은 현재 시간 반환."""
        dt = _parse_date("not-a-date")
        # 현재 시간에 가까운 datetime 반환
        assert dt is not None


class TestCreateNewsTimeline:
    """BigKinds 뉴스 타임라인 생성 테스트."""

    def test_bigkinds_field_mapping(self):
        """BigKinds 필드 자동 매핑."""
        articles = [
            {
                "title": "AI 뉴스",
                "date": "2025-12-01",
                "summary": "AI 관련 뉴스 요약...",
                "thumbnail": "https://example.com/thumb.jpg",
                "provider": "경향신문",
            },
        ]
        result = create_news_timeline(articles, format="timelinejs")

        assert result["events"][0]["text"]["headline"] == "AI 뉴스"
        assert "AI 관련 뉴스" in result["events"][0]["text"]["text"]
        assert result["events"][0]["media"]["url"] == "https://example.com/thumb.jpg"
        assert result["events"][0]["group"] == "경향신문"
