"""analyze_timeline 도구 테스트.

TDD 방식으로 먼저 테스트를 정의하고 구현합니다.
"""

import pytest
from datetime import datetime, timedelta

from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.async_scraper import AsyncArticleScraper
from bigkinds_mcp.core.cache import MCPCache
from bigkinds_mcp.tools import search, article, analysis


@pytest.fixture(scope="module")
def init_tools():
    """tools 초기화 fixture."""
    client = AsyncBigKindsClient()
    scraper = AsyncArticleScraper()
    cache = MCPCache()

    search.init_search_tools(client, cache)
    article.init_article_tools(client, scraper, cache)
    analysis.init_analysis_tools(client, cache)

    return client, cache


class TestAnalyzeTimelineInput:
    """입력 파라미터 검증 테스트."""

    def test_required_params(self):
        """필수 파라미터 확인."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        # keyword, start_date, end_date는 필수
        with pytest.raises(TypeError):
            analyze_timeline()

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, init_tools):
        """잘못된 날짜 형식."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        with pytest.raises(ValueError, match="날짜"):
            await analyze_timeline(
                keyword="테스트",
                start_date="2025/01/01",  # 잘못된 형식
                end_date="2025-12-20"
            )

    @pytest.mark.asyncio
    async def test_date_range_too_short(self, init_tools):
        """기간이 너무 짧은 경우 (최소 1개월)."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        with pytest.raises(ValueError, match="기간"):
            await analyze_timeline(
                keyword="테스트",
                start_date="2025-12-01",
                end_date="2025-12-10"  # 10일만
            )


class TestAnalyzeTimelineOutput:
    """출력 형식 테스트."""

    @pytest.mark.asyncio
    async def test_output_structure(self, init_tools):
        """출력 구조 확인."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        result = await analyze_timeline(
            keyword="AI",
            start_date="2024-01-01",
            end_date="2025-12-20",
            max_events=5
        )

        # 기본 구조
        assert "keyword" in result
        assert "period" in result
        assert "total_articles" in result
        assert "events" in result
        assert "timeline_summary" in result

        # period 구조
        assert "start_date" in result["period"]
        assert "end_date" in result["period"]
        assert "months" in result["period"]

    @pytest.mark.asyncio
    async def test_events_structure(self, init_tools):
        """이벤트 구조 확인."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        result = await analyze_timeline(
            keyword="AI",
            start_date="2024-01-01",
            end_date="2025-12-20",
            max_events=5
        )

        assert isinstance(result["events"], list)

        if result["events"]:  # 이벤트가 있으면
            event = result["events"][0]

            # 이벤트 필수 필드
            assert "period" in event  # "2024-03" 형식
            assert "article_count" in event
            assert "spike_ratio" in event  # 평균 대비 비율
            assert "top_keywords" in event  # 핵심 키워드 리스트
            assert "representative_articles" in event

            # 대표 기사 구조
            if event["representative_articles"]:
                article = event["representative_articles"][0]
                assert "title" in article
                assert "date" in article
                assert "url" in article
                assert "publisher" in article

    @pytest.mark.asyncio
    async def test_max_events_limit(self, init_tools):
        """max_events 제한 확인."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        result = await analyze_timeline(
            keyword="AI",
            start_date="2020-01-01",
            end_date="2025-12-20",
            max_events=3
        )

        assert len(result["events"]) <= 3


class TestEventDetection:
    """이벤트 탐지 로직 테스트 (단위 테스트)."""

    def test_detect_spikes_basic(self):
        """기본 스파이크 탐지."""
        from bigkinds_mcp.tools.timeline_utils import detect_spikes

        # 월별 기사 수 (급증 시점 포함)
        # 평균: (100+100+500+100+100+800+100)/7 = 257
        # 500/257 = 1.94, 800/257 = 3.11
        monthly_counts = {
            "2024-01": 100,
            "2024-02": 100,
            "2024-03": 500,  # 급증! (평균의 1.94배)
            "2024-04": 100,
            "2024-05": 100,
            "2024-06": 800,  # 급증! (평균의 3.11배)
            "2024-07": 100,
        }

        spikes = detect_spikes(monthly_counts, threshold=1.8)

        # 평균의 1.8배 이상인 월만 탐지
        assert "2024-03" in spikes
        assert "2024-06" in spikes
        assert "2024-01" not in spikes

    def test_detect_spikes_with_ratio(self):
        """스파이크 비율 계산."""
        from bigkinds_mcp.tools.timeline_utils import detect_spikes

        monthly_counts = {
            "2024-01": 100,
            "2024-02": 100,
            "2024-03": 300,
        }

        spikes = detect_spikes(monthly_counts, threshold=1.5)

        # 300 / (평균 166.67) ≈ 1.8배
        assert "2024-03" in spikes
        assert spikes["2024-03"]["ratio"] > 1.5

    def test_detect_spikes_empty(self):
        """빈 데이터 처리."""
        from bigkinds_mcp.tools.timeline_utils import detect_spikes

        spikes = detect_spikes({}, threshold=2.0)
        assert spikes == {}

    def test_detect_spikes_all_zero(self):
        """모든 값이 0인 경우."""
        from bigkinds_mcp.tools.timeline_utils import detect_spikes

        monthly_counts = {"2024-01": 0, "2024-02": 0, "2024-03": 0}
        spikes = detect_spikes(monthly_counts, threshold=2.0)
        assert spikes == {}


