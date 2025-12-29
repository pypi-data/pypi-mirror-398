"""
Utils Module - Provides common utility functions
"""

# Configuration manager (import first)
from .config import config

# Logging
from .log import log, uvicorn_logger

# Random utilities
from .util import randstr, arandstr, randint, arandint, APP_ID

# File operations
from .file import load_json, save_json, save, save_jfs

# Subprocess management
from .subprocess_manager import SubprocessManager, create_http_health_check

# LLM sampling params (import as module)
from . import llm_sampling_params

# Initialize logger with configuration manager
log.set_logger(
    log_path=config.log.path,
    app_name=config.app.name,
    log_level=config.log.level,
    file_enabled=config.log.file_enabled,
)

__all__ = [
    # Configuration manager
    'config',
    
    # Logging
    'log',
    'uvicorn_logger',
    
    # Random utilities
    'randstr',
    'arandstr',
    'randint',
    'arandint',
    'APP_ID',
    
    # File operations
    'load_json',
    'save_json',
    'save',
    'save_jfs',
    
    # Subprocess management
    'SubprocessManager',
    'create_http_health_check',
    
    # LLM sampling params
    'llm_sampling_params',
]
