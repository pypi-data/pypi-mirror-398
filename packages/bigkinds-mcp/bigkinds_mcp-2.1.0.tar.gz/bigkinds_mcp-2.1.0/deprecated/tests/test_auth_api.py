"""BigKinds 로그인 API 테스트 - 브라우저 없이 인증 가능 여부 확인."""

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


async def test_login_api():
    """
    BigKinds 로그인 API 테스트.

    테스트 목적:
    1. 브라우저 없이 로그인 가능한지 확인
    2. 세션 쿠키 획득 가능한지 확인
    3. 세션으로 시각화 API 호출 가능한지 확인
    """

    # 환경변수에서 테스트 계정 정보 가져오기
    user_id = os.getenv("BIGKINDS_USER_ID", "")
    user_password = os.getenv("BIGKINDS_USER_PASSWORD", "")

    if not user_id or not user_password:
        print("⚠️  BIGKINDS_USER_ID, BIGKINDS_USER_PASSWORD 환경변수 필요")
        print("   export BIGKINDS_USER_ID='your_email'")
        print("   export BIGKINDS_USER_PASSWORD='your_password'")

        # 계정 없이도 API 구조 테스트는 가능
        print("\n📋 계정 없이 API 엔드포인트 테스트 진행...")
        await test_endpoints_without_auth()
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "Origin": "https://www.bigkinds.or.kr",
        "Referer": "https://www.bigkinds.or.kr/v2/member/login.do",
        "X-Requested-With": "XMLHttpRequest",
    }

    async with httpx.AsyncClient(
        verify=False,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        # 1. 먼저 메인 페이지 접속 (세션 쿠키 초기화)
        print("1️⃣  메인 페이지 접속...")
        main_resp = await client.get("https://www.bigkinds.or.kr/", headers=headers)
        print(f"   상태: {main_resp.status_code}")
        print(f"   쿠키: {dict(client.cookies)}")

        # 2. 로그인 API 호출
        print("\n2️⃣  로그인 API 호출...")
        login_data = {
            "userId": user_id,
            "userPassword": user_password,
        }

        # 두 가지 로그인 엔드포인트 시도
        login_endpoints = [
            "/api/account/signin.do",
            "/api/account/signin2023.do",
        ]

        login_success = False
        for endpoint in login_endpoints:
            url = f"https://www.bigkinds.or.kr{endpoint}"
            print(f"   시도: {endpoint}")

            try:
                login_resp = await client.post(
                    url,
                    json=login_data,
                    headers=headers,
                )
                print(f"   상태: {login_resp.status_code}")
                print(f"   응답: {login_resp.text[:500] if login_resp.text else '(empty)'}")

                if login_resp.status_code == 200:
                    try:
                        result = login_resp.json()
                        print(f"   JSON: {result}")
                        if result.get("success") or result.get("result") == "success":
                            login_success = True
                            print("   ✅ 로그인 성공!")
                            break
                    except Exception as e:
                        print(f"   JSON 파싱 오류: {e}")
            except Exception as e:
                print(f"   오류: {e}")

        if not login_success:
            print("\n❌ 로그인 실패")
            return

        # 3. 로그인 후 쿠키 확인
        print("\n3️⃣  로그인 후 쿠키...")
        print(f"   쿠키: {dict(client.cookies)}")

        # 4. 시각화 API 테스트
        print("\n4️⃣  시각화 API 테스트...")
        await test_visualization_apis(client, headers)


async def test_endpoints_without_auth():
    """인증 없이 API 엔드포인트 접근 테스트."""

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "Origin": "https://www.bigkinds.or.kr",
        "Referer": "https://www.bigkinds.or.kr/v2/news/index.do",
        "X-Requested-With": "XMLHttpRequest",
    }

    endpoints = [
        # 로그인 엔드포인트 (401/403 예상)
        ("POST", "/api/account/signin.do", {"userId": "", "userPassword": ""}),

        # 시각화 API (401/403 예상)
        ("POST", "/api/analysis/keywordTrends.do", {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "interval": 1,
        }),
        ("POST", "/api/analysis/relationalWords.do", {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "maxNewsCount": 100,
            "resultNumber": 50,
            "analysisType": "relational_word",
        }),
        ("POST", "/news/getNetworkDataAnalysis.do", {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "maxNewsCount": 100,
            "sectionDiv": 1000,
            "resultNo": 50,
        }),

        # 공개 API (정상 작동 예상)
        ("POST", "/api/news/search.do", {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "pageInfo": {"page": 1, "size": 10},
            "sortMethod": "date",
        }),
    ]

    async with httpx.AsyncClient(
        verify=False,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        # 메인 페이지 먼저 접속
        await client.get("https://www.bigkinds.or.kr/", headers=headers)

        for method, path, data in endpoints:
            url = f"https://www.bigkinds.or.kr{path}"
            print(f"\n📡 {method} {path}")

            try:
                if method == "POST":
                    resp = await client.post(url, json=data, headers=headers)
                else:
                    resp = await client.get(url, headers=headers)

                print(f"   상태: {resp.status_code}")

                # 응답 내용 요약
                text = resp.text[:300] if resp.text else "(empty)"
                if resp.status_code == 200:
                    try:
                        result = resp.json()
                        if isinstance(result, dict):
                            keys = list(result.keys())[:5]
                            print(f"   응답 키: {keys}")
                            if "message" in result:
                                print(f"   메시지: {result['message']}")
                        else:
                            print(f"   응답: {type(result)}")
                    except Exception:
                        print(f"   응답: {text}")
                else:
                    print(f"   응답: {text}")

            except Exception as e:
                print(f"   오류: {e}")


async def test_visualization_apis(client: httpx.AsyncClient, headers: dict):
    """로그인된 세션으로 시각화 API 테스트."""

    # 키워드 트렌드 API
    print("\n   📊 키워드 트렌드 API...")
    try:
        resp = await client.post(
            "https://www.bigkinds.or.kr/api/analysis/keywordTrends.do",
            json={
                "keyword": "AI",
                "startDate": "2024-12-01",
                "endDate": "2024-12-10",
                "interval": 1,
            },
            headers=headers,
        )
        print(f"      상태: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            print(f"      응답 키: {list(result.keys())[:5]}")
            if "root" in result:
                print(f"      데이터 포인트: {len(result.get('root', []))}")
    except Exception as e:
        print(f"      오류: {e}")

    # 연관어 분석 API
    print("\n   🔗 연관어 분석 API...")
    try:
        resp = await client.post(
            "https://www.bigkinds.or.kr/api/analysis/relationalWords.do",
            json={
                "keyword": "AI",
                "startDate": "2024-12-01",
                "endDate": "2024-12-10",
                "maxNewsCount": 100,
                "resultNumber": 50,
                "analysisType": "relational_word",
                "startNo": 0,
            },
            headers=headers,
        )
        print(f"      상태: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            print(f"      응답 키: {list(result.keys())[:5]}")
            if "topics" in result:
                topics = result.get("topics", {}).get("data", [])
                print(f"      연관어 수: {len(topics)}")
    except Exception as e:
        print(f"      오류: {e}")

    # 관계도 분석 API
    print("\n   🕸️  관계도 분석 API...")
    try:
        resp = await client.post(
            "https://www.bigkinds.or.kr/news/getNetworkDataAnalysis.do",
            json={
                "keyword": "AI",
                "startDate": "2024-12-01",
                "endDate": "2024-12-10",
                "maxNewsCount": 100,
                "sectionDiv": 1000,
                "resultNo": 50,
                "normalization": 10,
            },
            headers=headers,
        )
        print(f"      상태: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            print(f"      응답 키: {list(result.keys())[:5]}")
            if "nodes" in result:
                print(f"      노드 수: {len(result.get('nodes', []))}")
            if "links" in result:
                print(f"      링크 수: {len(result.get('links', []))}")
    except Exception as e:
        print(f"      오류: {e}")


if __name__ == "__main__":
    asyncio.run(test_login_api())
