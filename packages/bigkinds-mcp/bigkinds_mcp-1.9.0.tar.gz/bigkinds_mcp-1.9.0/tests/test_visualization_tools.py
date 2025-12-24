"""시각화 MCP Tools 테스트."""

import asyncio
import os
from pathlib import Path

from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds_mcp.core.cache import MCPCache
from bigkinds_mcp.tools import visualization

# .env 파일 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


async def test_keyword_trends():
    """키워드 트렌드 툴 테스트."""
    print("=" * 60)
    print("키워드 트렌드 툴 테스트")
    print("=" * 60)

    client = AsyncBigKindsClient()
    cache = MCPCache()

    visualization.init_visualization_tools(client, cache)

    try:
        # 테스트 케이스 1: 단일 키워드, 일간
        print("\n1. 단일 키워드 (AI), 일간 트렌드")
        result = await visualization.get_keyword_trends(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-15",
            interval=1,
        )

        print(f"   성공: {result.get('success')}")
        print(f"   키워드 수: {result.get('total_keywords')}")
        print(f"   데이터 포인트: {result.get('total_data_points')}")

        if result.get("trends"):
            for trend in result["trends"]:
                print(f"   - {trend['keyword']}: {trend['total_count']}건")
                if trend['data']:
                    print(f"     첫 데이터: {trend['data'][0]}")
        elif "error" in result:
            print(f"   에러: {result['error']}")
        else:
            print(f"   ⚠️  데이터 없음 (API가 빈 결과 반환)")

        # 테스트 케이스 2: 여러 키워드
        print("\n2. 여러 키워드 (AI,인공지능), 주간 트렌드")
        result = await visualization.get_keyword_trends(
            keyword="AI,인공지능",
            start_date="2024-11-15",
            end_date="2024-12-15",
            interval=2,
        )

        print(f"   성공: {result.get('success')}")
        print(f"   키워드 수: {result.get('total_keywords')}")
        print(f"   시간 단위: {result.get('interval_name')}")

        if result.get("trends"):
            for trend in result["trends"]:
                print(f"   - {trend['keyword']}: {len(trend['data'])} 주")
        elif "error" in result:
            print(f"   에러: {result['error']}")

    finally:
        await client.close()


async def test_related_keywords():
    """연관어 분석 툴 테스트."""
    print("\n" + "=" * 60)
    print("연관어 분석 툴 테스트")
    print("=" * 60)

    client = AsyncBigKindsClient()
    cache = MCPCache()

    visualization.init_visualization_tools(client, cache)

    try:
        # 테스트 케이스
        print("\n1. 연관어 분석 (AI, 100건 분석)")
        result = await visualization.get_related_keywords(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-15",
            max_news_count=100,
            result_number=50,
        )

        print(f"   성공: {result.get('success')}")
        print(f"   분석 뉴스 수: {result.get('news_count')}")
        print(f"   연관어 수: {result.get('total_related_words')}")

        if result.get("top_words"):
            print(f"\n   상위 10개 연관어:")
            for i, word in enumerate(result["top_words"], 1):
                print(f"   {i}. {word['name']}: {word['weight']:.4f}")
        elif "error" in result:
            print(f"   에러: {result['error']}")
        else:
            print(f"   ⚠️  데이터 없음")

    finally:
        await client.close()


# NOTE: test_network_analysis 제거됨
# 사유: /news/getNetworkDataAnalysis.do API는 브라우저 전용
#       httpx 직접 호출 시 302 → /err/error400.do 리다이렉트


async def main():
    """모든 테스트 실행."""
    print("\n🔬 BigKinds 시각화 MCP Tools 테스트\n")

    await test_keyword_trends()
    await test_related_keywords()

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print("\n참고:")
    print("- 로그인 필요: BIGKINDS_USER_ID, BIGKINDS_USER_PASSWORD 환경변수")
    print("- API가 빈 결과를 반환하는 경우: 계정 권한 또는 데이터 부족")
    print("- 정상적으로 로그인되면 에러 메시지가 없어야 합니다")
    print("- 네트워크 분석(관계도)은 브라우저 전용으로 제거됨")


if __name__ == "__main__":
    asyncio.run(main())
