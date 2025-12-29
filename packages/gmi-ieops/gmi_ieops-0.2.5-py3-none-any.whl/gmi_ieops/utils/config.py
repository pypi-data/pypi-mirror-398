"""
Environment Variable Configuration Manager

Provides type-safe environment variable access with support for:
- Automatic type conversion (str, int, float, bool, list)
- Default value management
- Environment variable grouping
- Lazy loading (read on first access)

Usage:
```python
from gmi_ieops.utils.config import config

# Access configuration
app_name = config.app.name
timeout = config.model.timeout
port = config.server.port

# Or directly get environment variables
value = config.get("MY_ENV_VAR", default="default_value")
value_int = config.get_int("MY_INT_VAR", default=10)
value_bool = config.get_bool("MY_BOOL_VAR", default=False)
```
"""

import os
from typing import Any, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, field


T = TypeVar('T')


class EnvVar:
    """Environment variable descriptor with lazy loading and type conversion"""
    
    def __init__(
        self, 
        name: str, 
        default: Any = None, 
        type_: type = str,
        description: str = ""
    ):
        self.name = name
        self.default = default
        self.type_ = type_
        self.description = description
        self._value: Any = None
        self._loaded = False
        self._is_set = False  # Whether environment variable is set
    
    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        """Descriptor protocol - return value when accessed from instance"""
        if obj is None:
            return self  # Accessed from class, return descriptor itself
        return self.get()
    
    def _convert(self, value: str) -> Any:
        """Type conversion"""
        if self.type_ == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif self.type_ == int:
            return int(value)
        elif self.type_ == float:
            return float(value)
        elif self.type_ == list:
            return [v.strip() for v in value.split(',') if v.strip()]
        return value
    
    def get(self) -> Any:
        """Get value (lazy loading)"""
        if not self._loaded:
            raw = os.environ.get(self.name)
            if raw is not None:
                self._value = self._convert(raw)
                self._is_set = True
            else:
                self._value = self.default
                self._is_set = False
            self._loaded = True
        return self._value
    
    @property
    def is_set(self) -> bool:
        """Check if environment variable is explicitly set (even if empty)"""
        if not self._loaded:
            self.get()  # Trigger loading
        return self._is_set
    
    def reload(self) -> Any:
        """Reload value"""
        self._loaded = False
        self._is_set = False
        return self.get()


class ConfigGroup:
    """Configuration group base class"""
    
    def __init__(self):
        self._vars: Dict[str, EnvVar] = {}
        # Auto-collect all EnvVar attributes
        for name in dir(self.__class__):
            attr = getattr(self.__class__, name)
            if isinstance(attr, EnvVar):
                self._vars[name] = attr
    
    def __getattribute__(self, name: str) -> Any:
        # Avoid recursion
        if name.startswith('_') or name in ('reload', 'to_dict', 'get_var', 'is_set'):
            return super().__getattribute__(name)
        
        try:
            vars_dict = super().__getattribute__('_vars')
            if name in vars_dict:
                return vars_dict[name].get()
        except AttributeError:
            pass
        
        return super().__getattribute__(name)
    
    def reload(self) -> None:
        """Reload all configurations"""
        for var in self._vars.values():
            var.reload()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {name: var.get() for name, var in self._vars.items()}
    
    def get_var(self, name: str) -> Optional[EnvVar]:
        """Get environment variable descriptor"""
        return self._vars.get(name)
    
    def is_set(self, name: str) -> bool:
        """Check if environment variable is explicitly set"""
        var = self._vars.get(name)
        return var.is_set if var else False


# ========== Configuration Group Definitions ==========

class AppConfig(ConfigGroup):
    """Application configuration"""
    name = EnvVar("APP_NAME", "ieops", str, "Application name")
    

class LogConfig(ConfigGroup):
    """Logging configuration"""
    path = EnvVar("LOG_FILE_PATH", "/var/log/ieops", str, "Log file path")
    level = EnvVar("LOG_LEVEL", "INFO", str, "Log level")
    file_enabled = EnvVar("LOG_FILE_ENABLED", False, bool, "Enable file logging")


class ServerConfig(ConfigGroup):
    """Server configuration"""
    socket = EnvVar("MODEL_SERVER_SOCKET", "", str, "Unix socket path")
    socket_dir = EnvVar("SERVER_SOCKET_DIR", "", str, "Socket directory")
    host = EnvVar("MODEL_SERVER_HOST", "127.0.0.1", str, "Listen address")
    port = EnvVar("MODEL_SERVER_PORT", 8001, int, "Listen port")
    graceful_shutdown_time = EnvVar("GRACEFUL_SHUTDOWN_TIME", 3, int, "Graceful shutdown timeout (seconds)")


