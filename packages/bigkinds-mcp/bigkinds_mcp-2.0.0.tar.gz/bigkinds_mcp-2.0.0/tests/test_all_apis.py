"""BigKinds 전체 API 테스트 - 계정 정보로 테스트."""

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


async def test_all_apis():
    """전체 API 테스트."""

    user_id = os.getenv("BIGKINDS_USER_ID", "")
    user_password = os.getenv("BIGKINDS_USER_PASSWORD", "")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://www.bigkinds.or.kr",
        "Referer": "https://www.bigkinds.or.kr/v2/news/index.do",
        "X-Requested-With": "XMLHttpRequest",
    }

    results = []

    async with httpx.AsyncClient(
        verify=False,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        # 1. 메인 페이지 접속 (세션 초기화)
        print("=" * 70)
        print("BigKinds API 전체 테스트")
        print("=" * 70)

        await client.get("https://www.bigkinds.or.kr/", headers=headers)
        print("세션 초기화 완료\n")

        # 2. 로그인
        print("-" * 70)
        print("1. 로그인 테스트")
        print("-" * 70)

        login_data = {"userId": user_id, "userPassword": user_password}
        login_resp = await client.post(
            "https://www.bigkinds.or.kr/api/account/signin.do",
            json=login_data,
            headers=headers,
        )

        login_result = login_resp.json() if login_resp.status_code == 200 else {}
        login_success = login_resp.status_code == 200 and login_result.get("userSn")

        if login_success:
            print(f"✅ 로그인 성공 (userSn: {login_result.get('userSn')})")
            results.append(("로그인 API", "✅ 성공", "/api/account/signin.do"))
        else:
            msg = login_result.get("message") or login_result.get("messages", "")
            print(f"❌ 로그인 실패: {msg}")
            results.append(("로그인 API", f"❌ 실패: {msg}", "/api/account/signin.do"))

            if "계정이 잠겨" in msg:
                print("\n⏰ 계정 잠금 상태입니다. 나중에 다시 시도해주세요.")
                return results

        # 3. 공개 API 테스트 - 뉴스 검색
        print("\n" + "-" * 70)
        print("2. 뉴스 검색 API (공개)")
        print("-" * 70)

        search_payload = {
            "indexName": "news",
            "searchKey": "AI",
            "searchKeys": [{}],
            "byLine": "",
            "searchFilterType": "1",
            "searchScopeType": "1",
            "searchSortType": "date",
            "sortMethod": "date",
            "mainTodayPersonYn": "",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "newsIds": [],
            "categoryCodes": [],
            "providerCodes": [],
            "incidentCodes": [],
            "networkNodeType": "",
            "topicOrigin": "",
            "dateCodes": [],
            "editorialIs": False,
            "startNo": 1,
            "resultNumber": 5,
            "isTmUsable": True,
            "isNotTmUsable": False,
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/api/news/search.do",
            json=search_payload,
            headers=headers,
        )

        if resp.status_code == 200:
            result = resp.json()
            total = result.get("resultState", {}).get("totalCnt", 0)
            docs = len(result.get("resultList", []))
            print(f"✅ 성공 - 총 {total}건 중 {docs}개 반환")
            results.append(("뉴스 검색", f"✅ 성공 ({total}건)", "/api/news/search.do"))
        else:
            print(f"❌ 실패 - 상태: {resp.status_code}")
            results.append(("뉴스 검색", f"❌ 실패 ({resp.status_code})", "/api/news/search.do"))

        # 4. 오늘의 이슈 API
        print("\n" + "-" * 70)
        print("3. 오늘의 이슈 API")
        print("-" * 70)

        resp = await client.get(
            "https://www.bigkinds.or.kr/search/trendReportData2.do",
            params={"SEARCH_DATE": "2024-12-15", "category": "전체"},
            headers=headers,
        )

        if resp.status_code == 200:
            result = resp.json()
            issues = result.get("issueList", [])
            print(f"✅ 성공 - {len(issues)}개 이슈")
            if issues:
                print(f"   예시: {issues[0].get('keyword', '')[:30]}")
            results.append(("오늘의 이슈", f"✅ 성공 ({len(issues)}개)", "/search/trendReportData2.do"))
        else:
            print(f"❌ 실패 - 상태: {resp.status_code}")
            results.append(("오늘의 이슈", f"❌ 실패 ({resp.status_code})", "/search/trendReportData2.do"))

        # 5. 키워드 트렌드 API (로그인 필요)
        print("\n" + "-" * 70)
        print("4. 키워드 트렌드 API (로그인 필요)")
        print("-" * 70)

        trends_payload = {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "interval": 1,
            "providerCode": "",
            "categoryCode": "",
            "incidentCode": "",
            "isTmUsable": True,
            "isNotTmUsable": False,
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/api/analysis/keywordTrends.do",
            json=trends_payload,
            headers=headers,
        )

        if resp.status_code == 200:
            result = resp.json()
            root = result.get("root", [])
            if root:
                data_points = len(root[0].get("data", []))
                print(f"✅ 성공 - {len(root)}개 키워드, {data_points}개 데이터포인트")
                results.append(("키워드 트렌드", f"✅ 성공 ({data_points}포인트)", "/api/analysis/keywordTrends.do"))
            else:
                print(f"⚠️  성공 (빈 결과) - 응답 키: {list(result.keys())}")
                results.append(("키워드 트렌드", "⚠️ 빈 결과", "/api/analysis/keywordTrends.do"))
        else:
            print(f"❌ 실패 - 상태: {resp.status_code}")
            results.append(("키워드 트렌드", f"❌ 실패 ({resp.status_code})", "/api/analysis/keywordTrends.do"))

        # 6. 연관어 분석 API (로그인 필요)
        print("\n" + "-" * 70)
        print("5. 연관어 분석 API (로그인 필요)")
        print("-" * 70)

        related_payload = {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "maxNewsCount": 100,
            "resultNumber": 50,
            "analysisType": "relational_word",
            "sortMethod": "score",
            "startNo": 1,
            "isTmUsable": True,
            "searchKey": "AI",       # 필수!
            "indexName": "news",      # 필수!
            "providerCode": "",
            "categoryCode": "",
            "incidentCode": "",
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/api/analysis/relationalWords.do",
            json=related_payload,
            headers=headers,
        )

        if resp.status_code == 200:
            result = resp.json()
            topics = result.get("topics", {}).get("data", [])
            doc_count = result.get("news", {}).get("documentCount", 0)
            if topics:
                print(f"✅ 성공 - {len(topics)}개 연관어, {doc_count}개 문서 분석")
                print(f"   Top 3: {', '.join([t.get('name', '') for t in topics[:3]])}")
                results.append(("연관어 분석", f"✅ 성공 ({len(topics)}개)", "/api/analysis/relationalWords.do"))
            else:
                print(f"⚠️  성공 (빈 결과) - 응답 키: {list(result.keys())}")
                results.append(("연관어 분석", "⚠️ 빈 결과", "/api/analysis/relationalWords.do"))
        elif resp.status_code == 500:
            print(f"❌ 실패 - 서버 오류 (500)")
            print(f"   {resp.text[:200]}")
            results.append(("연관어 분석", "❌ 서버오류 (500)", "/api/analysis/relationalWords.do"))
        else:
            print(f"❌ 실패 - 상태: {resp.status_code}")
            results.append(("연관어 분석", f"❌ 실패 ({resp.status_code})", "/api/analysis/relationalWords.do"))

        # 7. 관계도 분석 API (로그인 필요)
        print("\n" + "-" * 70)
        print("6. 관계도 분석 API (로그인 필요)")
        print("-" * 70)

        network_payload = {
            "keyword": "AI",
            "startDate": "2024-12-01",
            "endDate": "2024-12-10",
            "maxNewsCount": 100,
            "sectionDiv": 1000,
            "resultNo": 50,
            "normalization": 10,
            "isTmUsable": True,
            "isNotTmUsable": False,
            "searchFtr": "1",
            "searchScope": "1",
            "providerCode": "",
            "categoryCode": "",
            "incidentCode": "",
            "keywordFilterJson": "",
        }

        resp = await client.post(
            "https://www.bigkinds.or.kr/news/getNetworkDataAnalysis.do",
            json=network_payload,
            headers=headers,
        )

        if resp.status_code == 200:
            result = resp.json()
            nodes = result.get("nodes", [])
            links = result.get("links", [])
            if nodes or links:
                print(f"✅ 성공 - {len(nodes)}개 노드, {len(links)}개 링크")
                results.append(("관계도 분석", f"✅ 성공 ({len(nodes)}노드)", "/news/getNetworkDataAnalysis.do"))
            else:
                print(f"⚠️  성공 (빈 결과) - 응답 키: {list(result.keys())}")
                results.append(("관계도 분석", "⚠️ 빈 결과", "/news/getNetworkDataAnalysis.do"))
        else:
            print(f"❌ 실패 - 상태: {resp.status_code}")
            results.append(("관계도 분석", f"❌ 실패 ({resp.status_code})", "/news/getNetworkDataAnalysis.do"))

        # 결과 요약
        print("\n" + "=" * 70)
        print("테스트 결과 요약")
        print("=" * 70)
        print(f"{'API 이름':<20} {'결과':<25} {'엔드포인트'}")
        print("-" * 70)
        for name, status, endpoint in results:
            print(f"{name:<20} {status:<25} {endpoint}")

        # 분류
        print("\n" + "-" * 70)
        success = [r for r in results if "✅" in r[1]]
        warning = [r for r in results if "⚠️" in r[1]]
        failed = [r for r in results if "❌" in r[1]]

        print(f"✅ 정상 작동: {len(success)}개")
        for r in success:
            print(f"   - {r[0]}")

        if warning:
            print(f"⚠️  빈 결과: {len(warning)}개")
            for r in warning:
                print(f"   - {r[0]}")

        if failed:
            print(f"❌ 실패: {len(failed)}개")
            for r in failed:
                print(f"   - {r[0]}")

        return results


if __name__ == "__main__":
    asyncio.run(test_all_apis())
