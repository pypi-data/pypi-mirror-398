#!/bin/bash
set -e

echo "🚀 BigKinds MCP 배포 시작..."

# 1. .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "📝 .env.example을 복사하여 .env 파일을 생성하세요:"
    echo "   cp .env.example .env"
    echo ""
    echo "💡 Public Tools만 사용할 경우 환경변수 없이도 사용 가능합니다."
    echo "   Private Tools (get_keyword_trends, get_related_keywords)를 사용하려면"
    echo "   BIGKINDS_USER_ID와 BIGKINDS_USER_PASSWORD를 설정하세요."
    echo ""
    read -p "계속하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. Docker 빌드
echo "📦 Docker 이미지 빌드 중..."
docker-compose build

# 3. 컨테이너 시작
echo "🔄 컨테이너 시작 중..."
docker-compose up -d

# 4. Redis 헬스체크 대기
echo "🏥 Redis 헬스체크 대기 중..."
timeout 30s bash -c 'until docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do sleep 1; done' || {
    echo "❌ Redis 시작 실패. 로그를 확인하세요:"
    docker-compose logs redis
    exit 1
}

# 5. MCP 서버 상태 확인
echo "🔍 MCP 서버 상태 확인 중..."
sleep 3
if docker-compose ps bigkinds-mcp | grep -q "Up"; then
    echo "✅ 배포 완료! 서버가 정상 동작 중입니다."
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 서비스 정보"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 BigKinds MCP: stdio 모드 (Claude Desktop에서 사용)"
    echo "📊 Redis: localhost:6379"
    echo ""
    echo "📝 로그 확인:"
    echo "   docker-compose logs -f bigkinds-mcp"
    echo ""
    echo "🛑 중지:"
    echo "   docker-compose down"
    echo ""
    echo "🧹 완전 제거 (볼륨 포함):"
    echo "   docker-compose down -v"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ MCP 서버 시작 실패. 로그를 확인하세요:"
    docker-compose logs bigkinds-mcp
    exit 1
fi
