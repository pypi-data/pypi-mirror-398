# BigKinds MCP - Docker 배포 가이드

BigKinds MCP를 Docker 컨테이너로 실행하기 위한 가이드입니다.

## 배포 옵션

| 옵션 | 설명 | 사용 사례 |
|------|------|----------|
| **로컬 stdio** | uvx로 직접 실행 | 개인 사용, 개발 |
| **로컬 Docker** | Docker Compose로 로컬 실행 | 개발, 테스트 |
| **원격 서버** | Docker + Cloudflare Tunnel | 프로덕션, 팀 공유 |

---

## 1. 로컬 Docker 배포

### 빠른 시작

```bash
# 저장소 클론
git clone https://github.com/seolcoding/bigkinds-mcp.git
cd bigkinds-mcp

# .env 파일 생성 (선택사항 - Private Tools 사용 시)
cat > .env << EOF
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password
EOF

# Docker 빌드 및 실행
docker compose build
docker compose up -d

# 상태 확인
docker compose ps
```

### 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| bigkinds-mcp | 58002 | MCP Remote Server (HTTP/SSE) |
| redis | 56379 | 캐시 서버 |

### 헬스체크

```bash
curl http://localhost:58002/health
```

---

## 2. 원격 서버 배포

### 배포 아키텍처

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│ Cloudflare Tunnel│────▶│  Remote Server  │
│ (Claude, Cursor)│     │  (HTTPS/WSS)     │     │ (Docker + Redis)│
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### 현재 배포 상태

| 항목 | 값 |
|------|-----|
| **서버** | `100.114.192.51` |
| **영구 URL** | `https://bigkinds.seolcoding.com` |
| **API Key** | `bigkinds_mcp_secret_key_2025` |
| **포트** | 58002 (MCP), 56379 (Redis) |

### 서버 설정 방법

#### Step 1: 서버 접속 및 클론

```bash
ssh wai-3090ti@100.114.192.51

# 저장소 클론
git clone https://github.com/seolcoding/bigkinds-mcp.git
cd bigkinds-mcp
```

#### Step 2: 환경 설정

```bash
cat > .env << EOF
BIGKINDS_USER_ID=your_email@example.com
BIGKINDS_USER_PASSWORD=your_password
EOF
```

#### Step 3: Docker 실행

```bash
sudo docker compose build
sudo docker compose up -d
```

#### Step 4: Cloudflare Tunnel 설정

```bash
# 1. Cloudflare 로그인
cloudflared tunnel login
# → 브라우저에서 도메인 선택 및 인증

# 2. Named Tunnel 생성
cloudflared tunnel create wai-mcp-tunnel

# 3. DNS 라우트 추가
cloudflared tunnel route dns wai-mcp-tunnel bigkinds.yourdomain.com

# 4. config.yml 생성
cat > ~/.cloudflared/config.yml << EOF
tunnel: <TUNNEL_ID>
credentials-file: /home/<USER>/.cloudflared/<TUNNEL_ID>.json
protocol: http2

ingress:
  - hostname: bigkinds.yourdomain.com
    service: http://localhost:58002
  - service: http_status:404
EOF

# 5. systemd 서비스 등록
sudo tee /etc/systemd/system/cloudflared-tunnel.service << EOF
[Unit]
Description=Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/bin/cloudflared tunnel run wai-mcp-tunnel
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cloudflared-tunnel
sudo systemctl start cloudflared-tunnel
```

### 서버 관리 명령어

```bash
# SSH 접속
ssh wai-3090ti@100.114.192.51

# Docker 상태
cd ~/bigkinds-mcp && sudo docker compose ps

# Docker 로그
sudo docker compose logs -f bigkinds-mcp

# Docker 재시작
sudo docker compose restart

# Cloudflare Tunnel 상태
sudo systemctl status cloudflared-tunnel

# Cloudflare Tunnel 재시작
sudo systemctl restart cloudflared-tunnel

# 수동 배포 (git pull 후)
cd ~/bigkinds-mcp
git pull origin main
sudo docker compose build
sudo docker compose up -d
```

---

## 3. MCP 클라이언트 설정

### Claude Desktop (로컬 stdio)

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uvx",
      "args": ["bigkinds-mcp"],
      "env": {
        "BIGKINDS_USER_ID": "your_email@example.com",
        "BIGKINDS_USER_PASSWORD": "your_password"
      }
    }
  }
}
```

### Claude Desktop (원격 서버)

```json
{
  "mcpServers": {
    "bigkinds": {
      "type": "sse",
      "url": "https://bigkinds.seolcoding.com/sse",
      "headers": {
        "x-api-key": "bigkinds_mcp_secret_key_2025"
      }
    }
  }
}
```

### Claude Code

```bash
# 로컬 stdio
claude mcp add bigkinds -- uvx bigkinds-mcp

