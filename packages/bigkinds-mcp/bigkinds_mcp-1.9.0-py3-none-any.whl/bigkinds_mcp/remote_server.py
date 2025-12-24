"""
Remote MCP Server with Streamable HTTP transport.

Implements MCP Protocol Specification (2025-03-26):
- JSON-RPC 2.0 message format
- Streamable HTTP transport (POST/GET on single endpoint)
- SSE streaming for responses
- Session management

Usage:
    uv run bigkinds-mcp-remote
    or
    uv run python -m bigkinds_mcp.remote_server
"""

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .core.async_client import AsyncBigKindsClient
from .core.async_scraper import AsyncArticleScraper
from .core.cache import MCPCache
from .tools import analysis, article, search, visualization

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# MCP Protocol Version
PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "bigkinds-mcp"
SERVER_VERSION = "1.9.0"

# 전역 리소스
_client: Optional[AsyncBigKindsClient] = None
_scraper: Optional[AsyncArticleScraper] = None
_cache: Optional[MCPCache] = None

# 세션 관리
_sessions: dict[str, dict] = {}


# ============================================================
# Tool Definitions with inputSchema
# ============================================================

TOOLS = [
    {
        "name": "search_news",
        "description": "BigKinds에서 뉴스 기사를 검색합니다. 54개 주요 언론사의 뉴스를 키워드, 기간, 언론사, 카테고리로 필터링하여 검색할 수 있습니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드 (AND/OR 연산자 지원)"
                },
                "start_date": {
                    "type": "string",
                    "description": "검색 시작일 (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "검색 종료일 (YYYY-MM-DD)"
                },
                "page": {
                    "type": "integer",
                    "description": "페이지 번호 (기본값: 1)",
                    "default": 1
                },
                "page_size": {
                    "type": "integer",
                    "description": "페이지당 결과 수 (기본값: 20, 최대: 100)",
                    "default": 20
                },
                "providers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "언론사 필터 (예: [\"경향신문\", \"한겨레\"])"
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "카테고리 필터 (예: [\"경제\", \"IT_과학\"])"
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["both", "date", "relevance"],
                    "description": "정렬 방식: both(병합), date(최신순), relevance(관련도순)",
                    "default": "both"
                }
            },
            "required": ["keyword", "start_date", "end_date"]
        }
    },
    {
        "name": "get_article",
        "description": "기사의 상세 정보를 가져옵니다. news_id 또는 URL로 기사 전문, 메타데이터, 이미지를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "news_id": {
                    "type": "string",
                    "description": "BigKinds 기사 ID"
                },
                "url": {
                    "type": "string",
                    "description": "원본 기사 URL"
                },
                "include_full_content": {
                    "type": "boolean",
                    "description": "전문 포함 여부 (기본값: true)",
                    "default": True
                },
                "include_images": {
                    "type": "boolean",
                    "description": "이미지 URL 목록 포함 여부 (기본값: false)",
                    "default": False
                }
            }
        }
    },
    {
        "name": "get_article_count",
        "description": "검색 조건에 맞는 기사 수를 조회합니다. 일별/주별/월별 집계를 지원합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드"
                },
                "start_date": {
                    "type": "string",
                    "description": "검색 시작일 (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "검색 종료일 (YYYY-MM-DD)"
                },
                "providers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "언론사 필터"
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "카테고리 필터"
                },
                "group_by": {
                    "type": "string",
                    "enum": ["total", "day", "week", "month"],
                    "description": "집계 단위 (기본값: total)",
                    "default": "total"
                }
            },
            "required": ["keyword", "start_date", "end_date"]
        }
    },
    {
        "name": "scrape_article_url",
        "description": "URL에서 기사 내용을 스크래핑합니다. BigKinds 검색 결과의 원본 URL에서 전문을 가져올 때 사용합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "스크래핑할 기사 URL"
                },
                "extract_images": {
                    "type": "boolean",
                    "description": "이미지 추출 여부 (기본값: false)",
                    "default": False
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "get_article_thumbnail",
        "description": "기사 URL에서 대표 이미지(썸네일)를 추출합니다. og:image를 우선 사용하고, 없으면 본문 이미지에서 추출합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "기사 URL"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "get_today_issues",
        "description": "오늘 또는 특정 날짜의 인기 이슈(Top 뉴스)를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "조회할 날짜 (YYYY-MM-DD). 생략하면 오늘"
                },
                "category": {
                    "type": "string",
                    "enum": ["전체", "AI"],
                    "description": "카테고리 필터 (기본값: 전체)",
                    "default": "전체"
                }
            }
        }
    },
    {
        "name": "compare_keywords",
        "description": "여러 키워드(2-10개)의 기사량을 비교 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 10,
                    "description": "비교할 키워드 목록 (2-10개)"
                },
                "start_date": {
                    "type": "string",
                    "description": "검색 시작일 (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "검색 종료일 (YYYY-MM-DD)"
                },
                "group_by": {
                    "type": "string",
                    "enum": ["total", "day", "week", "month"],
                    "description": "집계 단위 (기본값: total)",
                    "default": "total"
                }
            },
            "required": ["keywords", "start_date", "end_date"]
        }
    },
    {
        "name": "smart_sample",
        "description": "대용량 검색 결과에서 대표 샘플을 추출합니다. stratified(계층화), latest(최신), random(무작위) 전략을 지원합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드"
                },
                "start_date": {
                    "type": "string",
                    "description": "검색 시작일 (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "검색 종료일 (YYYY-MM-DD)"
                },
                "sample_size": {
                    "type": "integer",
                    "description": "추출할 샘플 수 (기본값: 100)",
                    "default": 100
                },
                "strategy": {
                    "type": "string",
                    "enum": ["stratified", "latest", "random"],
                    "description": "샘플링 전략 (기본값: stratified)",
                    "default": "stratified"
                }
            },
            "required": ["keyword", "start_date", "end_date"]
        }
    },
    {
        "name": "export_all_articles",
        "description": "전체 기사를 일괄 내보내기합니다. JSON, CSV, JSONL 형식을 지원하며 최대 50,000건까지 가능합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드"
                },
                "start_date": {
                    "type": "string",
                    "description": "검색 시작일 (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "검색 종료일 (YYYY-MM-DD)"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["json", "csv", "jsonl"],
                    "description": "출력 형식 (기본값: json)",
                    "default": "json"
                },
                "output_path": {
                    "type": "string",
                    "description": "저장 경로 (생략 시 자동 생성)"
                },
                "max_articles": {
                    "type": "integer",
                    "description": "최대 기사 수 (기본값: 1000, 최대: 50000)",
                    "default": 1000
                },
                "include_content": {
                    "type": "boolean",
                    "description": "전문 포함 여부 (기본값: false)",
                    "default": False
                }
            },
            "required": ["keyword", "start_date", "end_date"]
        }
    },
    {
        "name": "analyze_timeline",
        "description": "키워드의 타임라인을 분석하여 주요 이벤트를 자동 탐지합니다. 25만건 이상의 대용량 기사에서 시간별 주요 사건을 NLP 기반으로 자동 추출합니다. 급증 시점 탐지, 핵심 키워드 추출, 대표 기사 선정을 수행합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "분석할 키워드 (예: 한동훈, AI, 비트코인)"
                },
                "start_date": {
                    "type": "string",
                    "description": "분석 시작일 (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "분석 종료일 (YYYY-MM-DD)"
                },
                "max_events": {
                    "type": "integer",
                    "description": "추출할 최대 이벤트 수 (기본값: 10, 최대: 50)",
                    "default": 10
                },
                "articles_per_event": {
                    "type": "integer",
                    "description": "이벤트당 대표 기사 수 (기본값: 3)",
                    "default": 3
                }
            },
            "required": ["keyword", "start_date", "end_date"]
        }
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 생명주기 관리."""
    global _client, _scraper, _cache

    logger.info("🚀 Starting BigKinds Remote MCP Server (Protocol: %s)...", PROTOCOL_VERSION)

    # Startup
    _client = AsyncBigKindsClient()
    _scraper = AsyncArticleScraper()
    _cache = MCPCache()

    # Tools 초기화
    search.init_search_tools(_client, _cache)
    article.init_article_tools(_client, _scraper, _cache)
    visualization.init_visualization_tools(_client, _cache)
    analysis.init_analysis_tools(_client, _cache)

    logger.info("✅ Server initialized successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down server...")
    if _client:
        await _client.close()
    if _scraper:
        _scraper.close()
    logger.info("👋 Server shutdown complete")


# FastAPI 앱 생성
app = FastAPI(
    title="BigKinds MCP Remote Server",
    version=SERVER_VERSION,
    description="MCP-compliant remote server for BigKinds news analysis",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# JSON-RPC Error Codes
# ============================================================

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


def jsonrpc_error(id: Any, code: int, message: str, data: Any = None) -> dict:
    """JSON-RPC 에러 응답 생성."""
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": id, "error": error}


def jsonrpc_result(id: Any, result: Any) -> dict:
    """JSON-RPC 성공 응답 생성."""
    return {"jsonrpc": "2.0", "id": id, "result": result}


# ============================================================
# MCP Message Handlers
# ============================================================

async def handle_initialize(params: dict, request_id: Any) -> dict:
    """Handle initialize request."""
    client_protocol = params.get("protocolVersion", "unknown")
    client_info = params.get("clientInfo", {})

    logger.info(
        "Initialize request from %s v%s (protocol: %s)",
        client_info.get("name", "unknown"),
        client_info.get("version", "unknown"),
        client_protocol
    )

    # 세션 ID 생성
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "client_info": client_info,
        "protocol_version": client_protocol,
        "initialized": False
    }

    return jsonrpc_result(request_id, {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {
            "tools": {
                "listChanged": False
            }
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION
        },
        "instructions": "BigKinds 뉴스 검색 및 분석 MCP 서버입니다. 54개 주요 언론사의 10년치 뉴스를 검색, 분석할 수 있습니다."
    }), session_id


async def handle_initialized(params: dict, session_id: str) -> None:
    """Handle initialized notification."""
    if session_id in _sessions:
        _sessions[session_id]["initialized"] = True
        logger.info("Session %s initialized", session_id[:8])


async def handle_tools_list(params: dict, request_id: Any) -> dict:
    """Handle tools/list request."""
    cursor = params.get("cursor")

    # 페이지네이션 지원 (현재는 단일 페이지)
    return jsonrpc_result(request_id, {
        "tools": TOOLS
    })


async def handle_tools_call(params: dict, request_id: Any) -> dict:
    """Handle tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    logger.info("Tool call: %s with args: %s", tool_name, list(arguments.keys()))

    try:
        result = await execute_tool(tool_name, arguments)

        # 결과를 text content로 변환
        if isinstance(result, dict):
            text_result = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            text_result = str(result)

        return jsonrpc_result(request_id, {
            "content": [
                {
                    "type": "text",
                    "text": text_result
                }
            ],
            "isError": False
        })

    except ValueError as e:
        return jsonrpc_result(request_id, {
            "content": [
                {
                    "type": "text",
                    "text": f"입력 오류: {str(e)}"
                }
            ],
            "isError": True
        })
    except Exception as e:
        logger.error("Tool execution error: %s", e, exc_info=True)
        return jsonrpc_result(request_id, {
            "content": [
                {
                    "type": "text",
                    "text": f"실행 오류: {str(e)}"
                }
            ],
            "isError": True
        })


