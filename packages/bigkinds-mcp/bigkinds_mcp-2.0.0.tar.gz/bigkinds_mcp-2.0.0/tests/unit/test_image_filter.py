"""이미지 필터 단위 테스트."""

import pytest

from bigkinds_mcp.utils.image_filter import (
    ImageFilter,
    filter_meaningful_images,
    get_main_image,
)


class TestImageFilter:
    """ImageFilter 클래스 테스트."""

    @pytest.fixture
    def filter(self):
        return ImageFilter()

    def test_filters_ad_urls(self, filter):
        """광고 URL 필터링."""
        ad_urls = [
            "https://ads.example.com/banner.jpg",
            "https://example.com/doubleclick/ad.jpg",
            "https://googlesyndication.com/ad.jpg",
            "https://adservice.google.com/img.jpg",
        ]
        for url in ad_urls:
            assert not filter.is_meaningful(url), f"Should filter: {url}"

    def test_filters_logo_urls(self, filter):
        """로고/아이콘 URL 필터링."""
        logo_urls = [
            "https://news.com/logo.png",
            "https://news.com/icon/share.png",
            "https://news.com/favicon.ico",
            "https://news.com/button_submit.png",
        ]
        for url in logo_urls:
            assert not filter.is_meaningful(url), f"Should filter: {url}"

    def test_filters_tracking_pixels(self, filter):
        """트래킹 픽셀 필터링."""
        tracking_urls = [
            "https://tracker.com/pixel.gif",
            "https://example.com/beacon.gif",
            "https://example.com/1x1.gif",
            "https://example.com/spacer.gif",
        ]
        for url in tracking_urls:
            assert not filter.is_meaningful(url), f"Should filter: {url}"

    def test_filters_social_buttons(self, filter):
        """소셜 버튼 필터링."""
        social_urls = [
            "https://example.com/facebook_btn.png",
            "https://example.com/twitter_share.png",
            "https://example.com/kakao_btn.png",
            "https://example.com/share_buttons.png",
        ]
        for url in social_urls:
            assert not filter.is_meaningful(url), f"Should filter: {url}"

    def test_filters_file_extensions(self, filter):
        """파일 확장자 필터링."""
        bad_extensions = [
            "https://example.com/icon.gif",
            "https://example.com/logo.svg",
            "https://example.com/favicon.ico",
        ]
        for url in bad_extensions:
            assert not filter.is_meaningful(url), f"Should filter: {url}"

    def test_filters_common_paths(self, filter):
        """공통 경로 패턴 필터링."""
        common_paths = [
            "https://news.com/common/header.jpg",
            "https://news.com/resource/bg.jpg",
            "https://news.com/assets/icon.png",
            "https://news.com/bi/logo.png",
        ]
        for url in common_paths:
            assert not filter.is_meaningful(url), f"Should filter: {url}"

    def test_passes_meaningful_urls(self, filter):
        """의미있는 URL 통과."""
        good_urls = [
            "https://news.com/img/2024/12/15/article-main.jpg",
            "https://news.com/photo/2024121512345678abcd.jpg",
        ]
        for url in good_urls:
            # 캡션이 있거나 메인 이미지인 경우 통과
            assert filter.is_meaningful(url, caption="기사 이미지", is_main=True), f"Should pass: {url}"

    def test_main_image_more_lenient(self, filter):
        """메인 이미지는 더 관대하게 처리."""
        # 메인 이미지는 블랙리스트 아니면 통과
        url = "https://news.com/img/article.jpg"
        assert filter.is_meaningful(url, is_main=True)

    def test_caption_increases_trust(self, filter):
        """캡션이 있으면 신뢰도 증가."""
        url = "https://news.com/img/photo.jpg"
        assert filter.is_meaningful(url, caption="기자 촬영 사진")


class TestFilterImages:
    """filter_meaningful_images 함수 테스트."""

    def test_filters_bad_images(self, sample_images):
        """나쁜 이미지 필터링."""
        result = filter_meaningful_images(sample_images)

        # 광고, 로고, 트래커 등은 필터링되어야 함
        urls = [img["url"] for img in result]
        assert not any("ads." in url for url in urls)
        assert not any("logo" in url for url in urls)
        assert not any("pixel" in url for url in urls)

    def test_respects_max_images(self, sample_images):
        """최대 이미지 수 제한."""
        result = filter_meaningful_images(sample_images, max_images=2)
        assert len(result) <= 2

    def test_prioritizes_main_image(self, sample_images):
        """메인 이미지 우선."""
        result = filter_meaningful_images(sample_images)
        if result:
            # 첫 번째가 메인 이미지여야 함
            assert result[0].get("is_main", False) or result[0].get("caption")


class TestGetMainImage:
    """get_main_image 함수 테스트."""

    def test_returns_main_image(self, sample_images):
        """메인 이미지 반환."""
        result = get_main_image(sample_images)
        if result:
            assert result.get("is_main", False) or "main" in result.get("url", "")

    def test_returns_none_for_empty(self):
        """빈 목록에 대해 None 반환."""
        assert get_main_image([]) is None

    def test_returns_none_for_all_bad(self):
        """모두 필터링되면 None 반환."""
        bad_images = [
            {"url": "https://ads.com/banner.jpg", "is_main": False},
            {"url": "https://tracker.com/pixel.gif", "is_main": False},
        ]
        assert get_main_image(bad_images) is None
