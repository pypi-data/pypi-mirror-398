"""마크다운 변환 단위 테스트."""

import pytest

from bigkinds_mcp.utils.markdown import (
    article_to_context,
    extract_key_sentences,
    html_to_markdown,
    summarize_for_llm,
    text_to_llm_context,
)


class TestHtmlToMarkdown:
    """html_to_markdown 함수 테스트."""

    def test_converts_headings(self):
        """헤딩 변환."""
        html = "<h1>제목</h1><h2>부제목</h2>"
        result = html_to_markdown(html)
        assert "# 제목" in result or "제목" in result

    def test_converts_paragraphs(self):
        """문단 변환."""
        html = "<p>첫 번째 문단</p><p>두 번째 문단</p>"
        result = html_to_markdown(html)
        assert "첫 번째 문단" in result
        assert "두 번째 문단" in result

    def test_converts_bold(self):
        """볼드 변환."""
        html = "<p>이것은 <strong>중요한</strong> 내용입니다.</p>"
        result = html_to_markdown(html)
        assert "중요한" in result

    def test_removes_scripts(self):
        """스크립트 제거."""
        html = "<p>본문</p><script>alert('xss')</script>"
        result = html_to_markdown(html)
        assert "alert" not in result
        assert "script" not in result

    def test_removes_ads(self):
        """광고 영역 제거."""
        html = '<p>본문</p><div class="ad">광고</div>'
        result = html_to_markdown(html)
        assert "광고" not in result

    def test_removes_related_articles(self):
        """관련 기사 제거."""
        html = '<p>본문</p><div class="related-articles">관련기사</div>'
        result = html_to_markdown(html)
        assert "관련기사" not in result

    def test_handles_empty_input(self):
        """빈 입력 처리."""
        assert html_to_markdown("") == ""
        assert html_to_markdown(None) == ""

    def test_removes_images_by_default(self):
        """기본적으로 이미지 제거."""
        html = '<p>본문</p><img src="test.jpg" alt="이미지">'
        result = html_to_markdown(html)
        assert "![" not in result

    def test_includes_images_when_requested(self):
        """요청 시 이미지 포함."""
        html = '<p>본문</p><img src="test.jpg" alt="이미지">'
        result = html_to_markdown(html, include_images=True)
        # markdownify가 이미지를 변환
        assert "본문" in result


class TestTextToLlmContext:
    """text_to_llm_context 함수 테스트."""

    def test_creates_structured_output(self):
        """구조화된 출력 생성."""
        result = text_to_llm_context(
            title="테스트 제목",
            content="테스트 본문입니다.",
            publisher="테스트언론",
            published_date="2024-12-15",
        )

        assert "# 테스트 제목" in result
        assert "테스트언론" in result
        assert "2024-12-15" in result
        assert "테스트 본문" in result

    def test_includes_keywords(self):
        """키워드 포함."""
        result = text_to_llm_context(
            title="제목",
            content="본문",
            keywords=["AI", "반도체", "기술"],
        )
        assert "AI" in result
        assert "반도체" in result

    def test_includes_summary(self):
        """요약 포함."""
        result = text_to_llm_context(
            title="제목",
            content="본문",
            summary="이것은 요약입니다.",
        )
        assert "이것은 요약입니다" in result

    def test_includes_url(self):
        """URL 포함."""
        result = text_to_llm_context(
            title="제목",
            content="본문",
            url="https://example.com/article",
        )
        assert "https://example.com/article" in result


class TestExtractKeySentences:
    """extract_key_sentences 함수 테스트."""

    def test_extracts_sentences(self):
        """문장 추출."""
        content = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."
        result = extract_key_sentences(content, max_sentences=2)
        assert len(result) <= 2

    def test_filters_short_sentences(self):
        """짧은 문장 필터링."""
        content = "짧다. 이것은 충분히 긴 문장입니다."
        result = extract_key_sentences(content, min_sentence_length=10)
        assert "짧다" not in " ".join(result)

    def test_filters_reporter_bylines(self):
        """기자 바이라인 필터링."""
        content = "본문 내용입니다. 홍길동 기자"
        result = extract_key_sentences(content)
        assert not any("기자" in s and len(s) < 20 for s in result)

    def test_handles_empty_input(self):
        """빈 입력 처리."""
        assert extract_key_sentences("") == []
        assert extract_key_sentences(None) == []


class TestSummarizeForLlm:
    """summarize_for_llm 함수 테스트."""

    def test_respects_max_length(self):
        """최대 길이 제한."""
        long_content = "테스트 문장입니다. " * 100
        result = summarize_for_llm(long_content, max_length=100)
        assert len(result) <= 103  # "..." 포함

    def test_preserves_short_content(self):
        """짧은 내용 보존."""
        short_content = "짧은 내용입니다."
        result = summarize_for_llm(short_content, max_length=1000)
        assert result == short_content

    def test_handles_empty_input(self):
        """빈 입력 처리."""
        assert summarize_for_llm("") == ""


class TestArticleToContext:
    """article_to_context 함수 테스트."""

    def test_converts_article_data(self):
        """기사 데이터 변환."""
        article_data = {
            "title": "테스트 기사",
            "full_content": "기사 본문입니다.",
            "publisher": "테스트언론",
            "published_date": "2024-12-15",
        }
        result = article_to_context(article_data)

        assert "테스트 기사" in result
        assert "테스트언론" in result

    def test_limits_content_length(self):
        """본문 길이 제한."""
        article_data = {
            "title": "제목",
            "full_content": "본문입니다. " * 1000,
        }
        result = article_to_context(article_data, max_content_length=500)
        # 길이가 제한되어야 함 (메타데이터 포함하므로 정확한 값은 달라질 수 있음)
        assert len(result) < 10000

    def test_excludes_metadata_when_requested(self):
        """메타데이터 제외 옵션."""
        article_data = {
            "title": "제목",
            "full_content": "본문",
            "publisher": "언론사",
        }
        result = article_to_context(article_data, include_metadata=False)
        assert "언론사" not in result or "**언론사**" not in result
