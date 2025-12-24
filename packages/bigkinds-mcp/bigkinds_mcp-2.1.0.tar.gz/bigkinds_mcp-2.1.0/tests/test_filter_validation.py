"""필터 기능 실제 API 검증 테스트.

이 테스트는 실제 BigKinds API를 호출합니다.
"""

import pytest
from bigkinds_mcp.tools.search import search_news
from bigkinds_mcp.tools.utils import PROVIDER_CODES, CATEGORY_CODES
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
class TestCategoryFilter:
    """카테고리 필터 검증."""

    async def test_all_categories(self, init_tools):
        """모든 카테고리 필터 테스트."""
        # 테스트 키워드 (일반적인 단어)
        keyword = "경제"
        start_date = "2025-12-10"
        end_date = "2025-12-15"

        results = {}

        # 모든 카테고리 순회
        for category_input, category_api in CATEGORY_CODES.items():
            print(f"\n테스트: {category_input} → {category_api}")

            try:
                result = await search_news(
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    page_size=10,
                    categories=[category_input],
                )

                count = result.get("total_count", 0)
                results[category_input] = count

                print(f"  결과: {count}건")

                # 0건은 경고 (필터가 작동하지 않을 수 있음)
                if count == 0:
                    print(f"  ⚠️ 경고: {category_input} 필터가 0건 반환")

            except Exception as e:
                print(f"  ❌ 에러: {e}")
                results[category_input] = -1

        # 결과 요약
        print("\n" + "="*50)
        print("카테고리 필터 테스트 결과")
        print("="*50)
        for cat, count in results.items():
            status = "✅" if count > 0 else "❌" if count == 0 else "⚠️"
            print(f"{status} {cat}: {count}건")


@pytest.mark.asyncio
class TestProviderFilter:
    """언론사 필터 검증."""

    async def test_major_providers(self, init_tools):
        """주요 언론사 필터 테스트."""
        # 테스트 키워드
        keyword = "정치"
        start_date = "2025-12-10"
        end_date = "2025-12-15"

        results = {}

        # 주요 언론사만 테스트 (전체는 시간이 오래 걸림)
        major_providers = [
            "경향신문",
            "한겨레",
            "조선일보",
            "중앙일보",
            "한국경제",
        ]

        for provider_name in major_providers:
            code = PROVIDER_CODES.get(
                [k for k, v in PROVIDER_CODES.items() if v == provider_name][0]
            )
            print(f"\n테스트: {provider_name} (코드: {code})")

            try:
                result = await search_news(
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    page_size=10,
                    providers=[provider_name],
                )

                count = result.get("total_count", 0)
                results[provider_name] = count

                print(f"  결과: {count}건")

                # 0건은 경고
                if count == 0:
                    print(f"  ⚠️ 경고: {provider_name} 필터가 0건 반환")

            except Exception as e:
                print(f"  ❌ 에러: {e}")
                results[provider_name] = -1

        # 결과 요약
        print("\n" + "="*50)
        print("언론사 필터 테스트 결과")
        print("="*50)
        for prov, count in results.items():
            status = "✅" if count > 0 else "❌" if count == 0 else "⚠️"
            print(f"{status} {prov}: {count}건")


@pytest.mark.asyncio
class TestTotalPagesCalculation:
    """total_pages 계산 검증."""

    async def test_total_pages_with_both_sort(self, init_tools):
        """sort_by='both' 시 total_pages 계산 확인."""
        result = await search_news(
            keyword="AI",
            start_date="2025-12-01",
            end_date="2025-12-15",
            page_size=20,
            sort_by="both",
        )

        total_count = result["total_count"]
        page_size = result["page_size"]
        total_pages = result["total_pages"]

        # 계산 검증
        expected_pages = (total_count + page_size - 1) // page_size
        assert total_pages == expected_pages, (
            f"total_pages 계산 오류: "
            f"total_count={total_count}, page_size={page_size}, "
            f"expected={expected_pages}, actual={total_pages}"
        )

        print(f"\n✅ total_pages 계산 정상")
        print(f"  total_count: {total_count}건")
        print(f"  page_size: {page_size}")
        print(f"  total_pages: {total_pages}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
