"""정우성 복귀 기사 전문 수집 스크립트.

Usage:
    uv run python scripts/collect_articles.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bigkinds_mcp.core.async_client import AsyncBigKindsClient
from bigkinds.client import BigKindsClient
from bigkinds.models import SearchRequest

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "jung_woosong_articles.json"


async def collect_articles(keyword: str, start_date: str, end_date: str):
    """기사 검색 및 전문 수집."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 동기 클라이언트로 검색 (기존 client.py 활용)
    sync_client = BigKindsClient()
    async_client = AsyncBigKindsClient()

    print(f"[1/3] 기사 검색 중: {keyword}")
    print(f"      기간: {start_date} ~ {end_date}")

    # 검색 요청 (한 번에 최대 1000건까지)
    request = SearchRequest(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        sort_method="date",
        result_number=1000,
        start_no=1,
    )

    response = sync_client.search(request)
    total_count = response.total_count
    print(f"      검색 결과: {total_count}건")

    # 모든 기사 수집 (페이지네이션)
    all_articles = list(response.articles)

    # 추가 페이지가 있으면 수집
    if total_count > 1000:
        total_pages = (total_count + 999) // 1000
        for page in range(2, total_pages + 1):
            request.start_no = (page - 1) * 1000 + 1
            response = sync_client.search(request)
            all_articles.extend(list(response.articles))
            print(f"      페이지 {page}/{total_pages} 수집 완료")

    print(f"\n[2/3] 기사 전문 수집 중 ({len(all_articles)}건)...")

    # 언론사별로 그룹핑 (중복 제거용)
    seen_publishers = {}
    articles_with_content = []

    for i, article in enumerate(all_articles):
        news_id = article.news_id
        publisher = article.publisher or "Unknown"

        # 언론사당 최대 1개만 (전체 비교를 위해)
        if publisher in seen_publishers:
            continue

        print(f"      [{i+1}/{len(all_articles)}] {publisher} - {article.title[:30]}...")

        try:
            # detailView API로 전문 가져오기
            detail_result = await async_client.get_article_detail(news_id)

            if detail_result.get("success"):
                detail = detail_result.get("detail", {})
                content = detail.get("CONTENT", "")

                if content:
                    # HTML 태그 정리
                    content = content.replace("<br/>", "\n").replace("<br>", "\n")
                    content = content.replace("&nbsp;", " ")

                    article_data = {
                        "news_id": news_id,
                        "title": detail.get("TITLE", article.title),
                        "publisher": publisher,
                        "published_date": detail.get("DATE", ""),
                        "author": detail.get("BYLINE", ""),
                        "content": content,
                        "content_length": len(content),
                        "url": detail.get("PROVIDER_LINK_PAGE", ""),
                        "category": article.category,
                    }

                    articles_with_content.append(article_data)
                    seen_publishers[publisher] = True
                    print(f"            ✓ 전문 수집 완료 ({len(content)}자)")
                else:
                    print(f"            ✗ 전문 없음 (API 응답에 CONTENT 없음)")
            else:
                print(f"            ✗ API 실패: {detail_result.get('error', 'Unknown')}")

        except Exception as e:
            print(f"            ✗ 오류: {e}")

        # Rate limiting
        await asyncio.sleep(0.5)

    print(f"\n[3/3] 저장 중...")

    # JSON 저장
    output_data = {
        "keyword": keyword,
        "date_range": f"{start_date} ~ {end_date}",
        "collected_at": datetime.now().isoformat(),
        "total_searched": total_count,
        "total_collected": len(articles_with_content),
        "publishers_collected": list(seen_publishers.keys()),
        "articles": articles_with_content,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"      저장 완료: {OUTPUT_FILE}")
    print(f"\n=== 수집 완료 ===")
    print(f"총 검색: {total_count}건")
    print(f"전문 수집: {len(articles_with_content)}건")
    print(f"언론사: {len(seen_publishers)}개")

    sync_client.close()
    async_client.close()

    return output_data


if __name__ == "__main__":
    asyncio.run(collect_articles(
        keyword="정우성 메이드 인 코리아",
        start_date="2025-12-14",
        end_date="2025-12-15",
    ))