class TestKeywordExtraction:
    """키워드 추출 테스트 (단위 테스트)."""

    def test_extract_keywords_from_titles(self):
        """제목에서 키워드 추출."""
        from bigkinds_mcp.tools.timeline_utils import extract_keywords

        titles = [
            "한동훈 국민의힘 대표 취임",
            "한동훈 대표, 당 쇄신 선언",
            "국민의힘 한동훈 체제 출범",
            "한동훈, 윤석열 대통령과 회동",
        ]

        keywords = extract_keywords(titles, top_n=5)

        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        # "한동훈"은 모든 제목에 있으므로 상위에 있어야 함
        assert "한동훈" in keywords

    def test_extract_keywords_empty(self):
        """빈 제목 리스트."""
        from bigkinds_mcp.tools.timeline_utils import extract_keywords

        keywords = extract_keywords([], top_n=5)
        assert keywords == []

    def test_extract_keywords_with_exclude(self):
        """제외 단어 적용."""
        from bigkinds_mcp.tools.timeline_utils import extract_keywords

        titles = [
            "AI 기술의 발전",
            "AI 산업 성장",
            "인공지능 AI 혁신",
        ]

        # "AI"를 제외하고 추출
        keywords = extract_keywords(titles, top_n=5, exclude_words={"AI"})
        assert "AI" not in keywords


class TestRepresentativeArticleSelection:
    """대표 기사 선정 테스트 (단위 테스트)."""

    def test_select_representative_articles(self):
        """대표 기사 선정."""
        from bigkinds_mcp.tools.timeline_utils import select_representative_articles

        articles = [
            {"title": "A 사건 발생", "date": "2024-03-01", "publisher": "조선일보"},
            {"title": "A 사건 후속 보도", "date": "2024-03-02", "publisher": "중앙일보"},
            {"title": "A 사건 분석", "date": "2024-03-03", "publisher": "한겨레"},
            {"title": "A 사건 여파", "date": "2024-03-04", "publisher": "경향신문"},
            {"title": "A 사건 정리", "date": "2024-03-05", "publisher": "동아일보"},
        ]

        selected = select_representative_articles(articles, max_count=3)

        assert len(selected) == 3
        # 다양한 언론사에서 선택되어야 함 (다양성)

    def test_select_representative_articles_empty(self):
        """빈 기사 리스트."""
        from bigkinds_mcp.tools.timeline_utils import select_representative_articles

        selected = select_representative_articles([], max_count=3)
        assert selected == []

    def test_select_representative_articles_few(self):
        """기사 수가 max_count보다 적은 경우."""
        from bigkinds_mcp.tools.timeline_utils import select_representative_articles

        articles = [
            {"title": "A", "date": "2024-03-01", "publisher": "조선일보"},
            {"title": "B", "date": "2024-03-02", "publisher": "중앙일보"},
        ]

        selected = select_representative_articles(articles, max_count=5)
        assert len(selected) == 2  # 원본 그대로 반환


class TestTimelineSummary:
    """타임라인 요약 테스트 (단위 테스트)."""

    def test_generate_summary(self):
        """요약 생성."""
        from bigkinds_mcp.tools.timeline_utils import generate_timeline_summary

        events = [
            {
                "period": "2024-03",
                "article_count": 500,
                "spike_ratio": 2.5,
                "top_keywords": ["취임", "대표", "당대표"],
            },
            {
                "period": "2024-06",
                "article_count": 800,
                "spike_ratio": 4.0,
                "top_keywords": ["사퇴", "위기", "갈등"],
            },
        ]

        summary = generate_timeline_summary("한동훈", events)

        assert isinstance(summary, str)
        assert "한동훈" in summary
        assert "2024년 3월" in summary

    def test_generate_summary_empty(self):
        """빈 이벤트 리스트."""
        from bigkinds_mcp.tools.timeline_utils import generate_timeline_summary

        summary = generate_timeline_summary("테스트", [])
        assert "탐지되지 않았습니다" in summary


class TestParsePeriod:
    """기간 파싱 테스트 (단위 테스트)."""

    def test_parse_period_to_dates(self):
        """월 기간을 날짜로 변환."""
        from bigkinds_mcp.tools.timeline_utils import parse_period_to_dates

        start, end = parse_period_to_dates("2024-03")
        assert start == "2024-03-01"
        assert end == "2024-03-31"

    def test_parse_period_february(self):
        """2월 (윤년 아닌 해)."""
        from bigkinds_mcp.tools.timeline_utils import parse_period_to_dates

        start, end = parse_period_to_dates("2023-02")
        assert start == "2023-02-01"
        assert end == "2023-02-28"

    def test_parse_period_february_leap(self):
        """2월 (윤년)."""
        from bigkinds_mcp.tools.timeline_utils import parse_period_to_dates

        start, end = parse_period_to_dates("2024-02")
        assert start == "2024-02-01"
        assert end == "2024-02-29"


class TestIntegration:
    """통합 테스트 (실제 API 호출)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_timeline_analysis(self, init_tools):
        """전체 타임라인 분석 (실제 API)."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        result = await analyze_timeline(
            keyword="한동훈",
            start_date="2024-01-01",
            end_date="2025-12-20",
            max_events=10
        )

        # 기본 검증
        assert result["success"] is True
        assert result["total_articles"] > 0
        assert len(result["events"]) > 0

        # 이벤트가 시간순 정렬
        periods = [e["period"] for e in result["events"]]
        assert periods == sorted(periods)

        # 각 이벤트에 대표 기사 있음
        for event in result["events"]:
            assert len(event["representative_articles"]) > 0
            assert len(event["top_keywords"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timeline_with_few_results(self, init_tools):
        """결과가 적은 경우."""
        from bigkinds_mcp.tools.analysis import analyze_timeline

        result = await analyze_timeline(
            keyword="희귀한검색어xyz123",
            start_date="2024-01-01",
            end_date="2025-12-20",
            max_events=5
        )

        # 결과가 없어도 에러 없이 빈 이벤트 반환
        assert "events" in result
        assert result["total_articles"] == 0 or len(result["events"]) == 0
