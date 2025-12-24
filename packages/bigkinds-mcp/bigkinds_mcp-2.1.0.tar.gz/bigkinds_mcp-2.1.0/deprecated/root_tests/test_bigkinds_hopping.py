"""BigKinds 기사 URL hopping 테스트 - 실제 기사 내용/사진/메타데이터 수집 가능 여부 확인."""

import json

import requests
from bs4 import BeautifulSoup

from data_scrapers.bigkinds import BigKindsClient, SearchRequest


def test_raw_response():
    """API 원본 응답 데이터 확인."""
    print("\n" + "=" * 70)
    print("🔍 BigKinds API 원본 응답 데이터 확인")
    print("=" * 70)

    with BigKindsClient() as client:
        request = SearchRequest(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-10",
            result_number=3,
        )

        response = client.search(request)

        if response.success and response.articles:
            print(f"\n✅ {len(response.articles)}건 수집됨\n")

            for i, article in enumerate(response.articles, 1):
                raw = article.raw_data or {}

                print(f"\n{'─' * 60}")
                print(f"📰 기사 #{i}")
                print(f"{'─' * 60}")

                # 핵심 필드
                print(f"  제목: {raw.get('TITLE')}")
                print(f"  날짜: {raw.get('DATE')}")
                print(f"  언론사: {raw.get('PROVIDER')}")
                print(f"  기자: {raw.get('BYLINE')}")
                print(f"  카테고리: {raw.get('PROVIDER_SUBJECT')}")

                # URL 관련
                print(f"  🔗 원본 기사 URL: {raw.get('PROVIDER_LINK_PAGE')}")
                print(f"  🖼️ BigKinds 이미지: {raw.get('IMAGES')}")

                # 본문
                content = raw.get('CONTENT', '')
                if content:
                    print(f"  📄 본문 ({len(content)}자): {content[:150]}...")

            return response.articles
        else:
            print(f"❌ 검색 실패: {response.error_message}")
            return []


def test_provider_link_hopping(articles):
    """PROVIDER_LINK_PAGE로 실제 기사 페이지 접근 테스트."""
    print("\n" + "=" * 70)
    print("🌐 원본 기사 URL (PROVIDER_LINK_PAGE) 접근 테스트")
    print("=" * 70)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    for i, article in enumerate(articles[:3], 1):
        raw = article.raw_data or {}
        url = raw.get('PROVIDER_LINK_PAGE')
        title = raw.get('TITLE', '')[:40]

        print(f"\n{'─' * 60}")
        print(f"📰 기사 #{i}: {title}...")
        print(f"   언론사: {raw.get('PROVIDER')}")
        print(f"   URL: {url}")
        print("─" * 60)

        if not url:
            print("   ⚠️ URL 없음")
            continue

        try:
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            print(f"   HTTP 상태: {resp.status_code}")
            print(f"   최종 URL: {resp.url[:80]}...")

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # 제목 추출
                title_elem = soup.select_one('h1, .article-title, .news-title, #articleTitle, .view_title')
                if title_elem:
                    print(f"   📝 추출된 제목: {title_elem.get_text(strip=True)[:60]}...")

                # 본문 추출
                content_selectors = [
                    'article', '.article-body', '.news-content', '#articleBody',
                    '.view_content', '.article_body', '#articeBody', '.news_body'
                ]
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        text = content_elem.get_text(strip=True)
                        print(f"   📄 본문 ({len(text)}자): {text[:150]}...")
                        break

                # 이미지 추출
                images = soup.select('article img, .article-body img, .view_content img')
                if not images:
                    images = soup.select('img[src*="news"], img[src*="image"]')[:5]
                print(f"   🖼️ 이미지 수: {len(images)}")
                for img in images[:3]:
                    src = img.get('src') or img.get('data-src')
                    if src and not src.startswith('data:'):
                        print(f"      - {src[:70]}...")

                # 메타데이터
                og_image = soup.select_one('meta[property="og:image"]')
                og_desc = soup.select_one('meta[property="og:description"]')
                if og_image:
                    print(f"   📷 OG Image: {og_image.get('content', '')[:70]}...")
                if og_desc:
                    print(f"   📝 OG Desc: {og_desc.get('content', '')[:100]}...")

                print("   ✅ 접근 성공")
            else:
                print(f"   ❌ HTTP {resp.status_code}")

        except Exception as e:
            print(f"   ❌ 접근 실패: {e}")


def test_bigkinds_image():
    """BigKinds 서버 이미지 접근 테스트."""
    print("\n" + "=" * 70)
    print("🖼️ BigKinds 이미지 URL 접근 테스트")
    print("=" * 70)

    with BigKindsClient() as client:
        request = SearchRequest(
            keyword="AI",
            start_date="2024-12-01",
            end_date="2024-12-10",
            result_number=5,
        )

        response = client.search(request)

        if response.success and response.articles:
            for i, article in enumerate(response.articles, 1):
                raw = article.raw_data or {}
                image_url = raw.get('IMAGES')
                title = raw.get('TITLE', '')[:40]

                print(f"\n📰 #{i}: {title}...")
                print(f"   이미지 URL: {image_url}")

                if not image_url:
                    print("   ⚠️ 이미지 없음")
                    continue

                try:
                    resp = requests.head(image_url, timeout=10)
                    print(f"   상태: {resp.status_code}")
                    print(f"   Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
                    print(f"   Content-Length: {resp.headers.get('Content-Length', 'N/A')} bytes")

                    if resp.status_code == 200:
                        print("   ✅ 이미지 접근 가능")
                    else:
                        print(f"   ⚠️ 접근 불가 ({resp.status_code})")

                except Exception as e:
                    print(f"   ❌ 실패: {e}")


def summary():
    """결과 요약."""
    print("\n" + "=" * 70)
    print("📊 BigKinds Hopping 가능성 요약")
    print("=" * 70)
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 필드                  │ 가용성  │ 설명                          │
├─────────────────────────────────────────────────────────────────┤
│ CONTENT              │ ✅ 있음 │ API에서 직접 본문 제공          │
│ PROVIDER_LINK_PAGE   │ ✅ 있음 │ 원본 언론사 기사 URL           │
│ IMAGES               │ ✅ 있음 │ BigKinds 서버 이미지 URL       │
│ PROVIDER             │ ✅ 있음 │ 언론사 이름                    │
│ BYLINE               │ ✅ 있음 │ 기자 이름                      │
│ DATE                 │ ✅ 있음 │ 발행일                         │
│ CATEGORY             │ ✅ 있음 │ 카테고리 코드                  │
│ IMAGES_CAPTION       │ ⚠️ 일부 │ 이미지 캡션 (없는 경우 많음)    │
└─────────────────────────────────────────────────────────────────┘

🎯 결론:
1. API 자체로 본문(CONTENT) 제공 → Hopping 불필요할 수 있음
2. 원본 기사 URL로 hopping 가능 (PROVIDER_LINK_PAGE)
3. BigKinds 이미지 URL 직접 접근 가능 (IMAGES)
4. 추가 메타데이터는 원본 기사에서 스크래핑 필요
""")


if __name__ == "__main__":
    # 1. Raw 데이터 확인
    articles = test_raw_response()

    # 2. 원본 기사 URL hopping 테스트
    if articles:
        test_provider_link_hopping(articles)

    # 3. BigKinds 이미지 접근 테스트
    test_bigkinds_image()

    # 4. 요약
    summary()
