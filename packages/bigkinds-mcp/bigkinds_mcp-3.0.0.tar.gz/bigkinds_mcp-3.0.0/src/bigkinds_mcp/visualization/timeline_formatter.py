"""타임라인 이벤트 데이터를 TimelineJS 포맷으로 변환하는 모듈."""

from datetime import datetime
from typing import Any, Literal

TimelineFormat = Literal["timelinejs", "vis-timeline", "google-charts"]
MediaType = Literal["image", "video", "iframe", "none"]


def format_timeline_data(
    events: list[dict[str, Any]],
    format: TimelineFormat = "timelinejs",
    title_field: str = "title",
    date_field: str = "date",
    content_field: str = "content",
    media_field: str | None = None,
    group_field: str | None = None,
) -> dict[str, Any]:
    """
    이벤트 데이터를 타임라인 라이브러리 포맷으로 변환.

    Args:
        events: 원본 이벤트 데이터 [{title, date, content, ...}, ...]
        format: 출력 포맷 (timelinejs, vis-timeline, google-charts)
        title_field: 제목 필드명
        date_field: 날짜 필드명
        content_field: 본문 필드명
        media_field: 미디어 URL 필드명 (선택)
        group_field: 그룹/카테고리 필드명 (선택)

    Returns:
        타임라인 라이브러리 호환 데이터 구조

    Example:
        >>> events = [
        ...     {"title": "AI 규제안 발표", "date": "2025-12-01", "content": "..."},
        ...     {"title": "반도체 수출 호조", "date": "2025-12-05", "content": "..."}
        ... ]
        >>> result = format_timeline_data(events, format="timelinejs")
        >>> print(result["events"][0]["text"]["headline"])
        'AI 규제안 발표'
    """
    if not events:
        return _empty_response(format)

    # 날짜순 정렬
    sorted_events = sorted(
        events,
        key=lambda x: _parse_date(x.get(date_field, "")),
    )

    if format == "timelinejs":
        return _to_timelinejs(
            sorted_events, title_field, date_field, content_field, media_field, group_field
        )
    elif format == "vis-timeline":
        return _to_vis_timeline(
            sorted_events, title_field, date_field, content_field, group_field
        )
    elif format == "google-charts":
        return _to_google_charts(
            sorted_events, title_field, date_field, content_field
        )
    else:
        raise ValueError(
            f"Unknown format: {format}. Supported: timelinejs, vis-timeline, google-charts"
        )


def _empty_response(format: TimelineFormat) -> dict[str, Any]:
    """빈 데이터에 대한 응답 생성."""
    if format == "timelinejs":
        return {"events": [], "title": None}
    elif format == "vis-timeline":
        return {"items": [], "groups": []}
    elif format == "google-charts":
        return {"cols": [], "rows": []}
    return {}


