# BigKinds Remote MCP Server

FastAPI 기반 원격 MCP 서버 - 여러 클라이언트가 HTTP/SSE를 통해 BigKinds API에 접근할 수 있습니다.

## 기능

- FastAPI 기반 REST API 서버
- SSE (Server-Sent Events) 스트리밍 지원
- API 키 기반 인증
- CORS 지원 (개발/프로덕션 설정 가능)
- Redis 캐시 통합 (선택 사항)
- 모든 MCP Tools HTTP 엔드포인트로 노출

## 설치

```bash
# Remote 서버 의존성 설치
uv sync --extra remote

# 또는 개발 환경 전체 설치
uv sync --all-extras
```

## 환경 변수

```bash
# API 키 설정 (쉼표로 여러 키 구분)
export MCP_API_KEYS="your_api_key_1,your_api_key_2"

# 서버 포트 (기본: 8000)
export MCP_PORT=8000
export MCP_HOST=0.0.0.0

# BigKinds 인증 (Private Tools 사용 시 필요)
export BIGKINDS_USER_ID=your_email@example.com
export BIGKINDS_USER_PASSWORD=your_password

# Redis 캐시 (선택 사항)
export REDIS_URL=redis://localhost:6379
```

## 실행

### 로컬 개발

```bash
# 기본 포트 (8000)
uv run bigkinds-mcp-remote

# 커스텀 포트
MCP_PORT=8001 uv run bigkinds-mcp-remote

# 또는 직접 실행
uv run python -m bigkinds_mcp.remote_server
```

### 프로덕션 (Uvicorn)

```bash
# 워커 프로세스 4개로 실행
uvicorn bigkinds_mcp.remote_server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4

# 자동 재시작 (개발용)
uvicorn bigkinds_mcp.remote_server:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

## API 엔드포인트

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.7.0",
  "service": "bigkinds-mcp",
  "cache_stats": { ... }
}
```

### 2. SSE Stream

Server-Sent Events 스트림 (MCP 클라이언트용)

```bash
curl -H "x-api-key: your_api_key" http://localhost:8000/sse
```

### 3. Tools List

```bash
curl -H "x-api-key: your_api_key" http://localhost:8000/api/tools
```

### 4. Tool Execution

```bash
curl -X POST \
  -H "x-api-key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "AI",
    "start_date": "2024-12-01",
    "end_date": "2024-12-15",
    "page": 1,
    "page_size": 10
  }' \
  http://localhost:8000/api/tools/search_news
```

### 5. Cache Statistics

```bash
curl -H "x-api-key: your_api_key" http://localhost:8000/api/cache/stats
```

## 사용 가능한 Tools

- `search_news`: 뉴스 검색
- `get_article`: 기사 상세 조회
- `get_article_count`: 기사 수 집계
- `scrape_article_url`: URL 스크래핑
- `get_today_issues`: 오늘의 이슈
- `compare_keywords`: 키워드 비교
- `smart_sample`: 대표 샘플 추출
- `export_all_articles`: 전체 기사 내보내기

## Redis 캐시 (선택 사항)

Redis를 사용하면 여러 서버 인스턴스 간 캐시를 공유할 수 있습니다.

### Redis 설치 및 실행

```bash
# macOS
brew install redis
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:latest

# 연결 확인
redis-cli ping
```

### Remote Cache 사용

```python
from bigkinds_mcp.core.remote_cache import RemoteCache

cache = RemoteCache("redis://localhost:6379")
await cache.connect()

# 캐시 사용
await cache.set("key", {"data": "value"}, ttl=300)
data = await cache.get("key")
```

## 보안

### API 키 관리

```bash
# 강력한 API 키 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 환경 변수 설정
export MCP_API_KEYS="generated_key_1,generated_key_2"
```

### CORS 설정

프로덕션에서는 `remote_server.py`의 CORS 설정을 수정하세요:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["x-api-key", "content-type"],
)
```

## 테스트

```bash
# 단위 테스트
uv run pytest tests/test_remote_server.py -v

# 통합 테스트 (실제 서버 필요)
# Terminal 1: 서버 시작
MCP_PORT=8001 uv run bigkinds-mcp-remote

# Terminal 2: 테스트
curl -H "x-api-key: test_key_123" http://localhost:8001/health
```

## Docker 배포

### Dockerfile 예제

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 복사 및 설치
COPY pyproject.toml .
RUN uv sync --extra remote

# 소스 코드 복사
COPY . .

# 환경 변수
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000

# 서버 실행
CMD ["uv", "run", "bigkinds-mcp-remote"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  bigkinds-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_API_KEYS=${MCP_API_KEYS}
      - BIGKINDS_USER_ID=${BIGKINDS_USER_ID}
      - BIGKINDS_USER_PASSWORD=${BIGKINDS_USER_PASSWORD}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## 성능 튜닝

### Uvicorn 워커

```bash
# CPU 코어 수만큼 워커 실행
uvicorn bigkinds_mcp.remote_server:app \
  --workers $(nproc) \
  --host 0.0.0.0 \
  --port 8000
```

### Gunicorn (프로덕션)

```bash
# Gunicorn with Uvicorn workers
gunicorn bigkinds_mcp.remote_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 모니터링

### 헬스체크

```bash
# 주기적인 헬스체크
watch -n 10 curl -s http://localhost:8000/health
```

### 로그 수준 설정

```bash
# 디버그 로그
uvicorn bigkinds_mcp.remote_server:app --log-level debug

# 프로덕션 로그
uvicorn bigkinds_mcp.remote_server:app --log-level warning
```

## 문제 해결

### 포트 충돌

```bash
# 사용 중인 포트 확인
lsof -i :8000

# 다른 포트 사용
MCP_PORT=8001 uv run bigkinds-mcp-remote
```

### Redis 연결 실패

```bash
# Redis 상태 확인
redis-cli ping

# Redis 로그 확인
redis-cli monitor
```

## 라이선스

MIT License - 자세한 내용은 LICENSE 파일 참조