class ModelConfig(ConfigGroup):
    """Model configuration"""
    path = EnvVar("MODEL_PATH", "", str, "Model path")
    name = EnvVar("MODEL_NAME", "model", str, "Model name")
    timeout = EnvVar("MODEL_TIMEOUT", 600, int, "Inference timeout (seconds)")
    concurrency = EnvVar("MODEL_THREAD_CONCURRENCY", 8, int, "Concurrency")
    tensor_parallel_size = EnvVar("TENSOR_PARALLEL_SIZE", 1, int, "Tensor parallel size")
    infer_engine = EnvVar("MODEL_INFER_ENGINE", "vllm", str, "Inference engine")
    tokenizer_name = EnvVar("TOKENIZER_NAME", "transformers", str, "Tokenizer type")


class DeviceConfig(ConfigGroup):
    """Device configuration"""
    cuda_visible = EnvVar("CUDA_VISIBLE_DEVICES", "0", str, "Visible GPU devices")
    device = EnvVar("DEVICE", "auto", str, "Compute device (cuda/cpu/auto)")
    torch_dtype = EnvVar("TORCH_DTYPE", "float16", str, "PyTorch data type")


class ApiConfig(ConfigGroup):
    """API configuration"""
    gmi_api_key = EnvVar("GMI_API_KEY", "", str, "GMI API key")


class StorageConfig(ConfigGroup):
    """Storage configuration"""
    nfs_server = EnvVar("IEOPS_NFS_SERVER", "", str, "NFS server address")
    pid = EnvVar("IEOPS_STORAGE_PID", "u-00000000", str, "Storage PID")
    fs_name = EnvVar("IEOPS_STORAGE_FS_NAME", "jfs-dev", str, "Filesystem name")
    oid = EnvVar("IEOPS_STORAGE_OID", "gmicloud.ieops", str, "Organization ID")
    uid = EnvVar("IEOPS_STORAGE_UID", "gmicloud.ieops", str, "User ID")


class RegisterConfig(ConfigGroup):
    """Registration configuration"""
    enabled = EnvVar("REGISTER_ENABLED", True, bool, "Enable registration")
    interval = EnvVar("REGISTER_INTERVAL", 10, int, "Registration interval (seconds)")
    proxy_socket = EnvVar("IEOPS_PROXY_SOCKET", "/var/run/ieops/proxy.sock", str, "Proxy socket")
    brslet_socket = EnvVar("IEOPS_BRSLET_SOCKET", "/var/run/ieops/brslet.sock", str, "Brslet socket")


# ========== Main Configuration Class ==========

class Config:
    """
    Unified Configuration Manager
    
    Usage:
    ```python
    from gmi_ieops.utils.config import config
    
    # Access grouped configurations
    print(config.app.name)
    print(config.server.port)
    print(config.model.timeout)
    
    # Get environment variables directly
    value = config.get("MY_VAR", "default")
    value_int = config.get_int("MY_INT", 10)
    value_bool = config.get_bool("MY_BOOL", False)
    
    # Reload configurations
    config.reload()
    ```
    """
    
    def __init__(self):
        self.app = AppConfig()
        self.log = LogConfig()
        self.server = ServerConfig()
        self.model = ModelConfig()
        self.device = DeviceConfig()
        self.api = ApiConfig()
        self.storage = StorageConfig()
        self.register = RegisterConfig()
    
    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get string environment variable"""
        return os.environ.get(name, default)
    
    def get_int(self, name: str, default: int = 0) -> int:
        """Get integer environment variable"""
        value = os.environ.get(name)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def get_float(self, name: str, default: float = 0.0) -> float:
        """Get float environment variable"""
        value = os.environ.get(name)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    def get_bool(self, name: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.environ.get(name)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_list(self, name: str, default: Optional[List[str]] = None, sep: str = ',') -> List[str]:
        """Get list environment variable"""
        value = os.environ.get(name)
        if value is None:
            return default or []
        return [v.strip() for v in value.split(sep) if v.strip()]
    
    def reload(self) -> None:
        """Reload all configurations"""
        self.app.reload()
        self.log.reload()
        self.server.reload()
        self.model.reload()
        self.device.reload()
        self.api.reload()
        self.storage.reload()
        self.register.reload()
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert to dictionary"""
        return {
            "app": self.app.to_dict(),
            "log": self.log.to_dict(),
            "server": self.server.to_dict(),
            "model": self.model.to_dict(),
            "device": self.device.to_dict(),
            "api": self.api.to_dict(),
            "storage": self.storage.to_dict(),
            "register": self.register.to_dict(),
        }


# Global configuration instance
config = Config()

