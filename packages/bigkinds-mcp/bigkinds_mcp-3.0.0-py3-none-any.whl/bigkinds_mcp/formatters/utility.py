"""
Utility tools formatters (compare_keywords, smart_sample, export_all_articles).
"""

from typing import Any
from . import (
    format_number,
    create_progress_bar,
    add_footer,
)


def format_compare_keywords_basic(result: dict[str, Any]) -> str:
    """
    compare_keywords 결과를 마크다운으로 포맷.

    Args:
        result: compare_keywords의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    keywords = result.get("keywords", [])
    comparisons = result.get("comparisons", [])

    # 헤더
    keyword_list = ", ".join(keywords)
    md = f"# 🔄 키워드 비교: {keyword_list}\n\n"
    md += f"**기간**: {result.get('start_date')} ~ {result.get('end_date')}  \n"
    md += f"**비교 키워드**: {len(keywords)}개\n\n"

    if not comparisons:
        md += "비교 데이터가 없습니다.\n"
        return add_footer(md)

    # 순위
    sorted_keywords = sorted(
        comparisons, key=lambda x: x.get("total_count", 0), reverse=True
    )

    md += "## 순위\n"

    for idx, comp in enumerate(sorted_keywords, 1):
        keyword = comp.get("keyword", "")
        total = comp.get("total_count", 0)

        # 순위 이모지
        if idx == 1:
            rank = "🥇"
        elif idx == 2:
            rank = "🥈"
        elif idx == 3:
            rank = "🥉"
        else:
            rank = f"{idx}."

        md += f"{rank} **{keyword}**: {format_number(total)}건\n"

    # 점유율 시각화
    total_all = sum(c.get("total_count", 0) for c in comparisons)

    if total_all > 0:
        md += "\n## 점유율\n"

        for comp in comparisons:
            keyword = comp.get("keyword", "")
            total = comp.get("total_count", 0)
            ratio = (total / total_all) * 100

            bar = create_progress_bar(total, total_all, width=25)
            md += f"- {keyword}: {ratio:.0f}% {bar}\n"

    # 가장 핫한 키워드 (증가율 기반)
    md += "\n"

    if sorted_keywords:
        hottest = sorted_keywords[0]
        md += f"**가장 핫한 키워드**: {hottest.get('keyword')} "
        md += f"({format_number(hottest.get('total_count', 0))}건)\n"

    return add_footer(md, "일별 추이 데이터는 `response_format=\"full\"` 사용")


def format_smart_sample_basic(result: dict[str, Any]) -> str:
    """
    smart_sample 결과를 마크다운으로 포맷.

    Args:
        result: smart_sample의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    keyword = result.get("keyword", "검색어")
    total_count = result.get("total_count", 0)
    sample_size = result.get("sample_size", 0)
    samples = result.get("samples", [])

    # 헤더
    md = f"# 🎲 \"{keyword}\" 샘플링 결과\n\n"
    md += f"**기간**: {result.get('start_date')} ~ {result.get('end_date')}  \n"
    md += f"**전체**: {format_number(total_count)}건  \n"
    md += f"**샘플**: {format_number(sample_size)}건  \n"
    md += f"**전략**: {result.get('strategy', 'stratified')}\n\n"

    # 커버리지
    coverage = result.get("coverage", {})
    if coverage:
        coverage_pct = coverage.get("coverage_percentage", 0)
        md += f"**커버리지**: {coverage_pct:.1f}%\n\n"

    # 샘플 기사 (상위 5개만 미리보기)
    if samples:
        md += "## 샘플 기사 (미리보기)\n\n"

        for idx, article in enumerate(samples[:5], 1):
            title = article.get("title", "제목 없음")
            date = article.get("date", "")
            provider = article.get("provider", "")

            md += f"{idx}. **{title}** - {provider} ({date})\n"

        if len(samples) > 5:
            md += f"\n...외 {len(samples) - 5}건\n"

    return add_footer(md, "전체 샘플 데이터는 `response_format=\"full\"` 사용")


def format_export_basic(result: dict[str, Any]) -> str:
    """
    export_all_articles 결과를 마크다운으로 포맷.

    Args:
        result: export_all_articles의 전체 결과

    Returns:
        마크다운 문자열
    """
    if not result.get("success", True):
        return str(result)

    keyword = result.get("keyword", "검색어")
    exported_count = result.get("exported_count", 0)
    output_path = result.get("output_path", "")
    output_format = result.get("output_format", "json")

    # 헤더
    md = f"# 💾 \"{keyword}\" 내보내기 완료\n\n"
    md += f"**파일 경로**: `{output_path}`  \n"
    md += f"**형식**: {output_format.upper()}  \n"
    md += f"**기사 수**: {format_number(exported_count)}건\n\n"

    # 다음 단계 안내
    md += "## 다음 단계\n\n"

    if output_format == "json":
        md += "```python\n"
        md += "import json\n\n"
        md += f'with open("{output_path}", "r", encoding="utf-8") as f:\n'
        md += "    data = json.load(f)\n"
        md += "    print(f'기사 수: {len(data)}')\n"
        md += "```\n\n"
    elif output_format == "csv":
        md += "```python\n"
        md += "import pandas as pd\n\n"
        md += f'df = pd.read_csv("{output_path}")\n'
        md += "print(df.head())\n"
        md += "```\n\n"

    # 분석 코드 템플릿 힌트
    md += "💡 **분석 코드 템플릿**이 필요하면 `response_format=\"full\"`을 사용하세요.  \n"
    md += "자동 생성된 Python 분석 스크립트가 포함됩니다.\n"

    return md
