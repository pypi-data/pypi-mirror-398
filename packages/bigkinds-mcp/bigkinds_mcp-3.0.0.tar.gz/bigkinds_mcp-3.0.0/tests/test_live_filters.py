"""실제 BigKinds API로 필터 기능 검증."""

import pytest
from bigkinds_mcp.tools.search import search_news
from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.cache import MCPCache


@pytest.fixture(scope="module")
async def init_tools():
    """tools 초기화."""
    from bigkinds_mcp.tools import search

    client = AsyncBigKindsClient()
    cache = MCPCache()
    search.init_search_tools(client, cache)
    yield
    await client.close()


@pytest.mark.asyncio
class TestCategoryFilterLive:
    """카테고리 필터 실제 API 검증."""

    async def test_category_filter_economy(self, init_tools):
        """경제 카테고리 필터 테스트."""
        result = await search_news(
            keyword="AI",
            start_date="2025-12-15",
            end_date="2025-12-15",
            categories=["경제"],
            page_size=10,
        )

        assert result.get("success", False), f"API 호출 실패: {result.get('message')}"
        assert result["total_count"] > 0, "경제 카테고리 필터가 0건 반환"

        # 실제로 경제 카테고리만 반환되었는지 검증
        articles = result.get("articles", [])
        if articles:
            print(f"\n경제 필터: {result['total_count']}건")
            for art in articles[:3]:
                print(f"  - [{art.get('category_code', 'N/A')}] {art.get('publisher')}: {art.get('title', '')[:50]}")

            # 002000000 (경제) 포함 여부 확인
            for art in articles:
                category_code = art.get("category_code", "")
                assert "002000000" in category_code, f"경제 필터 실패: {category_code}"

    async def test_category_filter_it(self, init_tools):
        """IT_과학 카테고리 필터 테스트."""
        result = await search_news(
            keyword="AI",
            start_date="2025-12-15",
            end_date="2025-12-15",
            categories=["IT_과학"],
            page_size=10,
        )

        assert result.get("success", False), f"API 호출 실패: {result.get('message')}"
        assert result["total_count"] > 0, "IT_과학 카테고리 필터가 0건 반환"

        articles = result.get("articles", [])
        if articles:
            print(f"\nIT_과학 필터: {result['total_count']}건")
            for art in articles[:3]:
                print(f"  - [{art.get('category_code', 'N/A')}] {art.get('publisher')}: {art.get('title', '')[:50]}")

            # 008000000 (IT_과학) 포함 여부 확인
            for art in articles:
                category_code = art.get("category_code", "")
                assert "008000000" in category_code, f"IT_과학 필터 실패: {category_code}"


@pytest.mark.asyncio
class TestProviderFilterLive:
    """언론사 필터 실제 API 검증."""

    async def test_provider_filter_kyunghyang(self, init_tools):
        """경향신문 언론사 필터 테스트."""
        result = await search_news(
            keyword="정치",
            start_date="2025-12-14",
            end_date="2025-12-15",
            providers=["경향신문"],
            page_size=10,
        )

        assert result.get("success", False), f"API 호출 실패: {result.get('message')}"
        assert result["total_count"] > 0, "경향신문 필터가 0건 반환"

        articles = result.get("articles", [])
        if articles:
            print(f"\n경향신문 필터: {result['total_count']}건")
            for art in articles[:5]:
                print(f"  - {art.get('publisher')}: {art.get('title', '')[:50]}")

            # 모든 기사가 경향신문인지 확인
            non_kyunghyang = [a for a in articles if a.get("publisher") != "경향신문"]
            assert len(non_kyunghyang) == 0, f"경향신문 필터 실패: {[a.get('publisher') for a in non_kyunghyang]}"

    async def test_provider_filter_hankyoreh(self, init_tools):
        """한겨레 언론사 필터 테스트."""
        result = await search_news(
            keyword="경제",
            start_date="2025-12-14",
            end_date="2025-12-15",
            providers=["한겨레"],
            page_size=10,
        )

        assert result.get("success", False), f"API 호출 실패: {result.get('message')}"
        assert result["total_count"] > 0, "한겨레 필터가 0건 반환"

        articles = result.get("articles", [])
        if articles:
            print(f"\n한겨레 필터: {result['total_count']}건")
            for art in articles[:5]:
                print(f"  - {art.get('publisher')}: {art.get('title', '')[:50]}")

            # 모든 기사가 한겨레인지 확인
            non_hankyoreh = [a for a in articles if a.get("publisher") != "한겨레"]
            assert len(non_hankyoreh) == 0, f"한겨레 필터 실패: {[a.get('publisher') for a in non_hankyoreh]}"

    async def test_provider_multiple(self, init_tools):
        """복수 언론사 필터 테스트."""
        result = await search_news(
            keyword="AI",
            start_date="2025-12-15",
            end_date="2025-12-15",
            providers=["경향신문", "한겨레"],
            page_size=20,
        )

        assert result.get("success", False), f"API 호출 실패: {result.get('message')}"
        assert result["total_count"] > 0, "복수 언론사 필터가 0건 반환"

        articles = result.get("articles", [])
        if articles:
            print(f"\n경향신문+한겨레 필터: {result['total_count']}건")

            # 언론사 집계
            publishers = {}
            for art in articles:
                pub = art.get("publisher", "Unknown")
                publishers[pub] = publishers.get(pub, 0) + 1

            print(f"언론사별 분포: {publishers}")

            # 모든 기사가 경향신문 또는 한겨레인지 확인
            allowed = {"경향신문", "한겨레"}
            for art in articles:
                pub = art.get("publisher")
                assert pub in allowed, f"복수 필터 실패: {pub}는 허용된 언론사 아님"


@pytest.mark.asyncio
class TestCombinedFilters:
    """카테고리 + 언론사 복합 필터 검증."""

    async def test_combined_filter(self, init_tools):
        """경제 카테고리 + 한겨레 복합 필터."""
        result = await search_news(
            keyword="경제",
            start_date="2025-12-14",
            end_date="2025-12-15",
            categories=["경제"],
            providers=["한겨레"],
            page_size=10,
        )

        assert result.get("success", False), f"API 호출 실패: {result.get('message')}"
        # 복합 필터는 결과가 0일 수도 있으므로 에러만 체크
        print(f"\n경제+한겨레 복합 필터: {result['total_count']}건")

        articles = result.get("articles", [])
        if articles:
            for art in articles[:5]:
                cat = art.get("category_code", "")
                pub = art.get("publisher", "")
                print(f"  - [{cat[:30]}...] {pub}: {art.get('title', '')[:50]}")

            # 모두 조건을 만족하는지 확인
            for art in articles:
                assert "002000000" in art.get("category_code", ""), "경제 카테고리 아님"
                assert art.get("publisher") == "한겨레", "한겨레 아님"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