async def execute_tool(tool_name: str, arguments: dict) -> Any:
    """Execute a tool by name."""
    if tool_name == "search_news":
        return await search.search_news(**arguments)
    elif tool_name == "get_article":
        return await article.get_article(**arguments)
    elif tool_name == "get_article_count":
        return await search.get_article_count(**arguments)
    elif tool_name == "scrape_article_url":
        return await article.scrape_article_url(**arguments)
    elif tool_name == "get_article_thumbnail":
        return await article.get_article_thumbnail(**arguments)
    elif tool_name == "get_today_issues":
        return await _get_today_issues(**arguments)
    elif tool_name == "compare_keywords":
        return await analysis.compare_keywords(**arguments)
    elif tool_name == "smart_sample":
        return await analysis.smart_sample(**arguments)
    elif tool_name == "export_all_articles":
        return await analysis.export_all_articles(**arguments)
    elif tool_name == "analyze_timeline":
        return await analysis.analyze_timeline(**arguments)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


async def _get_today_issues(
    date: str | None = None,
    category: str = "전체",
) -> dict:
    """오늘/특정 날짜의 인기 이슈를 조회합니다."""
    if _client is None:
        raise RuntimeError("Client not initialized")

    valid_categories = {"전체", "AI"}
    if category not in valid_categories:
        raise ValueError(f"지원하지 않는 카테고리입니다: '{category}'")

    raw_data = await _client.get_today_issues(date=date)

    issues_by_date = {}
    for item in raw_data.get("trendList", []):
        item_category = item.get("topic_category", "전체")
        if category != "전체" and item_category != category:
            continue

        date_key = item.get("date", "")
        topic_list = item.get("topic_list", [])

        if topic_list:
            issues_by_date[date_key] = {
                "date": date_key,
                "date_display": f"{item.get('topic_year', '')} {item.get('topic_day', '')}",
                "category": item_category,
                "issues": [
                    {
                        "rank": idx + 1,
                        "title": t.get("topic_text", ""),
                        "article_count": int(t.get("topic_count", 0)),
                        "topic_id": t.get("topic_sn", ""),
                    }
                    for idx, t in enumerate(topic_list)
                ],
            }

    return {
        "query_date": raw_data.get("currentDate"),
        "category": category,
        "results": list(issues_by_date.values()),
        "total_dates": len(issues_by_date),
    }


