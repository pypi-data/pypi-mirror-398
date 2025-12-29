# pyright: strict, reportUnusedFunction=false

from loguru import logger
import sys
import os
from typing import Optional
from .util import *
import logging


class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._logger = logger
        self._initialized = True
        
    def set_logger(
        self,
        log_path: str = "/var/log/ieops",
        app_name: str = "gmi-ieops-sdk",
        log_level: str = "INFO",
        retention: str = "3 days",
        rotation: str = "00:00",
        compression: str = "zip",
        file_enabled: bool = True
    ) -> None:
        """
        Configure logger settings
        Args:
            log_path: Log storage path
            app_name: Application name
            log_level: Log level
            retention: Log retention period
            rotation: Log rotation time
            compression: Log compression format
            file_enabled: Whether to enable file logging
        """
        # Remove default handlers
        self._logger.remove()
        log_level = log_level.upper()
        # Define log format
        def format_with_trace_id(record: dict) -> str: # type: ignore
            trace_part = f"|trace_id:{record['extra']['trace_id']}" if 'trace_id' in record["extra"] else "" # type: ignore
            level = record['level'].name # type: ignore
            if level == "DEBUG":
                level = "DEBUG"
            elif level == "INFO":
                level = "INFOO"
            elif level == "WARNING":
                level = "WARNN"
            elif level == "ERROR":
                level = "ERROR"
            return "<level>["+level+"]</level> " \
                   "<green>[{time:YYYY-MM-DD HH:mm:ss.SSS}]</green> " \
                   "<cyan>pid:{process}|{file}:{line}"+trace_part+"|app:{extra[app_name]}</cyan> --- " \
                   "<level>{message}</level>\n" # type: ignore
            
        # Add stdout handler
        self._logger.add(
            sys.stdout,
            format=format_with_trace_id, # type: ignore
            level=log_level,
            enqueue=True
        ) # type: ignore
        
        # Ensure log directory exists
        os.makedirs(log_path, exist_ok=True)
        
        # Add file handler
        if file_enabled:
            log_file = os.path.join(log_path, f"{app_name}.{randstr(10)}.log")
            self._logger.add(
                log_file,
                format=format_with_trace_id, # type: ignore
                level=log_level,
                rotation=rotation,
                retention=retention,
                compression=compression,
                enqueue=True,
                encoding="utf-8"
            )   
        
        # Set default app_name
        self._logger = self._logger.bind(app_name=app_name)
    
    def get_logger(self, trace_id: Optional[str] = None):
        """
        Get logger instance with trace_id
        
        Args:
            trace_id: Trace ID, if None the trace_id will not be displayed
        """
        if trace_id:
            return self._logger.bind(trace_id=trace_id)
        return self._logger

log = Logger()

uvicorn_logger = logging.getLogger("uvicorn.error")  # use this logger for uvicorn