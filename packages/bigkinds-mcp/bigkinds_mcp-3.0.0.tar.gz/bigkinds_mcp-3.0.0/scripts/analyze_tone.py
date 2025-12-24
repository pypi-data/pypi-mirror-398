"""언론사별 논조 분석 스크립트.

수집된 기사 데이터를 분석하여 언론사별 논조를 비교합니다.

Usage:
    uv run python scripts/analyze_tone.py
"""

import json
import re
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "jung_woosong_articles.json"


def load_articles():
    """수집된 기사 로드."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_keywords(content: str) -> dict:
    """키워드 빈도 분석."""
    # 논조 관련 키워드
    positive_keywords = [
        "복귀", "기대", "인기", "호평", "성공", "화제", "관심", "기대작",
        "명품", "열연", "호응", "주목", "연기력", "배우"
    ]
    negative_keywords = [
        "논란", "스캔들", "사생아", "혼외자", "불륜", "책임", "비판",
        "외면", "실망", "비난", "충격", "파문"
    ]
    neutral_keywords = [
        "출연", "드라마", "촬영", "방송", "제작", "캐스팅", "작품"
    ]

    content_lower = content.lower()

    positive_count = sum(1 for kw in positive_keywords if kw in content_lower)
    negative_count = sum(1 for kw in negative_keywords if kw in content_lower)
    neutral_count = sum(1 for kw in neutral_keywords if kw in content_lower)

    # 키워드별 출현 횟수
    found_positive = [kw for kw in positive_keywords if kw in content_lower]
    found_negative = [kw for kw in negative_keywords if kw in content_lower]
    found_neutral = [kw for kw in neutral_keywords if kw in content_lower]

    return {
        "positive_score": positive_count,
        "negative_score": negative_count,
        "neutral_score": neutral_count,
        "found_positive": found_positive,
        "found_negative": found_negative,
        "found_neutral": found_neutral,
    }


def classify_tone(analysis: dict) -> str:
    """논조 분류."""
    pos = analysis["positive_score"]
    neg = analysis["negative_score"]

    if neg > pos * 1.5:
        return "비판적"
    elif pos > neg * 1.5:
        return "긍정적"
    elif neg > 0 and pos > 0:
        return "균형적"
    else:
        return "중립적"


def extract_first_paragraph(content: str) -> str:
    """첫 문단 추출 (리드문)."""
    paragraphs = content.split("\n")
    for p in paragraphs:
        p = p.strip()
        if len(p) > 50:  # 의미 있는 길이
            return p[:200] + "..." if len(p) > 200 else p
    return content[:200] + "..."


def analyze_scandal_mention(content: str) -> dict:
    """스캔들 언급 방식 분석."""
    scandal_keywords = ["사생아", "혼외자", "문가비", "아들", "스캔들", "논란", "외도"]
    mentions = []

    sentences = re.split(r'[.!?]\s*', content)
    for sent in sentences:
        if any(kw in sent for kw in scandal_keywords):
            mentions.append(sent.strip()[:100])

    return {
        "scandal_mentioned": len(mentions) > 0,
        "mention_count": len(mentions),
        "sample_mentions": mentions[:3],
    }


def main():
    """메인 분석 함수."""
    data = load_articles()

    print("=" * 70)
    print(f"언론사별 논조 분석 리포트")
    print(f"키워드: {data['keyword']}")
    print(f"기간: {data['date_range']}")
    print(f"수집 시점: {data['collected_at']}")
    print(f"분석 대상: {data['total_collected']}개 언론사")
    print("=" * 70)

    results = []

    for article in data["articles"]:
        publisher = article["publisher"]
        title = article["title"]
        content = article["content"]

        # 키워드 분석
        kw_analysis = analyze_keywords(content)
        tone = classify_tone(kw_analysis)

        # 스캔들 언급 분석
        scandal_analysis = analyze_scandal_mention(content)

        # 리드문
        lead = extract_first_paragraph(content)

        results.append({
            "publisher": publisher,
            "title": title,
            "tone": tone,
            "content_length": len(content),
            "kw_analysis": kw_analysis,
            "scandal": scandal_analysis,
            "lead": lead,
        })

    # 논조별 그룹핑
    tone_groups = {}
    for r in results:
        tone = r["tone"]
        if tone not in tone_groups:
            tone_groups[tone] = []
        tone_groups[tone].append(r["publisher"])

    print("\n### 논조별 분류 ###\n")
    for tone, publishers in tone_groups.items():
        print(f"[{tone}] ({len(publishers)}개)")
        for p in publishers:
            print(f"  - {p}")
        print()

    print("\n### 상세 분석 ###\n")
    for r in sorted(results, key=lambda x: x["content_length"], reverse=True):
        print("-" * 60)
        print(f"언론사: {r['publisher']}")
        print(f"제목: {r['title']}")
        print(f"논조: {r['tone']}")
        print(f"분량: {r['content_length']}자")
        print(f"\n긍정 키워드: {', '.join(r['kw_analysis']['found_positive']) or '없음'}")
        print(f"부정 키워드: {', '.join(r['kw_analysis']['found_negative']) or '없음'}")
        print(f"\n스캔들 언급: {'있음' if r['scandal']['scandal_mentioned'] else '없음'} ({r['scandal']['mention_count']}회)")
        if r["scandal"]["sample_mentions"]:
            print("  샘플:")
            for m in r["scandal"]["sample_mentions"]:
                print(f"    - \"{m}...\"")
        print(f"\n리드문: {r['lead']}")
        print()

    # 요약 통계
    print("\n### 요약 ###\n")
    scandal_mentioned = sum(1 for r in results if r["scandal"]["scandal_mentioned"])
    avg_length = sum(r["content_length"] for r in results) // len(results) if results else 0

    print(f"총 분석 언론사: {len(results)}개")
    print(f"평균 기사 길이: {avg_length}자")
    print(f"스캔들 언급 언론사: {scandal_mentioned}개 ({scandal_mentioned/len(results)*100:.1f}%)")
    print(f"\n논조 분포:")
    for tone, publishers in tone_groups.items():
        print(f"  - {tone}: {len(publishers)}개 ({len(publishers)/len(results)*100:.1f}%)")


if __name__ == "__main__":
    main()
