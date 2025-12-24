"""키워드 트렌드 API 상세 테스트 - 왜 빈 결과가 나오는지 확인."""

import asyncio
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


async def test_keyword_trends_params():
    """다양한 파라미터로 키워드 트렌드 API 테스트."""

    user_id = os.getenv("BIGKINDS_USER_ID", "")
    user_password = os.getenv("BIGKINDS_USER_PASSWORD", "")

    if not user_id or not user_password:
        print("❌ 환경변수 필요: BIGKINDS_USER_ID, BIGKINDS_USER_PASSWORD")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "Origin": "https://www.bigkinds.or.kr",
        "Referer": "https://www.bigkinds.or.kr/v2/news/visualize.do",
        "X-Requested-With": "XMLHttpRequest",
    }

    async with httpx.AsyncClient(
        verify=False,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        # 로그인
        print("🔐 로그인 중...")
        await client.get("https://www.bigkinds.or.kr/", headers=headers)

        login_resp = await client.post(
            "https://www.bigkinds.or.kr/api/account/signin2023.do",
            json={"userId": user_id, "userPassword": user_password},
            headers=headers,
        )

        if login_resp.status_code != 200:
            print(f"❌ 로그인 실패: {login_resp.status_code}")
            return

        login_data = login_resp.json()
        if not login_data.get("success"):
            print(f"❌ 로그인 실패: {login_data}")
            return

        print("✅ 로그인 성공")
        print(f"   쿠키: {dict(client.cookies)}\n")

        # 다양한 파라미터 조합으로 테스트 (2025년 날짜로 테스트)
        test_cases = [
            {
                "name": "2025년 최근 1주일, 일간",
                "params": {
                    "keyword": "AI",
                    "startDate": "2025-12-08",
                    "endDate": "2025-12-15",
                    "interval": 1,
                },
            },
            {
                "name": "2025년 인기 키워드 (대통령)",
                "params": {
                    "keyword": "대통령",
                    "startDate": "2025-12-01",
                    "endDate": "2025-12-15",
                    "interval": 1,
                },
            },
            {
                "name": "2024년 최근 데이터",
                "params": {
                    "keyword": "AI",
                    "startDate": "2024-12-01",
                    "endDate": "2024-12-15",
                    "interval": 1,
                },
            },
            {
                "name": "과거 데이터 (2024년 1월)",
                "params": {
                    "keyword": "AI",
                    "startDate": "2024-01-01",
                    "endDate": "2024-01-31",
                    "interval": 1,
                },
            },
            {
                "name": "완전한 파라미터 (모든 필드 포함)",
                "params": {
                    "keyword": "AI",
                    "startDate": "2025-12-01",
                    "endDate": "2025-12-15",
                    "interval": 1,
                    "providerCode": "",
                    "categoryCode": "",
                    "incidentCode": "",
                    "isTmUsable": False,
                    "isNotTmUsable": False,
                },
            },
        ]

        for idx, test in enumerate(test_cases, 1):
            print(f"{idx}️⃣  {test['name']}")
            print(f"   파라미터: {test['params']}")

            try:
                resp = await client.post(
                    "https://www.bigkinds.or.kr/api/analysis/keywordTrends.do",
                    json=test["params"],
                    headers=headers,
                )

                print(f"   상태: {resp.status_code}")

                if resp.status_code == 200:
                    result = resp.json()
                    print(f"   응답 키: {list(result.keys())}")

                    if "root" in result:
                        root_data = result["root"]
                        print(f"   root 타입: {type(root_data)}, 길이: {len(root_data) if isinstance(root_data, list) else 'N/A'}")

                        if isinstance(root_data, list) and len(root_data) > 0:
                            print(f"   ✅ 데이터 발견! 첫 항목: {root_data[0]}")
                            if "data" in root_data[0]:
                                print(f"      데이터 포인트 수: {len(root_data[0]['data'])}")
                                if root_data[0]['data']:
                                    print(f"      첫 데이터 포인트: {root_data[0]['data'][0]}")
                        else:
                            print(f"   ⚠️  root가 비어있거나 예상과 다름: {root_data}")
                    else:
                        print(f"   ⚠️  root 키 없음. 전체 응답: {result}")
                else:
                    print(f"   ❌ 오류: {resp.text[:200]}")

            except Exception as e:
                print(f"   ❌ 예외: {e}")

            print()


if __name__ == "__main__":
    asyncio.run(test_keyword_trends_params())
