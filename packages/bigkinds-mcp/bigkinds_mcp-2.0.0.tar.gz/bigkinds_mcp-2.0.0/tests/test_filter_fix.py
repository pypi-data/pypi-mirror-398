"""필터 수정 검증 테스트."""

import pytest


class TestCategoryMapping:
    """카테고리 매핑 테스트."""

    def test_category_codes_mapping(self):
        """CATEGORY_CODES 매핑 검증 (사용자 친화적 이름 → 9-digit 숫자 코드)."""
        from bigkinds_mcp.tools.utils import CATEGORY_CODES

        # 사용자 친화적 이름 → BigKinds API 숫자 코드
        assert CATEGORY_CODES["정치"] == "001000000"
        assert CATEGORY_CODES["경제"] == "002000000"
        assert CATEGORY_CODES["사회"] == "003000000"
        assert CATEGORY_CODES["문화"] == "004000000"
        assert CATEGORY_CODES["국제"] == "005000000"
        assert CATEGORY_CODES["지역"] == "006000000"
        assert CATEGORY_CODES["스포츠"] == "007000000"
        assert CATEGORY_CODES["IT_과학"] == "008000000"

    def test_category_normalization(self):
        """카테고리 정규화 로직 테스트 (사용자 이름 → API 숫자 코드)."""
        from bigkinds_mcp.tools.utils import CATEGORY_CODES

        # 시뮬레이션: search.py의 변환 로직
        test_cases = {
            "정치": "001000000",
            "경제": "002000000",
            "IT_과학": "008000000",
            "알수없는카테고리": "알수없는카테고리",  # 매핑 없으면 그대로
        }

        for input_cat, expected in test_cases.items():
            normalized = CATEGORY_CODES.get(input_cat, input_cat)
            print(f"{input_cat} → {normalized}")
            assert normalized == expected, f"{input_cat} should map to {expected}, got {normalized}"


class TestProviderMapping:
    """언론사 매핑 테스트."""

    def test_provider_name_to_code(self):
        """언론사 이름 → 코드 변환 검증 (실제 API 응답 기준)."""
        from bigkinds_mcp.tools.utils import PROVIDER_NAME_TO_CODE

        # 주요 언론사 확인
        assert "경향신문" in PROVIDER_NAME_TO_CODE
        assert "한겨레" in PROVIDER_NAME_TO_CODE
        assert "조선일보" in PROVIDER_NAME_TO_CODE

        # 코드 확인 (2025-12-15 API 응답 기준으로 수정)
        assert PROVIDER_NAME_TO_CODE["경향신문"] == "01100101"
        assert PROVIDER_NAME_TO_CODE["한겨레"] == "01101001"
        assert PROVIDER_NAME_TO_CODE["조선일보"] == "01100801"

    def test_provider_normalization(self):
        """언론사 정규화 로직 테스트 (실제 API 코드 기준)."""
        from bigkinds_mcp.tools.utils import PROVIDER_NAME_TO_CODE

        # 시뮬레이션: search.py의 변환 로직
        test_inputs = ["경향신문", "01100101", "알수없는언론사"]

        for input_prov in test_inputs:
            if input_prov in PROVIDER_NAME_TO_CODE:
                code = PROVIDER_NAME_TO_CODE[input_prov]
                print(f"{input_prov} → {code}")
            else:
                # 이미 코드거나 알 수 없는 값은 그대로
                code = input_prov
                print(f"{input_prov} → {code} (그대로)")

            # 경향신문은 코드로 변환 (2025-12-15 API 응답 기준)
            if input_prov == "경향신문":
                assert code == "01100101"
            # 코드 직접 입력 시 그대로
            elif input_prov == "01100101":
                assert code == "01100101"
            # 알 수 없는 값도 그대로 (fallback)
            else:
                assert code == input_prov


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
