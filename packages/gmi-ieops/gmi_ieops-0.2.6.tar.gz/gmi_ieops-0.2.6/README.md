# GMICLOUD-IEOPS Python SDK

> 用于构建可扩展 AI 模型推理服务的统一框架

## 目录

- [概览](#概览)
- [安装](#安装)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [配置管理](#配置管理)
- [API 参考](#api-参考)
- [示例](#示例)
- [详细文档](#详细文档)

---

## 概览

GMICLOUD-IEOPS Python SDK 提供构建推理服务的统一框架：

- **统一服务器基础设施**: 基于 FastAPI 的服务器，支持自动路由注册
- **灵活路由**: 支持 REST API、SSE 流式和 WebSocket
- **Handler 自动检测**: 自动处理同步/异步函数和生成器
- **配置管理**: 集中式环境变量管理，支持类型安全
- **服务注册**: 自动注册到 IEOPS 代理进行负载均衡

### 架构

```
┌─────────────────────────────────────────────────────────────────┐
│  Worker 应用                                                      │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐ │
│  │    Handler    │────▶│    Server     │────▶│   FastAPI     │ │
│  │ (你的逻辑)    │     │ (RouterDef)   │     │   Application │ │
│  └───────────────┘     └───────────────┘     └───────────────┘ │
│                                                      │          │
│                                                      ▼          │
│                                              ┌───────────────┐  │
│                                              │   Uvicorn     │  │
│                                              │   (TCP/Unix)  │  │
│                                              └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  IEOPS Proxy (负载均衡器)                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 安装

### 从 PyPI (推荐)

```bash
pip install gmi-ieops
```

### 从源码 (开发)

```bash
cd sdk
pip install -e .
```

### 依赖

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic

---

## 快速开始

### 1. 创建 Handler

```python
from typing import Dict, Any, AsyncGenerator

class MyHandler:
    """你的推理模型 Handler"""
    
    async def chat_stream(self, query: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """异步生成器用于流式输出"""
        messages = query.get("messages", [])
        response = f"Hello! You said: {messages[-1]['content'] if messages else 'nothing'}"
        
        for char in response:
            yield {
                "results": [{"content": char, "role": "assistant"}],
                "stoped": False,
            }
        
        yield {"stoped": True, "stop_reasons": ["end"]}
    
    def chat_complete(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """同步函数用于单次响应"""
        return {"message": "Hello from sync handler!"}
```

### 2. 创建 Server

```python
from gmi_ieops.handler import Handler, Server, RouterDef, RouterKind
from gmi_ieops.utils import config

def main():
    handler = MyHandler()
    
    server = Server(
        routers={
            "chat": [
                RouterDef(path="stream", handler=handler.chat_stream, kind=RouterKind.SSE),
                RouterDef(path="complete", handler=handler.chat_complete, kind=RouterKind.API),
            ],
        },
        app_name=config.app.name,
    )
    
    Handler(server=server).serve()

if __name__ == "__main__":
    main()
```

### 3. 运行 Server

```bash
# TCP 模式
MODEL_SERVER_HOST=0.0.0.0 MODEL_SERVER_PORT=8080 MODEL_SERVER_SOCKET="" python server.py

# Unix socket 模式 (默认)
python server.py
```

---

## 核心概念

### RouterDef

路由定义，包含路径、处理函数和类型：

```python
from gmi_ieops.handler import RouterDef, RouterKind, HTTPMethod

RouterDef(
    path="chat",                    # 路由路径 (不含前缀)
    handler=model.chat,             # 处理函数
    kind=RouterKind.SSE,            # 路由类型: API, SSE, 或 WS
    method=HTTPMethod.POST,         # HTTP 方法 (默认: POST)
    summary="Chat endpoint",        # OpenAPI 描述
    timeout=300,                    # 请求超时 (覆盖全局配置)
)
```

### RouterKind

| Kind | 说明 | 用途 |
|------|------|------|
| `RouterKind.API` | REST API，返回 JSON | 单次响应端点 |
| `RouterKind.SSE` | Server-Sent Events | 流式文本生成 |
| `RouterKind.WS` | WebSocket | 双向通信 |

### Handler 类型

SDK 自动检测 Handler 类型：

| Handler 类型 | 签名 | 行为 |
|-------------|------|------|
| 异步生成器 | `async def handler(query) -> AsyncGenerator` | 流式输出 |
| 同步生成器 | `def handler(query) -> Generator` | 线程池流式输出 |
| 异步函数 | `async def handler(query) -> Any` | 异步单次响应 |
| 同步函数 | `def handler(query) -> Any` | 线程池单次响应 |

### Server

`Server` 类管理 FastAPI 应用：

```python
server = Server(
    routers={...},                  # 路由定义
    router_config=RouterConfig(     # 全局路由配置
        timeout=600,
        sse_headers={...},
    ),
    prefix="/v1",                   # 路由前缀
    on_startup=startup_callback,    # 启动钩子
    on_shutdown=shutdown_callback,  # 关闭钩子
    enable_cors=True,               # 启用 CORS
    app_name="my-service",          # 应用名称
)
```

---

## 配置管理

### 环境变量

SDK 使用集中式配置管理器。通过 `config` 对象访问：

```python
from gmi_ieops.utils import config

# 应用配置
config.app.name              # APP_NAME (默认: "ieops")

# 服务器配置
config.server.host           # MODEL_SERVER_HOST (默认: "127.0.0.1")
config.server.port           # MODEL_SERVER_PORT (默认: 8001)
config.server.socket         # MODEL_SERVER_SOCKET (默认: "")

# 模型配置
config.model.path            # MODEL_PATH (默认: "")
config.model.name            # MODEL_NAME (默认: "model")
config.model.timeout         # MODEL_TIMEOUT (默认: 600)
config.model.concurrency     # MODEL_THREAD_CONCURRENCY (默认: 8)

# 设备配置
config.device.cuda_visible   # CUDA_VISIBLE_DEVICES (默认: "0")
config.device.device         # DEVICE (默认: "auto")
config.device.torch_dtype    # TORCH_DTYPE (默认: "float16")
```

### Socket vs TCP 模式

```bash
# Unix Socket 模式 (默认，自动生成 socket 路径)
python server.py

# Unix Socket 模式 (自定义路径)
MODEL_SERVER_SOCKET=/var/run/myapp.sock python server.py

# TCP 模式 (设置 socket 为空字符串)
MODEL_SERVER_SOCKET="" MODEL_SERVER_HOST=0.0.0.0 MODEL_SERVER_PORT=8080 python server.py
```

### 自定义环境变量

```python
from gmi_ieops.utils import config

# 获取字符串
value = config.get("MY_CUSTOM_VAR", "default")

# 带类型转换
value_int = config.get_int("MY_INT_VAR", 10)
value_bool = config.get_bool("MY_BOOL_VAR", False)
value_float = config.get_float("MY_FLOAT_VAR", 0.5)
value_list = config.get_list("MY_LIST_VAR", ["a", "b"])
```

---

## API 参考

### gmi_ieops.handler

| 类/函数 | 说明 |
|---------|------|
| `Server` | FastAPI 服务器，带路由管理 |
| `Handler` | 服务生命周期管理器 |
| `RouterDef` | 路由定义数据类 |
| `RouterConfig` | 全局路由配置 |
| `RouterKind` | 路由类型枚举 (API, SSE, WS) |
| `HTTPMethod` | HTTP 方法枚举 |
| `generate_trace_id()` | 生成唯一跟踪 ID |
| `format_error_response()` | 创建统一错误响应 |

### gmi_ieops.utils

| 类/函数 | 说明 |
|---------|------|
| `config` | 全局配置实例 |
| `log` | 日志工具 |
| `randstr()`, `arandstr()` | 随机字符串生成器 |
| `randint()`, `arandint()` | 随机整数生成器 |
| `SubprocessManager` | 子进程生命周期管理器 |

### gmi_ieops.storage

| 类/函数 | 说明 |
|---------|------|
| `FileSystem` | 用户隔离文件系统 |
| `Open()` | 存储工厂函数 |
| `CacheConfig` | 缓存配置 |

---

## 示例

### OpenAI 兼容聊天 API

```python
from gmi_ieops.handler import Handler, Server, RouterDef, RouterKind, HTTPMethod
from gmi_ieops.utils import config

class ChatHandler:
    async def chat_completions(self, query):
        """OpenAI 兼容聊天补全"""
        messages = query.get("messages", [])
        # 你的推理逻辑
        return {
            "id": "chatcmpl-xxx",
            "object": "chat.completion",
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
        }
    
    async def chat_completions_stream(self, query):
        """流式聊天补全"""
        async for token in self.generate_tokens(query):
            yield {
                "id": "chatcmpl-xxx",
                "object": "chat.completion.chunk",
                "choices": [{"delta": {"content": token}}],
            }

def main():
    handler = ChatHandler()
    
    server = Server(
        routers={
            "chat/completions": [
                RouterDef(path="", handler=handler.chat_completions, kind=RouterKind.API),
                RouterDef(path="stream", handler=handler.chat_completions_stream, kind=RouterKind.SSE),
            ],
            "models": [
                RouterDef(path="", handler=handler.list_models, kind=RouterKind.API, method=HTTPMethod.GET),
            ],
        },
        prefix="/v1",
        app_name=config.app.name,
    )
    
    Handler(server=server).serve()
```

### 图像生成 API

```python
class ImageHandler:
    async def txt2img(self, query):
        """文生图"""
        prompt = query.get("prompt", "")
        # 你的扩散逻辑
        return {"images": [{"base64": "..."}]}
    
    async def txt2img_stream(self, query):
        """流式进度更新"""
        for progress in range(0, 101, 10):
            yield {"progress": progress, "status": "generating"}
        yield {"progress": 100, "status": "complete", "images": [...]}

server = Server(
    routers={
        "images": [
            RouterDef(path="generate", handler=handler.txt2img, kind=RouterKind.API),
            RouterDef(path="generate/stream", handler=handler.txt2img_stream, kind=RouterKind.SSE),
        ],
    },
)
```

---

## 错误处理

SDK 提供统一错误处理：

```python
from gmi_ieops.handler import format_error_response
from fastapi import HTTPException

# 在你的 handler 中
async def my_handler(query):
    if not query.get("messages"):
        raise HTTPException(status_code=400, detail="Messages required")
    
    try:
        result = await inference(query)
        return result
    except Exception as e:
        # 会被全局异常处理器捕获
        raise

# 错误响应格式:
# {
#     "message": "错误描述",
#     "type": "error_type"
# }
```

---

## 最佳实践

### 1. Handler 设计

```python
# ✅ 好: 无状态 handler，配置来自构造函数
class Handler:
    def __init__(self, model_path: str = config.model.path):
        self.model = load_model(model_path)

# ❌ 坏: 全局状态
MODEL = None
def handler(query):
    global MODEL
    if MODEL is None:
        MODEL = load_model()
```

### 2. 流式输出

```python
# ✅ 好: 产出增量结果
async def stream_handler(query):
    async for chunk in generate():
        yield {"content": chunk, "stoped": False}
    yield {"stoped": True}

# ❌ 坏: 收集所有再产出
async def bad_stream(query):
    results = []
    async for chunk in generate():
        results.append(chunk)
    yield {"content": "".join(results)}
```

### 3. 错误处理

```python
# ✅ 好: 明确的异常
from fastapi import HTTPException

if not valid_input(query):
    raise HTTPException(status_code=400, detail="Invalid input")

# ✅ 好: 日志用于调试
from gmi_ieops.utils import log

try:
    result = inference(query)
except Exception as e:
    log.get_logger(trace_id=query.get("trace_id")).error(f"Inference error: {e}")
    raise
```

---

## 详细文档

| 文档 | 说明 |
|------|------|
| [NFS 存储指南](docs/nfs-client-guide.md) | 分布式文件系统访问、缓存、锁机制 |
| [Worker 示例](../workers/) | 参考实现 |