def _parse_date(date_str: str) -> datetime:
    """날짜 문자열을 datetime으로 파싱."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y.%m.%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # 파싱 실패 시 현재 시간 반환
    return datetime.now()


def _to_timelinejs(
    events: list[dict],
    title_field: str,
    date_field: str,
    content_field: str,
    media_field: str | None,
    group_field: str | None,
) -> dict[str, Any]:
    """TimelineJS 포맷으로 변환.

    TimelineJS: https://timeline.knightlab.com/
    """
    timeline_events = []

    for i, event in enumerate(events):
        date = _parse_date(event.get(date_field, ""))

        tl_event: dict[str, Any] = {
            "start_date": {
                "year": date.year,
                "month": date.month,
                "day": date.day,
            },
            "text": {
                "headline": event.get(title_field, f"Event {i + 1}"),
                "text": event.get(content_field, ""),
            },
            "unique_id": f"event-{i}",
        }

        # 미디어 추가
        if media_field and event.get(media_field):
            media_url = event[media_field]
            tl_event["media"] = {
                "url": media_url,
                "caption": event.get(title_field, ""),
            }

        # 그룹 추가
        if group_field and event.get(group_field):
            tl_event["group"] = event[group_field]

        # 추가 메타데이터
        if "url" in event:
            tl_event["text"]["text"] += f'<br><a href="{event["url"]}" target="_blank">원문 보기</a>'

        if "provider" in event:
            tl_event["text"]["text"] += f'<br><small>{event["provider"]}</small>'

        timeline_events.append(tl_event)

    result: dict[str, Any] = {
        "events": timeline_events,
    }

    # 첫 번째 이벤트를 타이틀 슬라이드로 사용할 수 있음
    if timeline_events:
        first_event = timeline_events[0]
        result["title"] = {
            "text": {
                "headline": f"뉴스 타임라인 ({len(timeline_events)}건)",
                "text": f"{events[0].get(date_field, '')} ~ {events[-1].get(date_field, '')}",
            },
        }

    return result


def _to_vis_timeline(
    events: list[dict],
    title_field: str,
    date_field: str,
    content_field: str,
    group_field: str | None,
) -> dict[str, Any]:
    """Vis.js Timeline 포맷으로 변환.

    Vis.js Timeline: https://visjs.github.io/vis-timeline/
    """
    items = []
    groups_set: set[str] = set()

    for i, event in enumerate(events):
        date = _parse_date(event.get(date_field, ""))

        item: dict[str, Any] = {
            "id": i,
            "content": event.get(title_field, f"Event {i + 1}"),
            "start": date.isoformat(),
            "title": event.get(content_field, "")[:200],  # 툴팁용 요약
        }

        if group_field and event.get(group_field):
            group = event[group_field]
            item["group"] = group
            groups_set.add(group)

        # 추가 속성
        if "url" in event:
            item["url"] = event["url"]

        items.append(item)

    # 그룹 정의
    groups = [
        {"id": group, "content": group}
        for group in sorted(groups_set)
    ]

    return {
        "items": items,
        "groups": groups,
        "options": {
            "height": "400px",
            "stack": True,
            "showCurrentTime": False,
            "zoomable": True,
            "moveable": True,
            "orientation": {"axis": "top"},
        },
    }


def _to_google_charts(
    events: list[dict],
    title_field: str,
    date_field: str,
    content_field: str,
) -> dict[str, Any]:
    """Google Charts Timeline 포맷으로 변환.

    Google Charts Timeline: https://developers.google.com/chart/interactive/docs/gallery/timeline
    """
    cols = [
        {"type": "string", "label": "Category"},
        {"type": "string", "label": "Title"},
        {"type": "date", "label": "Start"},
        {"type": "date", "label": "End"},
    ]

    rows = []
    for event in events:
        date = _parse_date(event.get(date_field, ""))
        title = event.get(title_field, "")
        category = event.get("category", "뉴스")

        # Google Charts는 시작/종료가 필요 - 단일 이벤트는 같은 날로 설정
        row = {
            "c": [
                {"v": category},
                {"v": title},
                {"v": f"Date({date.year}, {date.month - 1}, {date.day})"},
                {"v": f"Date({date.year}, {date.month - 1}, {date.day})"},
            ]
        }
        rows.append(row)

    return {
        "cols": cols,
        "rows": rows,
        "options": {
            "timeline": {
                "showRowLabels": True,
                "groupByRowLabel": True,
            },
            "avoidOverlappingGridLines": False,
        },
    }


def create_news_timeline(
    articles: list[dict[str, Any]],
    format: TimelineFormat = "timelinejs",
) -> dict[str, Any]:
    """BigKinds 뉴스 기사를 타임라인으로 변환.

    BigKinds 검색 결과의 필드명에 맞춰 자동 매핑.

    Args:
        articles: BigKinds 검색 결과 기사 목록
        format: 출력 포맷

    Returns:
        타임라인 데이터
    """
    # BigKinds 필드 매핑
    return format_timeline_data(
        events=articles,
        format=format,
        title_field="title",
        date_field="date",
        content_field="summary",
        media_field="thumbnail",
        group_field="provider",
    )
