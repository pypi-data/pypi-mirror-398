"""
Handler Module - Provides inference server and handlers

Usage:
```python
from gmi_ieops.handler import Handler, Server, RouterDef, RouterKind

server = Server(
    routers={
        "chat": [
            RouterDef(path="stream", handler=model.chat, kind=RouterKind.SSE),
            RouterDef(path="complete", handler=model.complete, kind=RouterKind.API),
        ],
    },
)
Handler(server=server).serve()
```
"""

from .handler import Handler
from .tokenizer import TokenizerPool, TokenizerBase

# Server
from .server import Server, UnifiedServer

# Router core types
from .router import (
    RouterDef,
    RouterConfig,
    RouterKind,
    HTTPMethod,
    generate_trace_id,
    format_error_response,
    # Status codes (for special scenarios like comfyui)
    SERVER_CODE_OK,
    SERVER_CODE_ERROR,
    SERVER_CODE_STOP,
)

__all__ = [
    # Core
    'Handler',
    'Server',
    
    # Router definitions
    'RouterDef',
    'RouterConfig',
    'RouterKind',
    'HTTPMethod',
    
    # Utilities
    'generate_trace_id',
    'format_error_response',
    
    # Status codes
    'SERVER_CODE_OK',
    'SERVER_CODE_ERROR',
    'SERVER_CODE_STOP',
    
    # Tokenizer (needed by specific workers)
    'TokenizerPool',
    'TokenizerBase',
]
