# /root/code/python/ieops-python/sdk/src/handler/router.py
"""
Router Base Module - Provides route definition and auto-generation

Core Concepts:
- RouterDef: Route definition, contains path, handler, kind, and optional config
- RouterConfig: Global route configuration
- create_router_from_config: Auto-generate FastAPI Router from config

Usage:
```python
from gmi_ieops.handler import RouterDef, RouterConfig, RouterKind, Server

# Basic usage
server = Server(
    routers={
        "v1": [
            RouterDef(path="chat", handler=model.chat, kind=RouterKind.SSE),
            RouterDef(path="complete", handler=model.complete, kind=RouterKind.API),
        ],
    }
)

# Route level config (overrides global config)
server = Server(
    routers={
    "v1": [
        RouterDef(
            path="chat", 
            handler=model.chat, 
                kind=RouterKind.SSE,
            timeout=300,  # Custom timeout
            sse_headers={"X-Custom": "value"},  # Custom SSE headers
        ),
        RouterDef(
            path="quick", 
            handler=model.quick, 
                kind=RouterKind.API,
            timeout=30,  # Different timeout
        ),
    ],
    },
    router_config=RouterConfig(timeout=600),  # Global config
)
```
"""

import json
import asyncio
import inspect
import time
from enum import Enum
from typing import (
    Any, 
    AsyncGenerator, 
    Callable, 
    Dict, 
    Generator,
    List, 
    Optional, 
    TypedDict, 
    Union,
)
from dataclasses import dataclass, field

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse

from ..utils.log import log
from ..utils.util import arandstr


# ========== Status Codes ==========
SERVER_CODE_OK = 0
SERVER_CODE_ERROR = 1
SERVER_CODE_STOP = 2


# ========== Route Type Definitions ==========
class RouterKind(str, Enum):
    """Route type enum"""
    API = "api"
    SSE = "sse"
    WS = "ws"


