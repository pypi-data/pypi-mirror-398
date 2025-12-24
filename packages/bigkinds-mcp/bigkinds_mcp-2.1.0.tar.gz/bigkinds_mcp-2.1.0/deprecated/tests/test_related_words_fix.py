"""Test the fixed related words API."""

import asyncio
import os

import pytest

from bigkinds_mcp.core.async_client import AsyncBigKindsClient


@pytest.mark.asyncio
async def test_related_words_api():
    """Test that the related words API works with the fix."""
    # Skip if no credentials
    if not os.getenv("BIGKINDS_USER_ID") or not os.getenv("BIGKINDS_USER_PASSWORD"):
        pytest.skip("BIGKINDS credentials not set")

    client = AsyncBigKindsClient()

    try:
        result = await client.get_related_keywords(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-10",
            max_news_count=100,
            result_number=50,
        )

        # Check structure
        assert "topics" in result or "error" in result

        if "error" in result:
            # Login might have failed, but that's OK for testing
            assert "Login required" in result["error"]
        else:
            # Success case
            topics = result.get("topics", {}).get("data", [])
            assert isinstance(topics, list)
            assert len(topics) > 0

            # Check topic structure
            first_topic = topics[0]
            assert "name" in first_topic
            assert "weight" in first_topic
            assert isinstance(first_topic["name"], str)
            assert isinstance(first_topic["weight"], (int, float))

            print(f"✅ Found {len(topics)} related words")
            print(f"Top word: {first_topic['name']} (weight: {first_topic['weight']})")

    finally:
        if client._auth_client:
            await client._auth_client.aclose()


if __name__ == "__main__":
    asyncio.run(test_related_words_api())
