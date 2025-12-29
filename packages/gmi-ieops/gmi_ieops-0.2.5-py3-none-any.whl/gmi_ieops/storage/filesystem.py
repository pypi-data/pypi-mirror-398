"""
FileSystem SDK - User-isolated Distributed File System Access

Based on NFS userspace client, provides:
- User directory isolation (pid/fs_name/oid/uid)
- Distributed file locks
- Transparent open() interception (auto-enabled via IEOPS_NFS_SERVER env var)
"""

import os
import builtins
from typing import Optional, Generator, List
from contextlib import contextmanager

from .nfs import (
    NFSFileSystem as BaseNFSFileSystem,
    NFSFile,
    NFSError,
    NFSLockError,
    FileStat,
    DirEntry,
)
from ..utils.config import config


# ============================================================================
# Path Configuration (from config)
# ============================================================================

def _get_base_nfs_path() -> str:
    """Get user base NFS path: /{pid}/{fs_name}/{oid}/{uid}"""
    return f"/{config.storage.pid}/{config.storage.fs_name}/{config.storage.oid}/{config.storage.uid}"


def _create_nfs_path(path: str) -> str:
    """Create NFS path: /{pid}/{fs_name}/{oid}/{uid}/{path}"""
    path = path.strip('/')
    base = _get_base_nfs_path()
    return f"{base}/{path}" if path else base


def _is_path_allowed(nfs_path: str) -> bool:
    """Check if path is within user directory (prevent path traversal attacks)"""
    base = os.path.normpath(_get_base_nfs_path())
    normalized = os.path.normpath(nfs_path)
    return normalized == base or normalized.startswith(base + '/')


def _create_safe_nfs_path(path: str) -> str:
    """Create and validate NFS path, prevent path traversal attacks"""
    nfs_path = _create_nfs_path(path)
    if not _is_path_allowed(nfs_path):
        raise PermissionError(f"Path not allowed (outside user directory): {path}")
    return nfs_path


# ============================================================================
# FileSystem Class
# ============================================================================

class FileSystem:
    """
    User-isolated FileSystem
    
    All paths are prefixed with: /{pid}/{fs_name}/{oid}/{uid}/
    """
    
    def __init__(self, server: str, export: str = "/", auto_mkdir: bool = True):
        self._nfs = BaseNFSFileSystem(server, export)
        if auto_mkdir:
            self._ensure_user_dir()
    
    def _ensure_user_dir(self):
        """Ensure user directory exists"""
        try:
            self._nfs.mkdir(_get_base_nfs_path(), parents=True, exist_ok=True)
        except NFSError:
            pass
    
    @property
    def base_path(self) -> str:
        """User base path"""
        return _get_base_nfs_path()
    
    # ============ File Operations ============
    
    def open(self, path: str, mode: str = 'r', 
             encoding: Optional[str] = None, errors: Optional[str] = None) -> NFSFile:
        """Open file"""
        return self._nfs.open(_create_safe_nfs_path(path), mode, encoding, errors)
    
    @contextmanager
    def locked_open(self, path: str, mode: str = 'r', exclusive: bool = True, blocking: bool = True):
        """Open file with lock (context manager)"""
        with self._nfs.locked_open(_create_safe_nfs_path(path), mode, exclusive, blocking) as f:
            yield f
    
    # ============ Directory Operations ============
    
    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False):
        """Create directory"""
        self._nfs.mkdir(_create_safe_nfs_path(path), parents, exist_ok)
    
    def rmdir(self, path: str):
        """Remove empty directory"""
        self._nfs.rmdir(_create_safe_nfs_path(path))
    
    def listdir(self, path: str = "") -> List[str]:
        """List directory contents"""
        return self._nfs.listdir(_create_safe_nfs_path(path))
    
    def scandir(self, path: str = "") -> List[DirEntry]:
        """List directory contents (with detailed info)"""
        return self._nfs.scandir(_create_safe_nfs_path(path))
    
    def walk(self, path: str = "") -> Generator:
        """Recursively traverse directory"""
        full_path = _create_safe_nfs_path(path)
        base_len = len(_get_base_nfs_path())
        for dirpath, dirnames, filenames in self._nfs.walk(full_path):
            rel_path = dirpath[base_len:].lstrip('/')
            yield (rel_path, dirnames, filenames)
    
    # ============ File Info ============
    
    def exists(self, path: str) -> bool:
        return self._nfs.exists(_create_safe_nfs_path(path))
    
    def isfile(self, path: str) -> bool:
        return self._nfs.isfile(_create_safe_nfs_path(path))
    
    def isdir(self, path: str) -> bool:
        return self._nfs.isdir(_create_safe_nfs_path(path))
    
    def stat(self, path: str) -> FileStat:
        return self._nfs.stat(_create_safe_nfs_path(path))
    
    def getsize(self, path: str) -> int:
        return self._nfs.getsize(_create_safe_nfs_path(path))
    
    # ============ File Management ============
    
    def remove(self, path: str):
        """Remove file"""
        self._nfs.remove(_create_safe_nfs_path(path))
    
    unlink = remove
    
    def rename(self, src: str, dst: str):
        """Rename/move file"""
        self._nfs.rename(_create_safe_nfs_path(src), _create_safe_nfs_path(dst))
    
    def copy(self, src: str, dst: str):
        """Copy file"""
        self._nfs.copy(_create_safe_nfs_path(src), _create_safe_nfs_path(dst))
    
    def chmod(self, path: str, mode: int):
        """Change file permissions"""
        self._nfs.chmod(_create_safe_nfs_path(path), mode)
    
    # ============ Context Manager ============
    
    def close(self):
        self._nfs.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# ============================================================================