class HTTPMethod(str, Enum):
    """HTTP method enum (Python 3.10+ compatible)"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

# Handler type: can be async generator, generator, async function, or sync function
HandlerType = Callable[[Dict[str, Any]], Union[
    AsyncGenerator[Any, None],
    Generator[Any, None, None],
    Any,
]]


@dataclass
class RouterDef:
    """
    Route Definition
    
    Attributes:
        path: Route path (without prefix)
        handler: Handler function, supports:
            - async generator: async def handler(query) -> AsyncGenerator
            - sync generator: def handler(query) -> Generator  
            - async function: async def handler(query) -> Any
            - sync function: def handler(query) -> Any
        kind: Interface type
            - "api": REST API, returns JSON
            - "sse": Server-Sent Events streaming
            - "ws": WebSocket
        method: HTTP method, defaults to POST (only for api/sse)
        summary: API description (for OpenAPI docs)
        tags: OpenAPI tags
        
        # Optional config (overrides global RouterConfig)
        timeout: Request timeout (seconds), None uses global config
        sse_headers: SSE response headers, None uses global config
    """
    path: str
    handler: HandlerType
    kind: RouterKind = RouterKind.API
    method: HTTPMethod = HTTPMethod.POST
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    # Optional config (overrides global config)
    timeout: Optional[int] = None
    sse_headers: Optional[Dict[str, str]] = None


# Route group config type: {"group_name": [RouterDef, ...], ...}
RouterGroupConfig = Dict[str, List[RouterDef]]


@dataclass
class RouterConfig:
    """
    Route Configuration
    
    Attributes:
        timeout: Request timeout (seconds)
        enable_cors: Whether to enable CORS
        sse_headers: SSE response headers
    """
    timeout: int = 600
    enable_cors: bool = True
    sse_headers: Dict[str, str] = field(default_factory=lambda: {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })


# ========== Type Definitions ==========

class InferenceResult(TypedDict, total=False):
    """Inference result type"""
    results: list
    stop_reasons: list
    stoped: bool
    token_encode: int
    token_decode: int


class IeopsRequest(TypedDict, total=False):
    """ieops protocol request format"""
    headers: Dict[str, Any]
    payload: Any
    trace_id: str


# StreamGenerator type alias
StreamGenerator = Callable[[Dict[str, Any]], AsyncGenerator[Any, None]]


# ========== Error Classes ==========

class RouterError(Exception):
    """Router error base class"""
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code


class InferenceError(RouterError):
    """Inference error"""
    pass


def format_error_response(
    message: str,
    error_type: str = "internal_error",
) -> Dict[str, Any]:
    """
    Unified error response format
    
    Used for consistent error structure across API, SSE, WebSocket
    """
    return {
        "message": message,
        "type": error_type,
    }


# ========== Utility Functions ==========

async def generate_trace_id() -> str:
    """Generate trace_id"""
    return f"traceid-{await arandstr(8)}"


async def parse_ieops_request(request: Request) -> IeopsRequest:
    """Parse ieops protocol request"""
    body = await request.body()
    
    try:
        request_data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        request_data = {}
    
    if isinstance(request_data, dict) and "headers" in request_data:
        headers = request_data.get("headers", {})
        payload = request_data.get("payload", request_data)
    else:
        headers = {}
        payload = request_data
    
    trace_id = str(headers.get("x-trace-id", await generate_trace_id()))
    
    return IeopsRequest(
        headers=headers,
        payload=payload,
        trace_id=trace_id,
    )


def create_sse_response(
    generator: AsyncGenerator[str, None],
    config: Optional[RouterConfig] = None,
) -> StreamingResponse:
    """Create SSE streaming response"""
    config = config or RouterConfig()
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=config.sse_headers,
    )


def create_json_response(
    data: Any,
    status_code: int = 200,
) -> JSONResponse:
    """Create JSON response"""
    return JSONResponse(content=data, status_code=status_code)


def is_async_gen(func: Callable) -> bool:
    """Check if function is async generator"""
    return inspect.isasyncgenfunction(func)


def is_sync_gen(func: Callable) -> bool:
    """Check if function is sync generator"""
    return inspect.isgeneratorfunction(func)


def is_async_func(func: Callable) -> bool:
    """Check if function is async function"""
    return asyncio.iscoroutinefunction(func)


# ========== Core: Generate Routes from Config ==========

def create_router_from_config(
    config: RouterGroupConfig,
    router_config: Optional[RouterConfig] = None,
    prefix: str = "",
) -> APIRouter:
    """
    Auto-generate FastAPI Router from config
    
    Args:
        config: Route group configuration
            {
                "group_name": [
                    RouterDef(path="xxx", handler=func, kind="api|sse|ws"),
                    ...
                ],
                ...
            }
        router_config: Route configuration (timeout, SSE headers, etc.)
        prefix: Global route prefix
    
    Returns:
        APIRouter instance
    
    Example:
        config = {
            "v1": [
                RouterDef(path="chat", handler=model.chat, kind="sse"),
                RouterDef(path="status", handler=get_status, kind="api"),
            ],
            "ws": [
                RouterDef(path="stream", handler=model.stream, kind="ws"),
            ],
        }
        router = create_router_from_config(config)
        # Generated routes:
        # POST /v1/chat (SSE)
        # POST /v1/status (API)
        # WS /ws/stream (WebSocket)
    """
    router_config = router_config or RouterConfig()
    router = APIRouter(prefix=prefix)
    
    for group_name, routes in config.items():
        group_prefix = f"/{group_name}" if group_name else ""
        
        for route_def in routes:
            _register_route(
                router=router,
                group_prefix=group_prefix,
                route_def=route_def,
                config=router_config,
            )
    
    return router


def _merge_config(global_config: RouterConfig, route_def: RouterDef) -> RouterConfig:
    """Merge global config and route config (route config takes priority)"""
    return RouterConfig(
        timeout=route_def.timeout if route_def.timeout is not None else global_config.timeout,
        enable_cors=global_config.enable_cors,
        sse_headers=route_def.sse_headers if route_def.sse_headers is not None else global_config.sse_headers,
    )


def _register_route(
    router: APIRouter,
    group_prefix: str,
    route_def: RouterDef,
    config: RouterConfig,
) -> None:
    """Register single route"""
    full_path = f"{group_prefix}/{route_def.path}".replace("//", "/")
    handler = route_def.handler
    kind = route_def.kind
    method = route_def.method.upper()
    tags = route_def.tags or []
    summary = route_def.summary or f"{kind.upper()} {full_path}"
    
    # Merge global config and route config
    merged_config = _merge_config(config, route_def)
    
    if kind == RouterKind.API:
        _register_api_route(router, full_path, handler, method, tags, summary, merged_config)
    elif kind == RouterKind.SSE:
        _register_sse_route(router, full_path, handler, method, tags, summary, merged_config)
    elif kind == RouterKind.WS:
        _register_ws_route(router, full_path, handler, tags, summary, merged_config)


def _register_api_route(
    router: APIRouter,
    path: str,
    handler: HandlerType,
    method: str,
    tags: List[str],
    summary: str,
    config: RouterConfig,
) -> None:
    """Register API route"""
    timeout = config.timeout
    
    async def api_endpoint(request: Request):
        trace_id = await generate_trace_id()
        
        try:
            body = await request.body()
            try:
                query = json.loads(body.decode("utf-8")) if body else {}
            except json.JSONDecodeError:
                query = {}
        except Exception:
            query = {}
        
        if isinstance(query, dict):
            query["trace_id"] = trace_id
        else:
            query = {"payload": query, "trace_id": trace_id}
        
        async def _run_handler():
            # Call based on handler type
            if is_async_gen(handler):
                # Async generator: collect all results
                results = []
                async for item in handler(query):
                    if isinstance(item, Exception):
                        return JSONResponse(format_error_response(str(item), "handler_error"), status_code=500)
                    results.append(item)
                return results[-1] if len(results) == 1 else {"results": results}
            
            elif is_sync_gen(handler):
                # Sync generator: execute in thread pool
                loop = asyncio.get_event_loop()
                results = []
                
                def collect_results():
                    for item in handler(query):
                        results.append(item)
                
                await loop.run_in_executor(None, collect_results)
                return results[-1] if len(results) == 1 else {"results": results}
            
            elif is_async_func(handler):
                # Async function
                result = await handler(query)
                return result
            
            else:
                # Sync function
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, handler, query)
                return result
        
        try:
            return await asyncio.wait_for(_run_handler(), timeout=timeout)
        except asyncio.TimeoutError:
            log.get_logger(trace_id=trace_id).error(f"API timeout after {timeout}s")
            return JSONResponse(format_error_response(f"Request timeout after {timeout}s", "timeout_error"), status_code=504)
        except Exception as e:
            log.get_logger(trace_id=trace_id).error(f"API error: {e}")
            return JSONResponse(format_error_response(str(e), "api_error"), status_code=500)
    
    router.add_api_route(
        path,
        api_endpoint,
        methods=[method],
        tags=tags,
        summary=summary,
    )


def _register_sse_route(
    router: APIRouter,
    path: str,
    handler: HandlerType,
    method: str,
    tags: List[str],
    summary: str,
    config: RouterConfig,
) -> None:
    """Register SSE route"""
    timeout = config.timeout
    sse_headers = config.sse_headers
    
    async def sse_endpoint(request: Request):
        trace_id = await generate_trace_id()
        
        try:
            body = await request.body()
            try:
                query = json.loads(body.decode("utf-8")) if body else {}
            except json.JSONDecodeError:
                query = {}
        except Exception:
            query = {}
        
        if isinstance(query, dict):
            query["trace_id"] = trace_id
        else:
            query = {"payload": query, "trace_id": trace_id}
        
        async def sse_generator():
            start_time = time.time()
            try:
                if is_async_gen(handler):
                    # Async generator
                    async for item in handler(query):
                        if time.time() - start_time > timeout:
                            yield f"data: {json.dumps(format_error_response(f'SSE timeout after {timeout}s', 'timeout_error'), ensure_ascii=False)}\n\n"
                            return
                        if isinstance(item, Exception):
                            yield f"data: {json.dumps(format_error_response(str(item), 'handler_error'), ensure_ascii=False)}\n\n"
                            return
                        yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                
                elif is_sync_gen(handler):
                    # Sync generator: execute in thread pool
                    loop = asyncio.get_event_loop()
                    import queue
                    q: queue.Queue = queue.Queue()
                    done = False
                    
                    def run_sync_gen():
                        nonlocal done
                        try:
                            for item in handler(query):
                                q.put(("data", item))
                            q.put(("done", None))
                        except Exception as e:
                            q.put(("error", e))
                        finally:
                            done = True
                    
                    # Start sync generator
                    loop.run_in_executor(None, run_sync_gen)
                    
                    while not done or not q.empty():
                        if time.time() - start_time > timeout:
                            yield f"data: {json.dumps(format_error_response(f'SSE timeout after {timeout}s', 'timeout_error'), ensure_ascii=False)}\n\n"
                            return
                        try:
                            msg_type, item = await asyncio.wait_for(
                                loop.run_in_executor(None, q.get, True, 0.1),
                                timeout=1.0
                            )
                            if msg_type == "data":
                                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                            elif msg_type == "error":
                                yield f"data: {json.dumps(format_error_response(str(item), 'handler_error'), ensure_ascii=False)}\n\n"
                                return
                            elif msg_type == "done":
                                break
                        except (asyncio.TimeoutError, Exception):
                            continue
                
                elif is_async_func(handler):
                    # Async function: single return
                    result = await asyncio.wait_for(handler(query), timeout=timeout)
                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
                
                else:
                    # Sync function
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, handler, query),
                        timeout=timeout
                    )
                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except asyncio.TimeoutError:
                log.get_logger(trace_id=trace_id).error(f"SSE timeout after {timeout}s")
                yield f"data: {json.dumps(format_error_response(f'SSE timeout after {timeout}s', 'timeout_error'), ensure_ascii=False)}\n\n"
            except Exception as e:
                log.get_logger(trace_id=trace_id).error(f"SSE error: {e}")
                yield f"data: {json.dumps(format_error_response(str(e), 'sse_error'), ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers=sse_headers,
        )
    
    router.add_api_route(
        path,
        sse_endpoint,
        methods=[method],
        tags=tags,
        summary=summary,
    )


def _register_ws_route(
    router: APIRouter,
    path: str,
    handler: HandlerType,
    tags: List[str],
    summary: str,
    config: RouterConfig,
) -> None:
    """Register WebSocket route"""
    
    async def ws_endpoint(websocket: WebSocket):
        trace_id = await generate_trace_id()
        logger = log.get_logger(trace_id=trace_id)
        
        await websocket.accept()
        logger.info(f"WebSocket connected: {path}")
        
        try:
            while True:
                # Receive message
                try:
                    data = await websocket.receive_text()
                    try:
                        query = json.loads(data)
                    except json.JSONDecodeError:
                        query = {"message": data}
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected by client")
                    break
                
                if isinstance(query, dict):
                    query["trace_id"] = trace_id
                else:
                    query = {"payload": query, "trace_id": trace_id}
                
                try:
                    if is_async_gen(handler):
                        async for item in handler(query):
                            if isinstance(item, Exception):
                                await websocket.send_json(format_error_response(str(item), "handler_error"))
                                break
                            await websocket.send_json(item)
                    
                    elif is_sync_gen(handler):
                        loop = asyncio.get_event_loop()
                        
                        def run_sync():
                            results = []
                            for item in handler(query):
                                results.append(item)
                            return results
                        
                        results = await loop.run_in_executor(None, run_sync)
                        for item in results:
                            await websocket.send_json(item)
                    
                    elif is_async_func(handler):
                        result = await handler(query)
                        await websocket.send_json(result)
                    
                    else:
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, handler, query)
                        await websocket.send_json(result)
                        
                except Exception as e:
                    logger.error(f"WebSocket handler error: {e}")
                    await websocket.send_json(format_error_response(str(e), "websocket_error"))
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            try:
                await websocket.close()
            except Exception:
                pass
    
    router.add_api_route(
        path,
        ws_endpoint,
        methods=["GET"],  # WebSocket upgrade via GET
        tags=tags,
        summary=summary,
    )
    # Also register WebSocket route
    router.add_websocket_route(path, ws_endpoint)


# ========== Convenience Functions ==========

def create_simple_router(
    routes: List[RouterDef],
    prefix: str = "",
    config: Optional[RouterConfig] = None,
) -> APIRouter:
    """
    Create simple router (no grouping)
    
    Example:
        router = create_simple_router([
            RouterDef(path="chat", handler=model.chat, kind="sse"),
            RouterDef(path="status", handler=get_status, kind="api"),
        ])
    """
    return create_router_from_config(
        config={"": routes},
        router_config=config,
        prefix=prefix,
    )

