# Deprecated Files

이 폴더에는 더 이상 사용되지 않는 파일들이 보관되어 있습니다.

## 제거 사유

### tests/
| 파일 | 사유 |
|------|------|
| `test_network_analysis.py` | 관계도 분석 API 제거됨 (브라우저 전용) |
| `test_network_debug.py` | 관계도 분석 디버깅용 |
| `test_auth_api.py` | 일회성 API 테스트 |
| `test_auth_api_v2.py` | 일회성 API 테스트 |
| `test_keyword_trends.py` | 일회성 트렌드 테스트 |
| `test_related_words_fix.py` | 버그 수정용 테스트 |
| `demo_related_words.py` | 데모 스크립트 |

### root_tests/
| 파일 | 사유 |
|------|------|
| `test_article_scraper.py` | 레거시 테스트 |
| `test_bigkinds_hopping.py` | 레거시 테스트 |
| `test_bigkinds_scenarios.py` | 레거시 테스트 |

## 관계도 분석 제거 배경

`/news/getNetworkDataAnalysis.do` API는 브라우저 전용입니다:
- 브라우저에서 로그인 후 호출: **200 OK** (정상)
- httpx에서 직접 호출: **302 Redirect** → `/err/error400.do`

JavaScript가 설정하는 추가 쿠키/토큰이 필요하거나 CSRF 검증이 있는 것으로 추정됩니다.

## 날짜

2024-12-15
