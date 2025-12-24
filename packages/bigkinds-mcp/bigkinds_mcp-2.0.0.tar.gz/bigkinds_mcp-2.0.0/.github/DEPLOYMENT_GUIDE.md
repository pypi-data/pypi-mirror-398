# GitHub Actions 배포 가이드

## 📋 개요

이 프로젝트는 3개의 GitHub Actions 워크플로를 사용합니다:

1. **test.yml**: PR/Push 시 자동 테스트
2. **publish.yml**: 태그 푸시 시 PyPI 자동 배포
3. **filter-validation.yml**: 월간 필터 코드 검증

---

## 🔐 필수 설정

### 1. GitHub Secrets 설정

Repository Settings → Secrets and variables → Actions에서 다음 시크릿을 추가하세요:

#### 필수 시크릿
```
PYPI_API_TOKEN: PyPI API 토큰
```

#### 선택적 시크릿 (Private Tools 테스트용)
```
BIGKINDS_USER_ID: BigKinds 계정 이메일
BIGKINDS_USER_PASSWORD: BigKinds 계정 비밀번호
```

### 2. PyPI API 토큰 발급

1. [PyPI 계정 설정](https://pypi.org/manage/account/) 접속
2. "API tokens" 섹션에서 "Add API token" 클릭
3. Token name: `github-actions-bigkinds-mcp`
4. Scope: "Entire account" 또는 "Project: bigkinds-mcp"
5. 생성된 토큰 복사 (한 번만 표시됨!)
6. GitHub Secrets에 `PYPI_API_TOKEN`으로 저장

---

## 🚀 배포 프로세스

### 자동 배포 (권장)

#### 1. 버전 업데이트
```bash
# pyproject.toml에서 버전 업데이트
version = "1.2.0" → "1.2.1"
```

#### 2. Git 태그 생성 및 푸시
```bash
# 변경사항 커밋
git add .
git commit -m "chore: bump version to 1.2.1"

# 태그 생성
git tag v1.2.1

# 푸시 (태그 포함)
git push origin main
git push origin v1.2.1
```

#### 3. 자동 배포 확인
- GitHub Actions 탭에서 "Publish to PyPI" 워크플로 실행 확인
- 테스트 → 빌드 → PyPI 배포 → GitHub Release 생성 순서로 진행
- 완료 후 https://pypi.org/project/bigkinds-mcp/ 에서 확인

### 수동 배포 (로컬)

```bash
# 빌드
uv build

# 배포 (환경변수 필요)
export UV_PUBLISH_TOKEN="pypi-..."
uv publish

# 또는 한 번에
UV_PUBLISH_TOKEN="pypi-..." uv publish
```

---

## 🧪 워크플로 상세

### 1. test.yml - 자동 테스트

**트리거:**
- `main`, `develop` 브랜치에 push
- PR 생성/업데이트

**실행 내용:**
```yaml
1. Python 3.12 환경 설정
2. uv 설치
3. 의존성 설치 (uv sync)
4. 테스트 실행 (pytest)
5. 코드 포맷 검사 (ruff)
6. 타입 체크 (mypy, 선택적)
```

**실패 시:**
- PR 머지 불가
- 로그 확인 후 수정 필요

### 2. publish.yml - PyPI 배포

**트리거:**
- `v*.*.*` 형식의 태그 푸시 (예: v1.2.0)

**실행 내용:**
```yaml
Job 1: test
  - 전체 테스트 실행
  - 실패 시 배포 중단

Job 2: publish (test 성공 시)
  - 패키지 빌드 (uv build)
  - PyPI 배포 (uv publish)
  - GitHub Release 생성
```

**결과:**
- PyPI에 새 버전 업로드
- GitHub Release 자동 생성 (릴리즈 노트 포함)
- dist 파일 (.tar.gz, .whl) 첨부

### 3. filter-validation.yml - 월간 검증

**트리거:**
- 매월 1일 00:00 UTC (자동)
- 수동 실행 가능 (Actions 탭 → Run workflow)

**실행 내용:**
```yaml
1. 필터 관련 테스트 실행
2. 실패 시 자동으로 GitHub Issue 생성
3. 성공 시 로그에 성공 메시지
```

**Issue 생성 시:**
- 제목: "⚠️ Filter codes validation failed"
- 라벨: `maintenance`, `filter-validation`
- 상세 조치 방법 포함

---

## 📝 버전 관리 규칙

### Semantic Versioning

```
v{MAJOR}.{MINOR}.{PATCH}

MAJOR: 호환되지 않는 API 변경
MINOR: 하위 호환 기능 추가
PATCH: 하위 호환 버그 수정
```

### 예시
```
v1.0.0 → 초기 릴리즈
v1.1.0 → 새 도구 추가 (compare_keywords 등)
v1.1.1 → 버그 수정
v1.2.0 → 필터 개선 (호환 유지)
v2.0.0 → Breaking change (API 변경)
```

### CHANGELOG.md 업데이트

배포 전 CHANGELOG.md에 변경사항 기록:

```markdown
## [1.2.1] - 2025-12-15

### Fixed
- 카테고리 필터 매핑 오류 수정

### Added
- compare_keywords 도구 추가

### Changed
- 캐시 TTL 5분 → 10분으로 변경
```

---

## 🔍 트러블슈팅

### 배포 실패 시

#### 1. 테스트 실패
```bash
# 로컬에서 테스트 실행
uv run pytest tests/ -v

# 특정 테스트만
uv run pytest tests/test_filter_fix.py -v
```

#### 2. PyPI 토큰 만료
- PyPI에서 새 토큰 발급
- GitHub Secrets의 `PYPI_API_TOKEN` 업데이트

#### 3. 버전 중복
```
Error: File already exists
```
→ pyproject.toml의 version을 올리고 새 태그 생성

#### 4. 권한 오류
```
Error: 403 Forbidden
```
→ PyPI 토큰 권한 확인 (프로젝트 소유자여야 함)

### 월간 검증 Issue 발생 시

```bash
# 1. 최신 필터 코드 수집
uv run python scripts/collect_provider_codes.py

# 2. 기존 코드와 비교
diff provider_codes_collected.json src/bigkinds_mcp/tools/utils.py

# 3. 변경 필요 시
# - utils.py의 PROVIDER_CODES 업데이트
# - tests/test_filter_fix.py 업데이트
# - 테스트 실행하여 검증

# 4. 커밋 및 푸시
git commit -am "fix: update filter codes"
git push
```

---

## 🎯 체크리스트

### 배포 전 체크리스트

- [ ] CHANGELOG.md 업데이트
- [ ] pyproject.toml 버전 업데이트
- [ ] 로컬 테스트 통과 (`uv run pytest`)
- [ ] README.md 업데이트 (필요시)
- [ ] 변경사항 커밋
- [ ] 태그 생성 및 푸시

### 배포 후 확인

- [ ] GitHub Actions 성공 확인
- [ ] PyPI 페이지에서 새 버전 확인
- [ ] GitHub Release 생성 확인
- [ ] 로컬에서 설치 테스트
  ```bash
  pip install bigkinds-mcp==1.2.1
  ```

---

## 📚 참고 자료

- [uv publish 문서](https://docs.astral.sh/uv/guides/publish/)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [PyPI API 토큰 가이드](https://pypi.org/help/#apitoken)
- [Semantic Versioning](https://semver.org/)

---

## 🆘 도움 필요 시

1. GitHub Actions 로그 확인
2. PyPI 배포 로그 확인
3. [GitHub Issues](https://github.com/YOUR_USERNAME/bigkinds/issues)에 문의
4. [Act Phase 문서](../docs/pdca/improvement-2025-12-15/act.md) 참조
