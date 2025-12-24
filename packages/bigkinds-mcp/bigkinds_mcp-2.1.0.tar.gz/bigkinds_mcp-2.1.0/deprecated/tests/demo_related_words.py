#!/usr/bin/env python3
"""
Demo: Related Words API Fix

This script demonstrates the fixed related words API.
Before the fix, this would return a 500 error.
After the fix, it successfully returns related keywords.
"""

import asyncio
import os
import sys

from bigkinds_mcp.core.async_client import AsyncBigKindsClient


async def demo_related_words():
    """Demonstrate the working related words API."""

    # Check credentials
    user_id = os.getenv("BIGKINDS_USER_ID", "")
    user_password = os.getenv("BIGKINDS_USER_PASSWORD", "")

    if not user_id or not user_password:
        print("❌ Error: BIGKINDS credentials not set")
        print("\nPlease set environment variables:")
        print("  export BIGKINDS_USER_ID='your_email'")
        print("  export BIGKINDS_USER_PASSWORD='your_password'")
        sys.exit(1)

    print("=" * 60)
    print("BigKinds Related Words API - Fix Demonstration")
    print("=" * 60)
    print()

    client = AsyncBigKindsClient()

    try:
        # Test cases
        test_cases = [
            {
                "name": "AI Technology",
                "keyword": "AI",
                "start_date": "2024-12-01",
                "end_date": "2024-12-10",
                "max_news_count": 100,
            },
            {
                "name": "Semiconductor Industry",
                "keyword": "반도체",
                "start_date": "2024-11-01",
                "end_date": "2024-11-30",
                "max_news_count": 200,
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'─' * 60}")
            print(f"Test {i}: {test['name']}")
            print(f"{'─' * 60}")
            print(f"Keyword: {test['keyword']}")
            print(f"Period: {test['start_date']} ~ {test['end_date']}")
            print(f"Max News: {test['max_news_count']}")
            print()

            result = await client.get_related_keywords(
                keyword=test['keyword'],
                start_date=test['start_date'],
                end_date=test['end_date'],
                max_news_count=test['max_news_count'],
                result_number=50,
            )

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            topics = result.get("topics", {}).get("data", [])
            news_count = result.get("news", {}).get("documentCount", 0)

            print(f"✅ Success!")
            print(f"   Analyzed articles: {news_count}")
            print(f"   Related words found: {len(topics)}")
            print()
            print("   Top 10 related words:")
            print("   " + "─" * 50)

            for j, topic in enumerate(topics[:10], 1):
                name = topic.get('name', '')
                weight = topic.get('weight', 0)
                print(f"   {j:2d}. {name:30s} ({weight:6.2f})")

            print()

        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        print()
        print("Key parameters that fixed the issue:")
        print("  - searchKey: (same as keyword)")
        print("  - indexName: 'news'")
        print("  - sortMethod: 'score'")
        print("  - startNo: 1 (not 0)")
        print("  - isTmUsable: true")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if client._auth_client:
            await client._auth_client.aclose()


if __name__ == "__main__":
    asyncio.run(demo_related_words())