# Open Interception - Auto-enabled via IEOPS_NFS_SERVER env var
# ============================================================================

_builtin_open = builtins.open
_global_nfs: Optional[BaseNFSFileSystem] = None


def _intercepted_open(file, mode='r', buffering=-1, encoding=None, 
                      errors=None, newline=None, closefd=True, opener=None):
    """
    Intercepted open function - routes all paths to NFS when IEOPS_NFS_SERVER is set
    
    Supported parameters:
        - file, mode: Fully supported
        - encoding, errors: Supported in text mode
        - buffering, newline, closefd, opener: Ignored (NFS doesn't support)
    """
    global _global_nfs
    
    # IEOPS_NFS_SERVER not set, use native open
    if _global_nfs is None:
        return _builtin_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
    
    # Convert and validate path (prevent path traversal attacks)
    nfs_path = _create_safe_nfs_path(str(file))
    nfs_mode = mode.replace('t', '')
    
    try:
        # Pass encoding and errors parameters
        return _global_nfs.open(nfs_path, nfs_mode, encoding, errors)
    except Exception as e:
        raise IOError(f"Failed to open NFS file '{nfs_path}': {e}")


def enable_nfs_intercept() -> bool:
    """
    Enable NFS open() interception (requires IEOPS_NFS_SERVER environment variable)
    
    Automatically called on module import. Does nothing if IEOPS_NFS_SERVER is not set.
    Once enabled, all open() calls will be routed to NFS: /{pid}/{fs_name}/{oid}/{uid}/{path}
        
    Returns:
        True if enabled successfully, False if IEOPS_NFS_SERVER is not configured
    """
    global _global_nfs
    
    server = config.storage.nfs_server
    if not server:
        return False
    
    if _global_nfs is not None:
        try:
            _global_nfs.close()
        except Exception:
            pass
    
    _global_nfs = BaseNFSFileSystem(server, "/")
    
    # Ensure user directory exists
    try:
        _global_nfs.mkdir(_get_base_nfs_path(), parents=True, exist_ok=True)
    except NFSError:
        pass
    
    builtins.open = _intercepted_open
    return True


def disable_nfs_intercept():
    """Disable NFS open() interception and release resources"""
    global _global_nfs
    
    builtins.open = _builtin_open
    
    if _global_nfs is not None:
        try:
            _global_nfs.close()
        except Exception:
            pass
        _global_nfs = None


# Auto-enable interception on module import
enable_nfs_intercept()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # High-level API
    'FileSystem',
    # Data types (re-exported from nfs module)
    'NFSFile',
    'FileStat',
    'DirEntry',
    # Exception classes
    'NFSError',
    'NFSLockError',
    # Interception control
    'enable_nfs_intercept',
    'disable_nfs_intercept',
]
