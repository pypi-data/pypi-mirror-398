"""Network analysis tool test."""

import asyncio
import os
from pathlib import Path

# .env 파일 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


async def test_network_analysis():
    """네트워크 분석 MCP 도구 테스트."""
    from src.bigkinds_mcp.core.async_client import AsyncBigKindsClient
    from src.bigkinds_mcp.core.cache import MCPCache
    from src.bigkinds_mcp.tools import visualization

    # 초기화
    client = AsyncBigKindsClient()
    cache = MCPCache()
    visualization.init_visualization_tools(client, cache)

    print("=" * 60)
    print("BigKinds Network Analysis Tool Test")
    print("=" * 60)

    # 로그인 테스트
    print("\n1. Testing login...")
    login_success = await client.login()
    if login_success:
        print("   ✅ Login successful")
    else:
        print("   ❌ Login failed - check BIGKINDS_USER_ID and BIGKINDS_USER_PASSWORD")
        print("   Credentials required in .env file")
        return

    # 네트워크 분석 테스트
    print("\n2. Testing network analysis API...")
    result = await visualization.get_network_analysis(
        keyword="AI",
        start_date="2024-12-01",
        end_date="2024-12-10",
        max_news_count=1000,
        result_no=100,
    )

    print(f"   Success: {result.get('success')}")
    print(f"   Keyword: {result.get('keyword')}")
    print(f"   Date range: {result.get('date_range')}")
    print(f"   Total nodes: {result.get('total_nodes')}")
    print(f"   Total links: {result.get('total_links')}")
    print(f"   Total news: {result.get('total_news')}")

    if result.get("success"):
        print("\n3. Node categories:")
        for category, count in result.get("nodes_by_category", {}).items():
            print(f"   - {category}: {count}")

        print("\n4. Top entities:")
        top_entities = result.get("top_entities", {})

        print("   Top 5 People:")
        for entity in top_entities.get("person", [])[:5]:
            print(f"      - {entity['name']}: {entity['weight']}")

        print("\n   Top 5 Organizations:")
        for entity in top_entities.get("organization", [])[:5]:
            print(f"      - {entity['name']}: {entity['weight']}")

        print("\n   Top 5 Locations:")
        for entity in top_entities.get("location", [])[:5]:
            print(f"      - {entity['name']}: {entity['weight']}")

        print("\n   Top 5 Keywords:")
        for entity in top_entities.get("keyword", [])[:5]:
            print(f"      - {entity['name']}: {entity['weight']}")

        # 샘플 노드 출력
        print("\n5. Sample nodes:")
        nodes = result.get("nodes", [])
        if nodes:
            for node in nodes[:3]:
                print(f"   - {node.get('title')} ({node.get('category')})")
                print(f"     ID: {node.get('id')}")
                print(f"     Weight: {node.get('weight')}")
                print(f"     Node size: {node.get('node_size')}")

        # 샘플 링크 출력
        print("\n6. Sample links:")
        links = result.get("links", [])
        if links:
            for link in links[:5]:
                print(f"   - {link.get('from')} -> {link.get('to')} (weight: {link.get('weight')})")

        print("\n✅ Network analysis test successful!")
    else:
        print(f"\n❌ Error: {result.get('error')}")

    # 정리
    client.close()


if __name__ == "__main__":
    asyncio.run(test_network_analysis())
