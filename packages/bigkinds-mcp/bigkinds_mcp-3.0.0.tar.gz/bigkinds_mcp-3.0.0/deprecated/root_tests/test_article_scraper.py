"""BigKinds → 원본 기사 hopping 테스트."""

from data_scrapers.bigkinds import (
    ArticleScraper,
    BigKindsClient,
    SearchRequest,
    scrape_article,
)


def test_full_pipeline():
    """BigKinds 검색 → 원본 기사 스크래핑 전체 파이프라인 테스트."""
    print("\n" + "=" * 70)
    print("🔄 BigKinds → 원본 기사 Hopping 테스트")
    print("=" * 70)

    # 1. BigKinds에서 기사 검색
    print("\n📡 Step 1: BigKinds API 검색...")
    with BigKindsClient() as client:
        request = SearchRequest(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-10",
            result_number=5,
        )
        response = client.search(request)

    if not response.success:
        print(f"❌ BigKinds 검색 실패: {response.error_message}")
        return

    print(f"✅ {len(response.articles)}건 검색됨\n")

    # 2. 각 기사 원본 URL로 hopping
    print("🌐 Step 2: 원본 기사 스크래핑...")
    print("=" * 70)

    with ArticleScraper() as scraper:
        for i, article in enumerate(response.articles, 1):
            raw = article.raw_data or {}
            original_url = raw.get("PROVIDER_LINK_PAGE")
            bigkinds_title = raw.get("TITLE", "")[:50]
            bigkinds_content = raw.get("CONTENT", "")

            print(f"\n{'─' * 60}")
            print(f"📰 기사 #{i}: {bigkinds_title}...")
            print(f"   BigKinds 본문 길이: {len(bigkinds_content)}자")
            print(f"   원본 URL: {original_url}")

            if not original_url:
                print("   ⚠️ 원본 URL 없음 - 스킵")
                continue

            # 스크래핑
            scraped = scraper.scrape(original_url)

            if scraped.success:
                print(f"\n   ✅ 스크래핑 성공!")
                print(f"   ├─ HTTP: {scraped.http_status}")
                print(f"   ├─ 제목: {scraped.title[:60] if scraped.title else '(없음)'}...")
                print(f"   ├─ 언론사: {scraped.publisher}")
                print(f"   ├─ 작성자: {scraped.author}")
                print(f"   ├─ 발행일: {scraped.published_date}")
                print(f"   ├─ 키워드: {scraped.keywords[:5] if scraped.keywords else []}")

                # 본문 비교
                scraped_len = len(scraped.content) if scraped.content else 0
                print(f"   ├─ 스크래핑 본문: {scraped_len}자")

                if scraped.content:
                    print(f"   │  미리보기: {scraped.content[:150]}...")

                # 이미지
                print(f"   ├─ 이미지 수: {len(scraped.images)}")
                if scraped.main_image:
                    print(f"   │  메인 이미지: {scraped.main_image[:70]}...")
                for img in scraped.images[:3]:
                    if not img.get("is_main"):
                        print(f"   │  - {img['url'][:60]}...")

                # 본문 증가율
                if bigkinds_content and scraped.content:
                    increase = (scraped_len / len(bigkinds_content) - 1) * 100
                    print(f"   └─ 본문 증가: +{increase:.0f}%")

            else:
                print(f"   ❌ 스크래핑 실패: {scraped.error}")


def test_various_publishers():
    """다양한 언론사 스크래핑 테스트."""
    print("\n" + "=" * 70)
    print("🏢 언론사별 스크래핑 테스트")
    print("=" * 70)

    # BigKinds에서 다양한 언론사 기사 수집
    with BigKindsClient() as client:
        request = SearchRequest(
            keyword="경제",
            start_date="2024-12-01",
            end_date="2024-12-10",
            result_number=20,
        )
        response = client.search(request)

    if not response.success:
        print(f"❌ 검색 실패")
        return

    # 언론사별로 그룹핑
    by_publisher = {}
    for article in response.articles:
        raw = article.raw_data or {}
        publisher = raw.get("PROVIDER", "Unknown")
        if publisher not in by_publisher:
            by_publisher[publisher] = []
        by_publisher[publisher].append(article)

    print(f"\n발견된 언론사: {list(by_publisher.keys())}\n")

    # 언론사별 1개씩 테스트
    with ArticleScraper() as scraper:
        for publisher, articles in list(by_publisher.items())[:8]:
            article = articles[0]
            raw = article.raw_data or {}
            url = raw.get("PROVIDER_LINK_PAGE")

            print(f"\n{'─' * 50}")
            print(f"🏢 {publisher}")

            if not url:
                print("   ⚠️ URL 없음")
                continue

            scraped = scraper.scrape(url)

            if scraped.success:
                content_len = len(scraped.content) if scraped.content else 0
                img_count = len(scraped.images)
                print(f"   ✅ 성공 | 본문: {content_len}자 | 이미지: {img_count}개")
                print(f"   제목: {scraped.title[:50] if scraped.title else '-'}...")
            else:
                print(f"   ❌ 실패: {scraped.error}")


def test_simple():
    """단순 스크래핑 테스트."""
    print("\n" + "=" * 70)
    print("🧪 단순 스크래핑 테스트")
    print("=" * 70)

    # 테스트 URL들
    test_urls = [
        "https://www.mk.co.kr/news/economy/11190021",
        "https://www.ilyo.co.kr/?ac=article_view&entry_id=483644",
        "http://www.breaknews.com/1078756",
    ]

    for url in test_urls:
        print(f"\n📰 {url[:50]}...")
        result = scrape_article(url)

        if result.success:
            print(f"   ✅ 제목: {result.title[:50] if result.title else '-'}...")
            print(f"   본문: {len(result.content) if result.content else 0}자")
            print(f"   이미지: {len(result.images)}개")
        else:
            print(f"   ❌ {result.error}")


if __name__ == "__main__":
    # 1. 전체 파이프라인 테스트
    test_full_pipeline()

    # 2. 다양한 언론사 테스트
    test_various_publishers()

    # 3. 단순 테스트
    # test_simple()
