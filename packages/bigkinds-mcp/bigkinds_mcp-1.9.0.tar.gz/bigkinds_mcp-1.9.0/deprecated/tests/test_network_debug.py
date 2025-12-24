"""Debug network analysis API response."""

import asyncio
import json
import os
from pathlib import Path

import httpx

# .env 파일 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


async def test_network_api_direct():
    """네트워크 API 직접 호출 디버깅."""

    user_id = os.getenv("BIGKINDS_USER_ID", "")
    password = os.getenv("BIGKINDS_USER_PASSWORD", "")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "Origin": "https://www.bigkinds.or.kr",
        "Referer": "https://www.bigkinds.or.kr/v2/news/index.do",
        "X-Requested-With": "XMLHttpRequest",
    }

    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
        # 메인 페이지
        await client.get("https://www.bigkinds.or.kr/", headers=headers)

        # 로그인
        login_data = {"userId": user_id, "userPassword": password}
        headers["Referer"] = "https://www.bigkinds.or.kr/v2/member/login.do"

        login_resp = await client.post(
            "https://www.bigkinds.or.kr/api/account/signin.do",
            json=login_data,
            headers=headers,
        )
        print(f"Login status: {login_resp.status_code}")
        print(f"Login response: {login_resp.text[:200]}")
        print(f"Cookies: {dict(client.cookies)}")

        # 네트워크 분석 - 여러 파라미터 조합 시도
        test_cases = [
            {
                "name": "Test 1: Recent dates, large news count",
                "data": {
                    "keyword": "AI",
                    "startDate": "2024-12-01",
                    "endDate": "2024-12-15",
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
                },
            },
            {
                "name": "Test 2: Different keyword",
                "data": {
                    "keyword": "삼성",
                    "startDate": "2024-12-01",
                    "endDate": "2024-12-15",
                    "maxNewsCount": 500,
                    "sectionDiv": 1000,
                    "resultNo": 50,
                    "normalization": 10,
                    "isTmUsable": True,
                    "isNotTmUsable": False,
                    "searchFtr": "",
                    "searchScope": "",
                    "providerCode": "",
                    "categoryCode": "",
                    "incidentCode": "",
                    "keywordFilterJson": "",
                },
            },
            {
                "name": "Test 3: Smaller date range",
                "data": {
                    "keyword": "윤석열",
                    "startDate": "2024-12-14",
                    "endDate": "2024-12-15",
                    "maxNewsCount": 100,
                    "sectionDiv": 1000,
                    "resultNo": 50,
                    "normalization": 10,
                    "isTmUsable": True,
                    "isNotTmUsable": False,
                    "searchFtr": "",
                    "searchScope": "",
                    "providerCode": "",
                    "categoryCode": "",
                    "incidentCode": "",
                    "keywordFilterJson": "",
                },
            },
        ]

        headers["Referer"] = "https://www.bigkinds.or.kr/v2/news/index.do"

        for test in test_cases:
            print("\n" + "=" * 60)
            print(test["name"])
            print("=" * 60)

            resp = await client.post(
                "https://www.bigkinds.or.kr/news/getNetworkDataAnalysis.do",
                json=test["data"],
                headers=headers,
            )

            print(f"Status: {resp.status_code}")
            print(f"Request: {json.dumps(test['data'], ensure_ascii=False)}")

            if resp.status_code == 200:
                try:
                    result = resp.json()
                    if isinstance(result, dict):
                        print(f"Response keys: {list(result.keys())}")
                        print(f"Nodes: {len(result.get('nodes', []))}")
                        print(f"Links: {len(result.get('links', []))}")
                        print(f"News IDs: {len(result.get('newsIds', []))}")

                        # 전체 응답 출력 (작은 경우)
                        response_str = json.dumps(result, ensure_ascii=False, indent=2)
                        if len(response_str) < 1000:
                            print(f"Full response:\n{response_str}")
                        else:
                            print(f"Response preview:\n{response_str[:1000]}...")

                        # 노드가 있으면 샘플 출력
                        nodes = result.get("nodes", [])
                        if nodes:
                            print("\nSample nodes:")
                            for node in nodes[:3]:
                                print(f"  - {node}")
                    else:
                        print(f"Response type: {type(result)}")
                        print(f"Response: {result}")
                except Exception as e:
                    print(f"JSON parse error: {e}")
                    print(f"Response text: {resp.text[:500]}")
            else:
                print(f"Error: {resp.text[:500]}")


if __name__ == "__main__":
    asyncio.run(test_network_api_direct())
