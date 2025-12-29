"""
Storage Module - User-isolated Distributed File System Access

Core feature: Transparent open() interception
- When IEOPS_NFS_SERVER env var is set, all open() calls are automatically 
  routed to NFS: /{pid}/{fs_name}/{oid}/{uid}/{path}
- No code changes needed in user applications

Usage:
    # Automatic interception (enabled by default when IEOPS_NFS_SERVER is set)
    import gmi_ieops.storage  # Enables interception on import
    
    with open("config.json", "w") as f:  # Automatically goes to NFS
        f.write('{"key": "value"}')
    
    # Explicit FileSystem usage
    from gmi_ieops.storage import FileSystem
    
    fs = FileSystem(server="nfs.local")
    with fs.open("data.txt", "w") as f:
        f.write("Hello")
"""

from .filesystem import (
    # High-level API
    FileSystem,
    # Data types (re-exported from nfs module)
    NFSFile,
    FileStat,
    DirEntry,
    # Exception classes
    NFSError,
    NFSLockError,
    # Interception control
    enable_nfs_intercept,
    disable_nfs_intercept,
)

__all__ = [
    # High-level API
    'FileSystem',
    # Data types
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
