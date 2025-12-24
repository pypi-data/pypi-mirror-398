"""Remote MCP Server 테스트 - MCP Protocol Compliance."""

import pytest
from fastapi.testclient import TestClient

from bigkinds_mcp.remote_server import app, TOOLS, PROTOCOL_VERSION, SERVER_VERSION


@pytest.fixture
def client():
    """테스트 클라이언트 fixture."""
    return TestClient(app)


def test_health_check(client):
    """헬스체크 엔드포인트 테스트."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["version"] == SERVER_VERSION
    assert data["protocol"] == PROTOCOL_VERSION
    assert data["service"] == "bigkinds-mcp"


def test_mcp_initialize(client):
    """MCP initialize 요청 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        },
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()

    # JSON-RPC 응답 형식 확인
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    assert "error" not in data

    # 결과 확인
    result = data["result"]
    assert result["protocolVersion"] == PROTOCOL_VERSION
    assert "capabilities" in result
    assert "tools" in result["capabilities"]
    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "bigkinds-mcp"

    # 세션 ID 헤더 확인
    assert "mcp-session-id" in response.headers


def test_mcp_tools_list(client):
    """MCP tools/list 요청 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()

    # JSON-RPC 응답 형식 확인
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data

    # tools 배열 확인
    tools = data["result"]["tools"]
    assert isinstance(tools, list)
    assert len(tools) == len(TOOLS)

    # 각 tool의 스키마 확인
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


def test_mcp_tools_call(client):
    """MCP tools/call 요청 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_news",
                "arguments": {
                    "keyword": "AI",
                    "start_date": "2025-12-01",
                    "end_date": "2025-12-15",
                    "page_size": 5
                }
            }
        },
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()

    # JSON-RPC 응답 형식 확인
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert "result" in data

    # Tool result 형식 확인
    result = data["result"]
    assert "content" in result
    assert "isError" in result
    assert isinstance(result["content"], list)

    # Content 확인
    if not result["isError"]:
        content = result["content"][0]
        assert content["type"] == "text"
        assert "text" in content


def test_mcp_tools_call_unknown_tool(client):
    """알 수 없는 tool 호출 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            }
        },
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()

    # Tool execution error (isError: true)
    result = data["result"]
    assert result["isError"] is True
    assert "Unknown tool" in result["content"][0]["text"]


def test_mcp_method_not_found(client):
    """알 수 없는 method 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "unknown/method",
            "params": {}
        },
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()

    # JSON-RPC error
    assert "error" in data
    assert data["error"]["code"] == -32601  # Method not found


def test_mcp_ping(client):
    """ping 요청 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "ping",
            "params": {}
        },
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 6
    assert data["result"] == {}


def test_mcp_notification(client):
    """notification (no id) 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        },
        headers={"Accept": "application/json"}
    )

    # Notification은 202 Accepted
    assert response.status_code == 202


def test_mcp_batch_request(client):
    """배치 요청 테스트."""
    response = client.post(
        "/mcp",
        json=[
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "ping",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/list",
                "params": {}
            }
        ],
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()

    # 배치 응답은 배열
    assert isinstance(data, list)
    assert len(data) == 2

    # 각 응답 확인
    ids = [d["id"] for d in data]
    assert 10 in ids
    assert 11 in ids


def test_mcp_sse_response(client):
    """SSE 응답 테스트."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/list",
            "params": {}
        },
        headers={"Accept": "text/event-stream, application/json"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


def test_legacy_tools_endpoint(client):
    """레거시 /api/tools 엔드포인트 테스트."""
    response = client.get("/api/tools")

    assert response.status_code == 200
    data = response.json()

    assert "tools" in data
    assert "search_news" in data["tools"]


def test_tool_input_schema_validation():
    """Tool inputSchema 형식 검증."""
    for tool in TOOLS:
        schema = tool["inputSchema"]

        # 기본 구조
        assert schema["type"] == "object"
        assert "properties" in schema

        # required 필드가 있으면 properties에 존재해야 함
        if "required" in schema:
            for req in schema["required"]:
                assert req in schema["properties"], f"{tool['name']}: required field '{req}' not in properties"


def test_cors_middleware_configured():
    """CORS middleware 설정 확인."""
    from bigkinds_mcp.remote_server import app
    from starlette.middleware.cors import CORSMiddleware

    middleware_classes = [m.cls for m in app.user_middleware]
    assert CORSMiddleware in middleware_classes