# 원격 서버 (SSE)
claude mcp add bigkinds --transport sse \
  --url "https://bigkinds.seolcoding.com/sse" \
  --header "x-api-key: bigkinds_mcp_secret_key_2025"
```

### Cursor / VS Code

`.cursor/mcp.json` 또는 `.vscode/mcp.json`:

#### 로컬 stdio

```json
{
  "mcpServers": {
    "bigkinds": {
      "command": "uvx",
      "args": ["bigkinds-mcp"],
      "env": {
        "BIGKINDS_USER_ID": "your_email@example.com",
        "BIGKINDS_USER_PASSWORD": "your_password"
      }
    }
  }
}
```

#### 원격 서버 (SSE)

```json
{
  "mcpServers": {
    "bigkinds": {
      "type": "sse",
      "url": "https://bigkinds.seolcoding.com/sse",
      "headers": {
        "x-api-key": "bigkinds_mcp_secret_key_2025"
      }
    }
  }
}
```

### 프로젝트별 설정 (.mcp.json)

프로젝트 루트에 `.mcp.json` 파일 생성:

```json
{
  "mcpServers": {
    "bigkinds": {
      "type": "sse",
      "url": "https://bigkinds.seolcoding.com/sse",
      "headers": {
        "x-api-key": "bigkinds_mcp_secret_key_2025"
      }
    }
  }
}
```

---

## 4. API 엔드포인트

### 원격 서버 API

| 엔드포인트 | 메서드 | 설명 | 인증 |
|-----------|--------|------|------|
| `/health` | GET | 헬스체크 | 불필요 |
| `/api/tools` | GET | 도구 목록 | 필요 |
| `/api/tools/{tool_name}` | POST | 도구 실행 | 필요 |
| `/sse` | GET | SSE 연결 (MCP) | 필요 |

### API 호출 예시

```bash
# 헬스체크
curl https://bigkinds.seolcoding.com/health

# 도구 목록
curl -H "x-api-key: bigkinds_mcp_secret_key_2025" \
  https://bigkinds.seolcoding.com/api/tools

# 뉴스 검색
curl -X POST \
  -H "x-api-key: bigkinds_mcp_secret_key_2025" \
  -H "Content-Type: application/json" \
  -d '{"keyword":"AI","start_date":"2025-12-01","end_date":"2025-12-15"}' \
  https://bigkinds.seolcoding.com/api/tools/search_news
```

---

## 5. 환경변수

### Docker 환경변수

| 변수 | 필수 | 설명 | 기본값 |
|------|------|------|--------|
| `MCP_PORT` | X | 서버 포트 | `58002` |
| `MCP_API_KEYS` | X | API 키 (쉼표 구분) | - |
| `REDIS_URL` | X | Redis 연결 URL | `redis://redis:6379` |
| `BIGKINDS_USER_ID` | △ | BigKinds 로그인 | - |
| `BIGKINDS_USER_PASSWORD` | △ | BigKinds 비밀번호 | - |
| `BIGKINDS_TIMEOUT` | X | API 타임아웃 | `30` |
| `BIGKINDS_MAX_RETRIES` | X | 최대 재시도 | `3` |
| `BIGKINDS_RETRY_DELAY` | X | 재시도 간격 | `1.0` |

---

## 6. 트러블슈팅

### Docker 빌드 실패

```bash
# 캐시 없이 재빌드
sudo docker compose build --no-cache
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
sudo lsof -i :58002

# docker-compose.yml에서 포트 변경
ports:
  - "58003:58002"  # 호스트 포트 변경
```

### Cloudflare Tunnel 연결 실패

```bash
# 로그 확인
sudo journalctl -u cloudflared-tunnel -f

# QUIC 실패 시 HTTP/2로 변경
# ~/.cloudflared/config.yml에 추가:
protocol: http2
```

### Redis 연결 실패

```bash
# Redis 상태 확인
sudo docker compose logs redis

# Redis 재시작
sudo docker compose restart redis
```

---

## 7. 보안 권장사항

1. **API 키 관리**: 강력한 API 키 사용, 정기 교체
2. **HTTPS 필수**: Cloudflare Tunnel로 자동 적용
3. **환경변수 보호**: `.env` 파일을 `.gitignore`에 추가
4. **접근 제한**: 필요시 Cloudflare Access로 추가 인증
5. **로그 모니터링**: 비정상 접근 패턴 감시

---

## 참고 링크

- [MCP Protocol 문서](https://modelcontextprotocol.io/)
- [Cloudflare Tunnel 문서](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
