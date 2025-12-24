"""BigKinds API 테스트 - 로그인 없이 시각화 API 호출 가능 여부 상세 확인."""

import asyncio
import json

import httpx


async def test_visualization_apis_detailed():
    """시각화 API 상세 테스트."""

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "Origin": "https://www.bigkinds.or.kr",
        "Referer": "https://www.bigkinds.or.kr/v2/news/index.do",
        "X-Requested-With": "XMLHttpRequest",
    }

    async with httpx.AsyncClient(
        verify=False,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        # 메인 페이지 먼저 접속 (세션 쿠키 획득)
        print("1️⃣  메인 페이지 접속 (세션 초기화)...")
        await client.get("https://www.bigkinds.or.kr/", headers=headers)
        print(f"   쿠키: {dict(client.cookies)}")

        # ========================================
        # 키워드 트렌드 API (로그인 없이 작동 확인됨)
        # ========================================
        print("\n" + "=" * 50)
        print("📊 키워드 트렌드 API (POST /api/analysis/keywordTrends.do)")
        print("=" * 50)

        trend_data = {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "interval": 1,  # 1: 일간, 2: 주간, 3: 월간
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/api/analysis/keywordTrends.do",
            json=trend_data,
            headers=headers,
        )
        print(f"상태: {resp.status_code}")
        print(f"요청: {json.dumps(trend_data, ensure_ascii=False)}")

        if resp.status_code == 200:
            result = resp.json()
            print(f"응답 구조: {list(result.keys())}")

            if "root" in result and result["root"]:
                root = result["root"]
                if isinstance(root, list) and len(root) > 0:
                    first = root[0]
                    print(f"첫 번째 항목 키: {list(first.keys()) if isinstance(first, dict) else type(first)}")
                    if isinstance(first, dict) and "data" in first:
                        data_points = first.get("data", [])
                        print(f"데이터 포인트 수: {len(data_points)}")
                        if data_points:
                            print(f"샘플 데이터: {data_points[:3]}")
                else:
                    print(f"root 내용: {root}")
            else:
                print(f"전체 응답: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
        else:
            print(f"오류 응답: {resp.text[:300]}")

        # ========================================
        # 연관어 분석 API
        # ========================================
        print("\n" + "=" * 50)
        print("🔗 연관어 분석 API (POST /api/analysis/relationalWords.do)")
        print("=" * 50)

        # 더 넓은 기간, 더 많은 뉴스로 테스트
        relational_data = {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "maxNewsCount": 1000,
            "resultNumber": 50,
            "analysisType": "relational_word",
            "startNo": 0,
            "providerCode": "",
            "categoryCode": "",
            "incidentCode": "",
            "isTmUsable": True,
            "searchInKey": "",
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/api/analysis/relationalWords.do",
            json=relational_data,
            headers=headers,
        )
        print(f"상태: {resp.status_code}")
        print(f"요청: {json.dumps(relational_data, ensure_ascii=False)}")

        if resp.status_code == 200:
            result = resp.json()
            print(f"응답 구조: {list(result.keys())}")

            if "topics" in result:
                topics = result.get("topics", {})
                if isinstance(topics, dict) and "data" in topics:
                    data = topics["data"]
                    print(f"연관어 수: {len(data)}")
                    if data:
                        print(f"상위 5개 연관어: {data[:5]}")
            else:
                print(f"전체 응답: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
        else:
            print(f"오류 응답: {resp.text[:300]}")

        # ========================================
        # 관계도 분석 API
        # ========================================
        print("\n" + "=" * 50)
        print("🕸️  관계도 분석 API (POST /news/getNetworkDataAnalysis.do)")
        print("=" * 50)

        network_data = {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "maxNewsCount": 1000,
            "sectionDiv": 1000,
            "resultNo": 100,
            "normalization": 10,
            "isTmUsable": True,
            "isNotTmUsable": False,
            "searchFtr": "",
            "searchScope": "",
            "providerCode": "",
            "categoryCode": "",
            "incidentCode": "",
            "keywordFilterJson": "",
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/news/getNetworkDataAnalysis.do",
            json=network_data,
            headers=headers,
        )
        print(f"상태: {resp.status_code}")
        print(f"요청: {json.dumps(network_data, ensure_ascii=False)}")

        if resp.status_code == 200:
            result = resp.json()
            if isinstance(result, dict):
                print(f"응답 구조: {list(result.keys())}")

                if "nodes" in result:
                    nodes = result.get("nodes", [])
                    print(f"노드 수: {len(nodes)}")
                    if nodes:
                        print(f"첫 번째 노드: {json.dumps(nodes[0], ensure_ascii=False)}")

                if "links" in result:
                    links = result.get("links", [])
                    print(f"링크 수: {len(links)}")
                    if links:
                        print(f"첫 번째 링크: {json.dumps(links[0], ensure_ascii=False)}")

                if not result:
                    print("빈 응답 (로그인 필요할 수 있음)")
            else:
                print(f"응답 타입: {type(result)}")
                print(f"응답 내용: {result[:500] if isinstance(result, str) else result}")
        else:
            print(f"오류 응답: {resp.text[:300]}")

        # ========================================
        # 뉴스 검색 API (비교용 - 공개 API)
        # ========================================
        print("\n" + "=" * 50)
        print("📰 뉴스 검색 API (POST /api/news/search.do)")
        print("=" * 50)

        search_data = {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "pageInfo": {
                "page": 1,
                "size": 5
            },
            "sortMethod": "date",
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/api/news/search.do",
            json=search_data,
            headers=headers,
        )
        print(f"상태: {resp.status_code}")

        if resp.status_code == 200:
            result = resp.json()
            print(f"응답 구조: {list(result.keys())}")
            if "resultList" in result:
                print(f"검색 결과 수: {len(result.get('resultList', []))}")
        else:
            print(f"오류 응답: {resp.text[:300]}")

        # ========================================
        # 결론
        # ========================================
        print("\n" + "=" * 50)
        print("📋 결론")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_visualization_apis_detailed())
