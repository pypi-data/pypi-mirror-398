"""이미지 필터링 모듈 - 광고/로고 제거, 의미있는 이미지만 추출."""

import re
from urllib.parse import urlparse


class ImageFilter:
    """공격적인 이미지 필터링 - 의미있는 콘텐츠 이미지만 통과."""

    # URL 패턴 블랙리스트 (공격적 필터링)
    BLACKLIST_PATTERNS = [
        # 광고 네트워크
        r"ad[sx]?\.",
        r"doubleclick",
        r"googlesyndication",
        r"googleadservices",
        r"adservice",
        r"adsystem",
        r"adnxs",
        r"criteo",
        r"taboola",
        r"outbrain",
        r"moat",
        r"adsrvr",
        r"pubmatic",
        r"rubiconproject",
        # 트래킹/분석
        r"pixel",
        r"beacon",
        r"tracker",
        r"analytics",
        r"1x1",
        r"spacer",
        r"blank\.",
        r"transparent\.",
        r"clear\.",
        # 아이콘/로고/버튼
        r"logo",
        r"icon",
        r"favicon",
        r"button",
        r"btn[_-]",
        r"nav[_-]",
        r"menu[_-]",
        r"arrow",
        r"bullet",
        r"check",
        r"close",
        r"search",
        # 소셜 미디어 버튼
        r"facebook.*btn",
        r"facebook.*button",
        r"facebook.*share",
        r"twitter.*btn",
        r"twitter.*share",
        r"kakao.*btn",
        r"kakao.*share",
        r"naver.*btn",
        r"naver.*share",
        r"band.*share",
        r"social[_-]",
        r"share[_-]",
        # 플레이스홀더/기본 이미지
        r"placeholder",
        r"default[_-]",
        r"no[_-]?image",
        r"no[_-]?photo",
        r"empty",
        r"dummy",
        r"sample",
        # 배너/광고 관련
        r"banner",
        r"promo",
        r"sponsor",
        r"advert",
        r"commercial",
        r"popup",
        r"layer",
        # UI 요소
        r"sprite",
        r"bg[_-]",
        r"background",
        r"pattern",
        r"texture",
        r"gradient",
        r"shadow",
        r"border",
        # 썸네일/작은 이미지 (언론사 로고일 가능성)
        r"thumb[_-]?s",
        r"thumbnail[_-]?s",
        r"_s\.",
        r"_xs\.",
        r"_small\.",
        r"_tiny\.",
        r"mini[_-]",
        # 특수 파일
        r"\.gif$",
        r"\.svg$",
        r"\.ico$",
        r"\.webp$",  # 대부분 아이콘/로고
        # 한국 언론사 공통 패턴
        r"/bi/",
        r"/ci/",
        r"/common/",
        r"/comm/",
        r"/resource/",
        r"/assets/",
        r"/static/img/",
        r"/images/common/",
        r"/images/icon/",
        r"/images/btn/",
        r"/img/common/",
        r"/img/icon/",
        r"/img/btn/",
        r"sitefiles",
        r"section[_-]?image",
    ]

    # 언론사별 로고 도메인/경로 패턴
    PUBLISHER_LOGO_PATTERNS = [
        # 주요 언론사 로고 경로
        r"img\.hani\.co\.kr.*logo",
        r"image\.chosun\.com/sitefiles",
        r"www\.mk\.co\.kr/resources",
        r"image\.kmib\.co\.kr.*logo",
        r"img\.seoul\.co\.kr.*logo",
        r"img\.hankyung\.com.*logo",
        r"img\.mt\.co\.kr.*logo",
        r"img\.sedaily\.com.*logo",
        r"img\.etoday\.co\.kr.*logo",
        r"image\.newsis\.com.*logo",
        # 네이버 뉴스 공통
        r"mimgnews\.pstatic\.net.*logo",
        r"imgnews\.pstatic\.net.*logo",
    ]

    # 캡션에서 광고 감지 패턴
    CAPTION_BLACKLIST = [
        r"광고",
        r"배너",
        r"제공",
        r"후원",
        r"협찬",
        r"sponsored",
        r"advertisement",
        r"프로모션",
    ]

    def __init__(self):
        """필터 초기화."""
        self.blacklist_regex = re.compile(
            "|".join(self.BLACKLIST_PATTERNS), re.IGNORECASE
        )
        self.publisher_logo_regex = re.compile(
            "|".join(self.PUBLISHER_LOGO_PATTERNS), re.IGNORECASE
        )
        self.caption_blacklist_regex = re.compile(
            "|".join(self.CAPTION_BLACKLIST), re.IGNORECASE
        )

    def is_meaningful(
        self,
        url: str,
        caption: str | None = None,
        is_main: bool = False,
    ) -> bool:
        """
        이미지가 의미있는 콘텐츠인지 확인.

        Args:
            url: 이미지 URL
            caption: 이미지 캡션 (있으면 신뢰도 높음)
            is_main: 메인 이미지 여부 (og:image 등)

        Returns:
            True if 의미있는 이미지, False otherwise
        """
        if not url:
            return False

        url_lower = url.lower()

        # 1. URL 블랙리스트 패턴 검사
        if self.blacklist_regex.search(url_lower):
            return False

        # 2. 언론사 로고 패턴 검사
        if self.publisher_logo_regex.search(url):
            return False

        # 3. 이미지 확장자 검사 (엄격)
        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        # GIF, SVG, ICO는 대부분 아이콘/애니메이션
        if path_lower.endswith((".gif", ".svg", ".ico")):
            return False

        # 4. 캡션 검사 (경로 길이 전에 먼저 검사 - 캡션이 신뢰도 높임)
        if caption:
            # 캡션에 광고 관련 텍스트가 있으면 제외
            if self.caption_blacklist_regex.search(caption):
                return False

            # 캡션이 있고 깨끗하면 신뢰도 높음 - 통과
            if len(caption) > 5:
                return True

        # 5. URL 경로 길이 검사 (너무 짧으면 로고일 가능성)
        if len(parsed.path) < 15 and not is_main:
            return False

        # 6. 메인 이미지는 약간 관대하게
        if is_main:
            # 메인이지만 확실한 블랙리스트 아니면 통과
            return True

        # 7. 쿼리 파라미터 검사 (리사이징 파라미터가 있으면 실제 콘텐츠일 가능성)
        if parsed.query:
            query_lower = parsed.query.lower()
            # 크기 조절 파라미터가 있으면 실제 이미지일 가능성 높음
            if any(
                param in query_lower
                for param in ["width=", "height=", "w=", "h=", "size=", "resize="]
            ):
                return True

        # 8. 이미지 파일명에서 의미있는 패턴 확인
        filename = path_lower.split("/")[-1]
        # 날짜/시간이 포함된 파일명 = 실제 뉴스 이미지일 가능성
        if re.search(r"20\d{2}[_-]?\d{2}[_-]?\d{2}", filename):
            return True
        # 긴 해시/ID가 있는 파일명 = 실제 콘텐츠일 가능성
        if re.search(r"[a-f0-9]{16,}", filename):
            return True

        # 기본적으로 제외 (공격적 필터링)
        return False

    def filter_images(
        self,
        images: list[dict],
        max_images: int = 3,
        require_caption: bool = False,
    ) -> list[dict]:
        """
        이미지 목록에서 의미있는 이미지만 필터링.

        Args:
            images: 이미지 목록 [{"url": ..., "caption": ..., "is_main": ...}]
            max_images: 최대 반환 이미지 수
            require_caption: 캡션 필수 여부 (더 엄격한 필터링)

        Returns:
            필터링된 이미지 목록
        """
        filtered = []

        for img in images:
            url = img.get("url", "")
            caption = img.get("caption")
            is_main = img.get("is_main", False)

            # 캡션 필수 모드에서 캡션 없으면 스킵
            if require_caption and not caption:
                continue

            if self.is_meaningful(url, caption, is_main):
                filtered.append(img)

        # 메인 이미지 우선 정렬
        filtered.sort(key=lambda x: (not x.get("is_main", False), not x.get("caption")))

        return filtered[:max_images]

    def get_main_image(self, images: list[dict]) -> dict | None:
        """
        가장 의미있는 메인 이미지 하나 추출.

        Args:
            images: 이미지 목록

        Returns:
            메인 이미지 또는 None
        """
        filtered = self.filter_images(images, max_images=1)
        return filtered[0] if filtered else None


# 싱글톤 인스턴스
_filter_instance: ImageFilter | None = None


def get_image_filter() -> ImageFilter:
    """ImageFilter 싱글톤 인스턴스 반환."""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = ImageFilter()
    return _filter_instance


def filter_meaningful_images(
    images: list[dict],
    max_images: int = 3,
) -> list[dict]:
    """편의 함수: 이미지 목록 필터링."""
    return get_image_filter().filter_images(images, max_images)


def get_main_image(images: list[dict]) -> dict | None:
    """편의 함수: 메인 이미지 추출."""
    return get_image_filter().get_main_image(images)
