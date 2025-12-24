"""모든 언론사 필터를 체계적으로 테스트."""

import pytest
from bigkinds_mcp.tools.search import search_news
from bigkinds_mcp.tools.utils import PROVIDER_CODES
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
class TestAllProviderFilters:
    """모든 언론사 필터 체계적 검증."""

    async def test_all_providers_sequentially(self, init_tools):
        """모든 언론사를 순차적으로 테스트 (주요 언론사 위주)."""

        # 주요 언론사만 테스트 (시간 절약)
        major_providers = [
            ("01100101", "경향신문"),
            ("01101001", "한겨레"),
            ("01100401", "동아일보"),
            ("01100801", "조선일보"),
            ("01100901", "중앙일보"),
            ("01101101", "한국일보"),
            ("02100101", "매일경제"),
            ("02100601", "한국경제"),
            ("07100501", "전자신문"),
            ("08100101", "KBS"),
            ("08100301", "SBS"),
            ("08100401", "YTN"),
        ]

        print(f"\n{'='*60}")
        print(f"Testing {len(major_providers)} major providers")
        print(f"{'='*60}\n")

        results = {
            "success": [],
            "failed": [],
            "zero_results": [],
        }

        for code, name in major_providers:
            print(f"Testing: {name} ({code})...", end=" ")

            try:
                result = await search_news(
                    keyword="정치",
                    start_date="2025-12-14",
                    end_date="2025-12-15",
                    providers=[name],  # Use name (will be converted to code)
                    page_size=5,
                )

                total_count = result.get("total_count", 0)

                if total_count == 0:
                    results["zero_results"].append((code, name))
                    print(f"⚠️  0건")
                else:
                    # Verify articles match the provider
                    articles = result.get("articles", [])
                    if articles:
                        mismatch = [a for a in articles if a.get("provider_code") != code]

                        if mismatch:
                            results["failed"].append((code, name, f"{len(mismatch)} mismatches"))
                            print(f"❌ {total_count}건 (mismatch: {len(mismatch)})")
                        else:
                            results["success"].append((code, name, total_count))
                            print(f"✅ {total_count}건")
                    else:
                        results["success"].append((code, name, total_count))
                        print(f"✅ {total_count}건")

            except Exception as e:
                results["failed"].append((code, name, str(e)))
                print(f"❌ Error: {e}")

        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Success: {len(results['success'])}/{len(major_providers)}")
        print(f"⚠️  Zero Results: {len(results['zero_results'])}")
        print(f"❌ Failed: {len(results['failed'])}")

        if results["zero_results"]:
            print("\nProviders with zero results:")
            for code, name in results["zero_results"]:
                print(f"  - {code}: {name}")

        if results["failed"]:
            print("\nFailed providers:")
            for item in results["failed"]:
                if len(item) == 3:
                    code, name, error = item
                    print(f"  - {code}: {name} ({error})")

        # Assert most providers work
        success_rate = len(results["success"]) / len(major_providers)
        assert success_rate >= 0.7, f"Success rate too low: {success_rate:.1%}"


@pytest.mark.asyncio
class TestProviderNameToCodeConversion:
    """언론사 이름 → 코드 변환 테스트."""

    async def test_name_to_code_mapping(self, init_tools):
        """주요 언론사 이름이 올바른 코드로 변환되는지 확인."""

        test_cases = {
            "경향신문": "01100101",
            "한겨레": "01101001",
            "조선일보": "01100801",
            "중앙일보": "01100901",
            "전자신문": "07100501",
        }

        from bigkinds_mcp.tools.utils import PROVIDER_NAME_TO_CODE

        for name, expected_code in test_cases.items():
            actual_code = PROVIDER_NAME_TO_CODE.get(name)
            print(f"{name} → {actual_code} (expected: {expected_code})")
            assert actual_code == expected_code, f"{name} maps to {actual_code}, expected {expected_code}"


@pytest.mark.asyncio
class TestSpecificProviderFilters:
    """개별 언론사 필터 상세 검증."""

    async def test_kyunghyang_filter(self, init_tools):
        """경향신문 필터 상세 검증."""
        result = await search_news(
            keyword="정치",
            start_date="2025-12-14",
            end_date="2025-12-15",
            providers=["경향신문"],
            page_size=10,
        )

        print(f"\n경향신문 필터: {result.get('total_count', 0)}건")

        articles = result.get("articles", [])
        if articles:
            for art in articles[:5]:
                print(f"  - {art.get('provider_code')}: {art.get('publisher')}")

            # All should be from 경향신문 (01100101)
            non_kyunghyang = [a for a in articles
                              if a.get("provider_code") != "01100101"]

            if non_kyunghyang:
                print(f"\n⚠️  Non-경향신문 articles:")
                for art in non_kyunghyang:
                    print(f"    - {art.get('provider_code')}: {art.get('publisher')}")

            assert len(non_kyunghyang) == 0, f"Found {len(non_kyunghyang)} non-경향신문 articles"

    async def test_hankyoreh_filter(self, init_tools):
        """한겨레 필터 상세 검증."""
        result = await search_news(
            keyword="경제",
            start_date="2025-12-14",
            end_date="2025-12-15",
            providers=["한겨레"],
            page_size=10,
        )

        print(f"\n한겨레 필터: {result.get('total_count', 0)}건")

        articles = result.get("articles", [])
        if articles:
            for art in articles[:5]:
                print(f"  - {art.get('provider_code')}: {art.get('publisher')}")

            # All should be from 한겨레 (01101001)
            non_hankyoreh = [a for a in articles
                             if a.get("provider_code") != "01101001"]

            if non_hankyoreh:
                print(f"\n⚠️  Non-한겨레 articles:")
                for art in non_hankyoreh:
                    print(f"    - {art.get('provider_code')}: {art.get('publisher')}")

            assert len(non_hankyoreh) == 0, f"Found {len(non_hankyoreh)} non-한겨레 articles"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
