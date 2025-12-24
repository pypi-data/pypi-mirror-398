FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install uv

# Python 의존성 (uv.lock은 .gitignore에 있으므로 제외)
COPY pyproject.toml README.md ./
RUN uv sync --all-extras

# 소스 코드
COPY src/ ./src/
COPY bigkinds/ ./bigkinds/

# 환경변수
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 헬스체크 (MCP 서버는 stdio 모드이므로 프로세스 존재 여부 확인)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD pgrep -f "bigkinds_mcp.server" || exit 1

# 실행
CMD ["uv", "run", "bigkinds-mcp"]
