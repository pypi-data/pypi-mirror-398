"""BigKinds API 다양한 시나리오 테스트."""

import time
from dataclasses import dataclass

from data_scrapers.bigkinds import BigKindsClient, BigKindsSearcher, SearchRequest


@dataclass
class TestScenario:
    """테스트 시나리오 정의."""

    name: str
    keyword: str
    start_date: str
    end_date: str
    max_articles: int


# 테스트 시나리오 정의
SCENARIOS = [
    # 1. 다양한 토픽 테스트 (최근 1개월, 소량)
    TestScenario("토픽-AI", "인공지능", "2024-11-01", "2024-11-30", 10),
    TestScenario("토픽-경제", "경제위기", "2024-11-01", "2024-11-30", 10),
    TestScenario("토픽-정치", "대통령", "2024-11-01", "2024-11-30", 10),
    TestScenario("토픽-부동산", "부동산", "2024-11-01", "2024-11-30", 10),
    TestScenario("토픽-환경", "기후변화", "2024-11-01", "2024-11-30", 10),
    # 2. 연대별 테스트 (동일 키워드)
    TestScenario("연대-1990s", "경제", "1990-01-01", "1990-12-31", 10),
    TestScenario("연대-2000s", "경제", "2000-01-01", "2000-12-31", 10),
    TestScenario("연대-2010s", "경제", "2010-01-01", "2010-12-31", 10),
    TestScenario("연대-2020s", "경제", "2020-01-01", "2020-12-31", 10),
    # 3. 아주 오래된 데이터 (1980년대)
    TestScenario("역사-1980", "올림픽", "1988-01-01", "1988-12-31", 10),
    TestScenario("역사-1985", "경제", "1985-01-01", "1985-12-31", 10),
    # 4. 대량 수집 테스트 (최근 데이터)
    TestScenario("대량-100건", "AI", "2024-01-01", "2024-01-31", 100),
    TestScenario("대량-1000건", "AI", "2024-01-01", "2024-06-30", 1000),
]


def test_health_check():
    """API 상태 확인."""
    print("\n" + "=" * 70)
    print("🏥 BigKinds API Health Check")
    print("=" * 70)

    with BigKindsClient() as client:
        is_healthy = client.health_check()
        status = "✅ OK" if is_healthy else "❌ FAILED"
        print(f"API Status: {status}")
        return is_healthy


def test_scenario(scenario: TestScenario) -> dict:
    """단일 시나리오 테스트."""
    print(f"\n{'─' * 60}")
    print(f"📋 {scenario.name}")
    print(f"   키워드: {scenario.keyword}")
    print(f"   기간: {scenario.start_date} ~ {scenario.end_date}")
    print(f"   최대: {scenario.max_articles}건")
    print("─" * 60)

    result = {
        "name": scenario.name,
        "keyword": scenario.keyword,
        "date_range": f"{scenario.start_date} ~ {scenario.end_date}",
        "max_articles": scenario.max_articles,
        "success": False,
        "total_available": 0,
        "fetched": 0,
        "error": None,
        "duration": 0,
    }

    start_time = time.time()

    try:
        with BigKindsClient() as client:
            # 먼저 총 개수 확인
            total = client.get_total_count(scenario.keyword, scenario.start_date, scenario.end_date)
            result["total_available"] = total
            print(f"   📊 총 기사 수: {total:,}건")

            if total == 0:
                print("   ⚠️ 검색 결과 없음")
                result["success"] = True
                return result

            # 실제 검색 (소량만)
            request = SearchRequest(
                keyword=scenario.keyword,
                start_date=scenario.start_date,
                end_date=scenario.end_date,
                result_number=min(scenario.max_articles, total),
            )

            response = client.search(request)

            if response.success:
                result["success"] = True
                result["fetched"] = len(response.articles)
                print(f"   ✅ 수집 성공: {result['fetched']:,}건")

                # 샘플 기사 출력
                if response.articles:
                    sample = response.articles[0]
                    print(
                        f"   📰 샘플: {sample.title[:50]}..."
                        if len(sample.title) > 50
                        else f"   📰 샘플: {sample.title}"
                    )
                    print(f"      발행: {sample.news_date}, 언론사: {sample.publisher}")
            else:
                result["error"] = response.error_message
                print(f"   ❌ 실패: {response.error_message}")

    except Exception as e:
        result["error"] = str(e)
        print(f"   ❌ 에러: {e}")

    result["duration"] = round(time.time() - start_time, 2)
    print(f"   ⏱️ 소요시간: {result['duration']}초")

    return result


def test_bulk_fetch():
    """대량 수집 테스트 (Searcher 사용)."""
    print("\n" + "=" * 70)
    print("📦 대량 수집 테스트 (BigKindsSearcher)")
    print("=" * 70)

    with BigKindsSearcher(max_total=500, show_progress=True) as searcher:
        response = searcher.search(
            keyword="AI",
            start_date="2024-01-01",
            end_date="2024-03-31",
            print_results=False,
        )

        if response.success:
            print(f"\n✅ 대량 수집 완료: {len(response.articles):,}건")
            return True
        else:
            print(f"\n❌ 대량 수집 실패: {response.error_message}")
            return False


def main():
    """메인 테스트 실행."""
    print("\n" + "=" * 70)
    print("🧪 BigKinds API 종합 테스트")
    print("=" * 70)

    # 1. 헬스체크
    if not test_health_check():
        print("\n⛔ API가 응답하지 않습니다. 테스트 중단.")
        return

    # 2. 각 시나리오 테스트
    results = []
    for scenario in SCENARIOS:
        result = test_scenario(scenario)
        results.append(result)
        time.sleep(0.5)  # Rate limiting

    # 3. 대량 수집 테스트
    print("\n")
    test_bulk_fetch()

    # 4. 결과 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)

    success_count = sum(1 for r in results if r["success"])
    print(f"\n총 {len(results)}개 시나리오 중 {success_count}개 성공\n")

    print(f"{'시나리오':<20} {'성공':^6} {'총기사':>10} {'수집':>8} {'시간':>8}")
    print("-" * 60)

    for r in results:
        status = "✅" if r["success"] else "❌"
        print(
            f"{r['name']:<20} {status:^6} {r['total_available']:>10,} "
            f"{r['fetched']:>8,} {r['duration']:>7.1f}s"
        )

    # 연대별 데이터 가용성
    print("\n📅 연대별 데이터 가용성:")
    decade_results = [
        r for r in results if r["name"].startswith("연대-") or r["name"].startswith("역사-")
    ]
    for r in decade_results:
        availability = "✅ 있음" if r["total_available"] > 0 else "❌ 없음"
        print(f"   {r['name']}: {r['total_available']:,}건 {availability}")


if __name__ == "__main__":
    main()