async def handle_message(message: dict, session_id: Optional[str] = None) -> tuple[Optional[dict], Optional[str]]:
    """Handle a single JSON-RPC message."""
    jsonrpc = message.get("jsonrpc")
    method = message.get("method")
    params = message.get("params", {})
    request_id = message.get("id")

    # Notification (no id) handling
    if request_id is None:
        if method == "notifications/initialized":
            if session_id:
                await handle_initialized(params, session_id)
            return None, session_id
        return None, session_id

    # Request handling
    if method == "initialize":
        result, new_session_id = await handle_initialize(params, request_id)
        return result, new_session_id
    elif method == "tools/list":
        return await handle_tools_list(params, request_id), session_id
    elif method == "tools/call":
        return await handle_tools_call(params, request_id), session_id
    elif method == "ping":
        return jsonrpc_result(request_id, {}), session_id
    else:
        return jsonrpc_error(request_id, JSONRPC_METHOD_NOT_FOUND, f"Method not found: {method}"), session_id


# ============================================================
# HTTP Endpoints
# ============================================================

@app.get("/health")
async def health_check():
    """서버 상태 확인."""
    return {
        "status": "healthy",
        "version": SERVER_VERSION,
        "protocol": PROTOCOL_VERSION,
        "service": SERVER_NAME,
        "cache_stats": _cache.stats() if _cache else None
    }


