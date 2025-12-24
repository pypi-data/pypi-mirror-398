"""마크다운 변환 모듈 - LLM friendly context 생성."""

import re

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def html_to_markdown(
    html: str,
    include_images: bool = False,
    include_links: bool = True,
    strip_tags: list[str] | None = None,
) -> str:
    """
    HTML을 LLM-friendly 마크다운으로 변환.

    Args:
        html: 변환할 HTML 문자열
        include_images: 이미지 포함 여부
        include_links: 링크 포함 여부
        strip_tags: 제거할 추가 태그 목록

    Returns:
        변환된 마크다운 문자열
    """
    if not html:
        return ""

    # 불필요한 태그 제거
    soup = BeautifulSoup(html, "html.parser")

    # 기본 제거 대상
    remove_selectors = [
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "iframe",
        "noscript",
        ".ad",
        ".advertisement",
        ".ads",
        ".social-share",
        ".share-buttons",
        ".related-articles",
        ".related-news",
        ".recommend",
        ".comment",
        ".comments",
        "#comment",
        "#comments",
        ".author-info",
        ".reporter-info",
        ".copyright",
        ".newsletter",
        ".subscription",
    ]

    if strip_tags:
        remove_selectors.extend(strip_tags)

    for selector in remove_selectors:
        for elem in soup.select(selector):
            elem.decompose()

    # markdownify로 변환
    markdown = md(
        str(soup),
        heading_style="ATX",  # # 스타일 헤딩
        bullets="-",  # 리스트 스타일
        strip=["a"] if not include_links else None,
    )

    # 이미지 제거 (옵션)
    if not include_images:
        markdown = re.sub(r"!\[.*?\]\(.*?\)", "", markdown)

    # 후처리: 정리
    markdown = _clean_markdown(markdown)

    return markdown


def _clean_markdown(text: str) -> str:
    """마크다운 텍스트 정리."""
    # 과도한 공백 줄 제거
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 빈 헤딩 제거
    text = re.sub(r"^#+\s*$", "", text, flags=re.MULTILINE)

    # 앞뒤 공백 제거
    text = text.strip()

    # 연속된 공백 제거
    text = re.sub(r" {2,}", " ", text)

    # 빈 링크 제거
    text = re.sub(r"\[]\(.*?\)", "", text)

    # 빈 줄로 시작하는 리스트 아이템 정리
    text = re.sub(r"^-\s*\n", "", text, flags=re.MULTILINE)

    return text


def text_to_llm_context(
    title: str,
    content: str,
    publisher: str | None = None,
    published_date: str | None = None,
    author: str | None = None,
    url: str | None = None,
    keywords: list[str] | None = None,
    summary: str | None = None,
) -> str:
    """
    기사 정보를 LLM context용 마크다운으로 구조화.

    Args:
        title: 기사 제목
        content: 본문 (텍스트 또는 HTML)
        publisher: 언론사
        published_date: 발행일
        author: 기자
        url: 원본 URL
        keywords: 키워드 목록
        summary: 요약

    Returns:
        구조화된 마크다운 문자열
    """
    parts = []

    # 제목
    parts.append(f"# {title}\n")

    # 메타데이터
    meta_parts = []
    if publisher:
        meta_parts.append(f"**언론사**: {publisher}")
    if published_date:
        meta_parts.append(f"**발행일**: {published_date}")
    if author:
        meta_parts.append(f"**기자**: {author}")

    if meta_parts:
        parts.append(" | ".join(meta_parts) + "\n")

    # 키워드
    if keywords:
        parts.append(f"**키워드**: {', '.join(keywords)}\n")

    # 요약
    if summary:
        parts.append(f"\n> {summary}\n")

    # 구분선
    parts.append("\n---\n")

    # 본문
    # HTML인지 확인
    if content and ("<" in content and ">" in content):
        content = html_to_markdown(content)

    if content:
        parts.append(f"\n{content}\n")

    # 출처
    if url:
        parts.append(f"\n---\n**원문**: {url}")

    return "\n".join(parts)


def extract_key_sentences(
    content: str,
    max_sentences: int = 5,
    min_sentence_length: int = 20,
) -> list[str]:
    """
    본문에서 핵심 문장 추출 (간단한 휴리스틱).

    Args:
        content: 본문 텍스트
        max_sentences: 최대 문장 수
        min_sentence_length: 최소 문장 길이

    Returns:
        핵심 문장 목록
    """
    if not content:
        return []

    # 문장 분리 (한국어 + 영어)
    sentences = re.split(r"(?<=[.!?다요])\s+", content)

    # 필터링
    filtered = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < min_sentence_length:
            continue
        # 광고/관련 없는 문장 필터링
        skip_patterns = [
            r"^기자$",
            r"^[가-힣]+\s*기자$",
            r"^사진\s*=",
            r"^출처\s*:",
            r"^\[.*?\]$",
            r"^©",
            r"무단.*금지",
            r"저작권",
        ]
        if any(re.search(p, sent) for p in skip_patterns):
            continue
        filtered.append(sent)

    # 첫 문장들 우선 (보통 핵심 내용)
    return filtered[:max_sentences]


def summarize_for_llm(
    content: str,
    max_length: int = 1000,
    include_structure: bool = True,
) -> str:
    """
    LLM 컨텍스트 효율을 위한 요약.

    Args:
        content: 본문 텍스트
        max_length: 최대 길이
        include_structure: 구조 유지 여부

    Returns:
        요약된 텍스트
    """
    if not content:
        return ""

    if len(content) <= max_length:
        return content

    # 문단 분리
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    if not paragraphs:
        # 문단이 없으면 단순 자르기
        return content[:max_length] + "..."

    result_parts = []
    current_length = 0

    for para in paragraphs:
        if current_length + len(para) > max_length:
            # 남은 공간이 있으면 일부라도 포함
            remaining = max_length - current_length - 3  # "..." 공간
            if remaining > 50:
                result_parts.append(para[:remaining] + "...")
            break

        result_parts.append(para)
        current_length += len(para) + 2  # 문단 구분자

    return "\n\n".join(result_parts)


def article_to_context(
    article_data: dict,
    max_content_length: int = 2000,
    include_metadata: bool = True,
) -> str:
    """
    기사 데이터를 LLM context 문자열로 변환.

    Args:
        article_data: 기사 정보 딕셔너리
        max_content_length: 최대 본문 길이
        include_metadata: 메타데이터 포함 여부

    Returns:
        LLM-ready 문자열
    """
    title = article_data.get("title", "")
    content = article_data.get("full_content") or article_data.get("content", "")

    # HTML이면 마크다운 변환
    if content and ("<" in content and ">" in content):
        content = html_to_markdown(content)

    # None 체크
    if not content:
        content = ""

    # 길이 제한
    if len(content) > max_content_length:
        content = summarize_for_llm(content, max_content_length)

    if include_metadata:
        return text_to_llm_context(
            title=title,
            content=content,
            publisher=article_data.get("publisher"),
            published_date=article_data.get("published_date"),
            author=article_data.get("author"),
            url=article_data.get("url"),
            keywords=article_data.get("keywords"),
            summary=article_data.get("summary"),
        )
    else:
        if title:
            return f"# {title}\n\n{content}"
        return content