@app.post("/mcp")
async def handle_mcp_post(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
):
    """
    MCP Streamable HTTP POST endpoint.

    Handles JSON-RPC messages (requests, notifications, responses).
    Returns JSON or SSE stream depending on content.
    """
    # Accept 헤더 확인
    accept = request.headers.get("accept", "")

    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse(
            content=jsonrpc_error(None, JSONRPC_PARSE_ERROR, f"Parse error: {str(e)}"),
            status_code=400
        )

    # 배치 처리 여부 확인
    is_batch = isinstance(body, list)
    messages = body if is_batch else [body]

    responses = []
    new_session_id = mcp_session_id

    for msg in messages:
        result, new_session_id = await handle_message(msg, new_session_id)
        if result is not None:
            responses.append(result)

    # 응답 헤더 설정
    headers = {}
    if new_session_id and new_session_id != mcp_session_id:
        headers["Mcp-Session-Id"] = new_session_id

    # 응답이 없으면 202 Accepted
    if not responses:
        return Response(status_code=202, headers=headers)

    # SSE 스트리밍 지원 여부 확인
    if "text/event-stream" in accept:
        async def event_stream():
            for resp in responses:
                yield f"data: {json.dumps(resp, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                **headers,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    # JSON 응답
    if is_batch:
        return JSONResponse(content=responses, headers=headers)
    else:
        return JSONResponse(content=responses[0] if responses else {}, headers=headers)


@app.get("/mcp")
async def handle_mcp_get(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
):
    """
    MCP Streamable HTTP GET endpoint.

    Returns SSE stream for server-initiated messages (optional).
    """
    accept = request.headers.get("accept", "")

    if "text/event-stream" not in accept:
        raise HTTPException(status_code=406, detail="Accept header must include text/event-stream")

    logger.info("SSE connection established (session: %s)", mcp_session_id[:8] if mcp_session_id else "none")

    async def event_stream():
        """SSE 이벤트 스트림."""
        try:
            # Keep-alive
            while True:
                if await request.is_disconnected():
                    break
                await asyncio.sleep(30)
        except Exception as e:
            logger.error("SSE stream error: %s", e)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# Legacy endpoints for backwards compatibility
@app.get("/sse")
async def legacy_sse(request: Request):
    """Legacy SSE endpoint - redirects to /mcp."""
    return await handle_mcp_get(request, None)


@app.get("/api/tools")
async def legacy_list_tools():
    """Legacy tool list endpoint."""
    return {"tools": [t["name"] for t in TOOLS]}


def main():
    """서버 시작 진입점."""
    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    logger.info("Starting MCP server on %s:%s (protocol: %s)", host, port, PROTOCOL_VERSION)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
