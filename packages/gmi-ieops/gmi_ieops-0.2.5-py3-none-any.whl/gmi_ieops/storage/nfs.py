"""
NFS Userspace Client - Full POSIX File Lock Support

Using ctypes to call libnfs C library, supports:
- Basic file operations (read, write, create, delete, etc.)
- NFSv4 file locks (lockf, fcntl style)
- Thread safety
- Context manager
"""

import ctypes
import ctypes.util
import os
import threading
from contextlib import contextmanager
from typing import Optional, Union, List, Generator
from dataclasses import dataclass
from enum import IntEnum


# ============================================================================
# libnfs C Library Loading and Type Definitions
# ============================================================================

def _load_libnfs():
    """Load libnfs shared library"""
    # Try multiple possible library names
    lib_names = [
        "libnfs.so.14",
        "libnfs.so.13", 
        "libnfs.so",
        "nfs",
    ]
    
    for name in lib_names:
        try:
            if name == "nfs":
                path = ctypes.util.find_library(name)
                if path:
                    return ctypes.CDLL(path)
            else:
                return ctypes.CDLL(name)
        except OSError:
            continue
    
    raise OSError("Failed to load libnfs library. Please install libnfs: apt-get install libnfs-dev")


# Load library
_libnfs = _load_libnfs()

# C type definitions
c_void_p = ctypes.c_void_p
c_char_p = ctypes.c_char_p
c_int = ctypes.c_int
c_int64 = ctypes.c_int64
c_uint64 = ctypes.c_uint64
c_size_t = ctypes.c_size_t


# ============================================================================
# Lock Operation Constants
# ============================================================================

class LockOp(IntEnum):
    """lockf style lock operations"""
    F_LOCK = 0   # Acquire lock (blocking)
    F_TLOCK = 1  # Try to acquire lock (non-blocking)
    F_ULOCK = 2  # Release lock
    F_TEST = 3   # Test lock


class FcntlOp(IntEnum):
    """fcntl style lock operations"""
    F_SETLK = 0   # Non-blocking set lock
    F_SETLKW = 1  # Blocking set lock


class LockType(IntEnum):
    """Lock types"""
    F_RDLCK = 0  # Read lock (shared)
    F_WRLCK = 1  # Write lock (exclusive)
    F_UNLCK = 2  # Unlock


class Whence(IntEnum):
    """seek origin position"""
    SEEK_SET = 0
    SEEK_CUR = 1
    SEEK_END = 2


# ============================================================================
# fcntl Lock Structure
# ============================================================================

class NFSFlock(ctypes.Structure):
    """NFS fcntl lock structure"""
    _fields_ = [
        ("l_type", c_int),      # F_RDLCK, F_WRLCK, F_UNLCK
        ("l_whence", c_int),    # SEEK_SET, SEEK_CUR, SEEK_END
        ("l_start", c_uint64),  # Lock start position
        ("l_len", c_uint64),    # Lock length, 0 means to end of file
        ("l_pid", c_int),       # PID of lock holder (only for F_GETLK)
    ]


# ============================================================================
# Define libnfs C Function Signatures
# ============================================================================

# Context management
_libnfs.nfs_init_context.argtypes = []
_libnfs.nfs_init_context.restype = c_void_p

_libnfs.nfs_destroy_context.argtypes = [c_void_p]
_libnfs.nfs_destroy_context.restype = None

_libnfs.nfs_get_error.argtypes = [c_void_p]
_libnfs.nfs_get_error.restype = c_char_p

# Mount
_libnfs.nfs_mount.argtypes = [c_void_p, c_char_p, c_char_p]
_libnfs.nfs_mount.restype = c_int

# File operations
_libnfs.nfs_open.argtypes = [c_void_p, c_char_p, c_int, ctypes.POINTER(c_void_p)]
_libnfs.nfs_open.restype = c_int

_libnfs.nfs_close.argtypes = [c_void_p, c_void_p]
_libnfs.nfs_close.restype = c_int

_libnfs.nfs_creat.argtypes = [c_void_p, c_char_p, c_int, ctypes.POINTER(c_void_p)]
_libnfs.nfs_creat.restype = c_int

_libnfs.nfs_read.argtypes = [c_void_p, c_void_p, c_uint64, c_char_p]
_libnfs.nfs_read.restype = c_int

_libnfs.nfs_write.argtypes = [c_void_p, c_void_p, c_uint64, c_char_p]
_libnfs.nfs_write.restype = c_int

_libnfs.nfs_lseek.argtypes = [c_void_p, c_void_p, c_int64, c_int, ctypes.POINTER(c_uint64)]
_libnfs.nfs_lseek.restype = c_int

_libnfs.nfs_ftruncate.argtypes = [c_void_p, c_void_p, c_uint64]
_libnfs.nfs_ftruncate.restype = c_int

_libnfs.nfs_fsync.argtypes = [c_void_p, c_void_p]
_libnfs.nfs_fsync.restype = c_int

# Lock operations
_libnfs.nfs_lockf.argtypes = [c_void_p, c_void_p, c_int, c_uint64]
_libnfs.nfs_lockf.restype = c_int

_libnfs.nfs_fcntl.argtypes = [c_void_p, c_void_p, c_int, c_void_p]
_libnfs.nfs_fcntl.restype = c_int

# Directory operations
_libnfs.nfs_mkdir.argtypes = [c_void_p, c_char_p]
_libnfs.nfs_mkdir.restype = c_int

_libnfs.nfs_rmdir.argtypes = [c_void_p, c_char_p]
_libnfs.nfs_rmdir.restype = c_int

_libnfs.nfs_opendir.argtypes = [c_void_p, c_char_p, ctypes.POINTER(c_void_p)]
_libnfs.nfs_opendir.restype = c_int

_libnfs.nfs_closedir.argtypes = [c_void_p, c_void_p]
_libnfs.nfs_closedir.restype = None

# File management
_libnfs.nfs_unlink.argtypes = [c_void_p, c_char_p]
_libnfs.nfs_unlink.restype = c_int

_libnfs.nfs_rename.argtypes = [c_void_p, c_char_p, c_char_p]
_libnfs.nfs_rename.restype = c_int

_libnfs.nfs_symlink.argtypes = [c_void_p, c_char_p, c_char_p]
_libnfs.nfs_symlink.restype = c_int

_libnfs.nfs_link.argtypes = [c_void_p, c_char_p, c_char_p]
_libnfs.nfs_link.restype = c_int

_libnfs.nfs_chmod.argtypes = [c_void_p, c_char_p, c_int]
_libnfs.nfs_chmod.restype = c_int

_libnfs.nfs_chown.argtypes = [c_void_p, c_char_p, c_int, c_int]
_libnfs.nfs_chown.restype = c_int

_libnfs.nfs_truncate.argtypes = [c_void_p, c_char_p, c_uint64]
_libnfs.nfs_truncate.restype = c_int


# ============================================================================
# nfs_stat64 Structure
# ============================================================================

class NFSStat64(ctypes.Structure):
    """NFS file status structure"""
    _fields_ = [
        ("nfs_dev", c_uint64),
        ("nfs_ino", c_uint64),
        ("nfs_mode", c_uint64),
        ("nfs_nlink", c_uint64),
        ("nfs_uid", c_uint64),
        ("nfs_gid", c_uint64),
        ("nfs_rdev", c_uint64),
        ("nfs_size", c_uint64),
        ("nfs_blksize", c_uint64),
        ("nfs_blocks", c_uint64),
        ("nfs_atime", c_uint64),
        ("nfs_mtime", c_uint64),
        ("nfs_ctime", c_uint64),
        ("nfs_atime_nsec", c_uint64),
        ("nfs_mtime_nsec", c_uint64),
        ("nfs_ctime_nsec", c_uint64),
        ("nfs_used", c_uint64),
    ]


_libnfs.nfs_stat64.argtypes = [c_void_p, c_char_p, ctypes.POINTER(NFSStat64)]
_libnfs.nfs_stat64.restype = c_int

_libnfs.nfs_fstat64.argtypes = [c_void_p, c_void_p, ctypes.POINTER(NFSStat64)]
_libnfs.nfs_fstat64.restype = c_int

_libnfs.nfs_lstat64.argtypes = [c_void_p, c_char_p, ctypes.POINTER(NFSStat64)]
_libnfs.nfs_lstat64.restype = c_int


# ============================================================================
# nfsdirent Structure (for directory traversal)
# ============================================================================

class NFSDirent(ctypes.Structure):
    """NFS directory entry structure"""
    pass

NFSDirent._fields_ = [
    ("next", ctypes.POINTER(NFSDirent)),
    ("name", c_char_p),
    ("inode", c_uint64),
    ("type", c_int),
    ("mode", c_int),
    ("size", c_uint64),
    ("atime", c_uint64),
    ("mtime", c_uint64),
    ("ctime", c_uint64),
    ("uid", c_uint64),
    ("gid", c_uint64),
    ("nlink", c_uint64),
    ("dev", c_uint64),
    ("rdev", c_uint64),
    ("blksize", c_uint64),
    ("blocks", c_uint64),
    ("used", c_uint64),
    ("atime_nsec", c_uint64),
    ("mtime_nsec", c_uint64),
    ("ctime_nsec", c_uint64),
]

_libnfs.nfs_readdir.argtypes = [c_void_p, c_void_p]
_libnfs.nfs_readdir.restype = ctypes.POINTER(NFSDirent)


# ============================================================================
# Exception Classes
# ============================================================================

class NFSError(Exception):
    """NFS operation error"""
    def __init__(self, message: str, errno: int = 0):
        self.errno = errno
        super().__init__(message)


class NFSLockError(NFSError):
    """NFS lock error"""
    pass


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class FileStat:
    """File status information"""
    size: int
    mode: int
    uid: int
    gid: int
    atime: int
    mtime: int
    ctime: int
    nlink: int
    ino: int
    dev: int
    blocks: int
    blksize: int
    
    @property
    def is_dir(self) -> bool:
        import stat
        return stat.S_ISDIR(self.mode)
    
    @property
    def is_file(self) -> bool:
        import stat
        return stat.S_ISREG(self.mode)
    
    @property
    def is_link(self) -> bool:
        import stat
        return stat.S_ISLNK(self.mode)


@dataclass
class DirEntry:
    """Directory entry"""
    name: str
    inode: int
    type: int
    mode: int
    size: int


# ============================================================================
# NFS Context Class (Low-level)
# ============================================================================

class NFSContext:
    """NFS connection context (low-level wrapper)"""
    
    def __init__(self, server: str, export: str):
        """
        Initialize NFS connection
        
        Args:
            server: NFS server address
            export: Export path
        """
        self._ctx = _libnfs.nfs_init_context()
        if not self._ctx:
            raise NFSError("Failed to initialize NFS context")
        
        self._server = server
        self._export = export
        self._mounted = False
        self._lock = threading.Lock()
        
        # Mount
        ret = _libnfs.nfs_mount(
            self._ctx,
            server.encode('utf-8'),
            export.encode('utf-8')
        )
        if ret != 0:
            error = self._get_error()
            _libnfs.nfs_destroy_context(self._ctx)
            raise NFSError(f"NFS mount failed: {error}", ret)
        
        self._mounted = True
    
    def _get_error(self) -> str:
        """Get last error message"""
        err = _libnfs.nfs_get_error(self._ctx)
        if err:
            return err.decode('utf-8', errors='replace')
        return "Unknown error"
    
    def _check_ret(self, ret: int, operation: str):
        """Check return value, raise exception on failure"""
        if ret < 0:
            raise NFSError(f"{operation} failed: {self._get_error()}", ret)
    
    def close(self):
        """Close connection"""
        if self._ctx:
            _libnfs.nfs_destroy_context(self._ctx)
            self._ctx = None
            self._mounted = False
    
    def __del__(self):
        self.close()
    
    # ============ File Operations ============
    
    def open(self, path: str, flags: int) -> c_void_p:
        """Open file, return file handle"""
        fh = c_void_p()
        ret = _libnfs.nfs_open(
            self._ctx,
            path.encode('utf-8'),
            flags,
            ctypes.byref(fh)
        )
        self._check_ret(ret, f"Open file {path}")
        return fh
    
    def creat(self, path: str, mode: int = 0o644) -> c_void_p:
        """Create file, return file handle"""
        fh = c_void_p()
        ret = _libnfs.nfs_creat(
            self._ctx,
            path.encode('utf-8'),
            mode,
            ctypes.byref(fh)
        )
        self._check_ret(ret, f"Create file {path}")
        return fh
    
    def close_file(self, fh: c_void_p):
        """Close file"""
        ret = _libnfs.nfs_close(self._ctx, fh)
        self._check_ret(ret, "Close file")
    
    def read(self, fh: c_void_p, count: int) -> bytes:
        """Read data"""
        buf = ctypes.create_string_buffer(count)
        ret = _libnfs.nfs_read(self._ctx, fh, count, buf)
        self._check_ret(ret, "Read file")
        return buf.raw[:ret]
    
    def write(self, fh: c_void_p, data: bytes) -> int:
        """Write data, return bytes written"""
        ret = _libnfs.nfs_write(self._ctx, fh, len(data), data)
        self._check_ret(ret, "Write file")
        return ret
    
    def lseek(self, fh: c_void_p, offset: int, whence: int) -> int:
        """Move file pointer, return new position"""
        new_offset = c_uint64()
        ret = _libnfs.nfs_lseek(self._ctx, fh, offset, whence, ctypes.byref(new_offset))
        self._check_ret(ret, "Seek file")
        return new_offset.value
    
    def ftruncate(self, fh: c_void_p, length: int):
        """Truncate file"""
        ret = _libnfs.nfs_ftruncate(self._ctx, fh, length)
        self._check_ret(ret, "Truncate file")
    
    def fsync(self, fh: c_void_p):
        """Sync file to disk"""
        ret = _libnfs.nfs_fsync(self._ctx, fh)
        self._check_ret(ret, "Sync file")
    
    def fstat(self, fh: c_void_p) -> FileStat:
        """Get file status (via handle)"""
        st = NFSStat64()
        ret = _libnfs.nfs_fstat64(self._ctx, fh, ctypes.byref(st))
        self._check_ret(ret, "Get file status")
        return self._stat_to_filestat(st)
    
    # ============ Lock Operations ============
    
    def lockf(self, fh: c_void_p, op: LockOp, count: int = 0) -> bool:
        """
        lockf style file lock
        
        Args:
            fh: File handle
            op: Lock operation (LockOp.F_LOCK, F_TLOCK, F_ULOCK, F_TEST)
            count: Bytes to lock, 0 means from current position to end of file
            
        Returns:
            True on success
            
        Raises:
            NFSLockError: On lock operation failure
        """
        ret = _libnfs.nfs_lockf(self._ctx, fh, int(op), count)
        if ret < 0:
            if op == LockOp.F_TLOCK and ret == -11:  # EAGAIN
                return False
            raise NFSLockError(f"Lock operation failed: {self._get_error()}", ret)
        return True
    
    def fcntl_lock(self, fh: c_void_p, cmd: FcntlOp, 
                   lock_type: LockType, start: int = 0, 
                   length: int = 0, whence: Whence = Whence.SEEK_SET) -> bool:
        """
        fcntl style file lock (supports byte range locks)
        
        Args:
            fh: File handle
            cmd: Lock command (FcntlOp.F_SETLK non-blocking, F_SETLKW blocking)
            lock_type: Lock type (LockType.F_RDLCK, F_WRLCK, F_UNLCK)
            start: Lock start position
            length: Lock length, 0 means to end of file
            whence: Reference position for start
            
        Returns:
            True on success
            
        Raises:
            NFSLockError: On lock operation failure
        """
        flock = NFSFlock()
        flock.l_type = int(lock_type)
        flock.l_whence = int(whence)
        flock.l_start = start
        flock.l_len = length
        flock.l_pid = 0
        
        ret = _libnfs.nfs_fcntl(self._ctx, fh, int(cmd), ctypes.byref(flock))
        if ret < 0:
            if cmd == FcntlOp.F_SETLK and ret == -11:  # EAGAIN
                return False
            raise NFSLockError(f"fcntl lock operation failed: {self._get_error()}", ret)
        return True
    
    # ============ Directory Operations ============
    
    def mkdir(self, path: str):
        """Create directory"""
        ret = _libnfs.nfs_mkdir(self._ctx, path.encode('utf-8'))
        self._check_ret(ret, f"Create directory {path}")
    
    def rmdir(self, path: str):
        """Remove directory"""
        ret = _libnfs.nfs_rmdir(self._ctx, path.encode('utf-8'))
        self._check_ret(ret, f"Remove directory {path}")
    
    def listdir(self, path: str) -> List[DirEntry]:
        """List directory contents"""
        dirh = c_void_p()
        ret = _libnfs.nfs_opendir(self._ctx, path.encode('utf-8'), ctypes.byref(dirh))
        self._check_ret(ret, f"Open directory {path}")
        
        entries = []
        try:
            while True:
                dirent = _libnfs.nfs_readdir(self._ctx, dirh)
                if not dirent:
                    break
                d = dirent.contents
                name = d.name.decode('utf-8') if d.name else ""
                if name and name not in ('.', '..'):
                    entries.append(DirEntry(
                        name=name,
                        inode=d.inode,
                        type=d.type,
                        mode=d.mode,
                        size=d.size
                    ))
        finally:
            _libnfs.nfs_closedir(self._ctx, dirh)
        
        return entries
    
    # ============ File Management ============
    
    def unlink(self, path: str):
        """Delete file"""
        ret = _libnfs.nfs_unlink(self._ctx, path.encode('utf-8'))
        self._check_ret(ret, f"Delete file {path}")
    
    def rename(self, old_path: str, new_path: str):
        """Rename file"""
        ret = _libnfs.nfs_rename(
            self._ctx,
            old_path.encode('utf-8'),
            new_path.encode('utf-8')
        )
        self._check_ret(ret, f"Rename {old_path} -> {new_path}")
    
    def stat(self, path: str) -> FileStat:
        """Get file status"""
        st = NFSStat64()
        ret = _libnfs.nfs_stat64(self._ctx, path.encode('utf-8'), ctypes.byref(st))
        self._check_ret(ret, f"Get file status {path}")
        return self._stat_to_filestat(st)
    
    def lstat(self, path: str) -> FileStat:
        """Get file status (do not follow symlinks)"""
        st = NFSStat64()
        ret = _libnfs.nfs_lstat64(self._ctx, path.encode('utf-8'), ctypes.byref(st))
        self._check_ret(ret, f"Get file status {path}")
        return self._stat_to_filestat(st)
    
    def chmod(self, path: str, mode: int):
        """Change file permissions"""
        ret = _libnfs.nfs_chmod(self._ctx, path.encode('utf-8'), mode)
        self._check_ret(ret, f"Change permissions {path}")
    
    def chown(self, path: str, uid: int, gid: int):
        """Change file owner"""
        ret = _libnfs.nfs_chown(self._ctx, path.encode('utf-8'), uid, gid)
        self._check_ret(ret, f"Change owner {path}")
    
    def truncate(self, path: str, length: int):
        """Truncate file"""
        ret = _libnfs.nfs_truncate(self._ctx, path.encode('utf-8'), length)
        self._check_ret(ret, f"Truncate file {path}")
    
    def symlink(self, target: str, link_path: str):
        """Create symbolic link"""
        ret = _libnfs.nfs_symlink(
            self._ctx,
            target.encode('utf-8'),
            link_path.encode('utf-8')
        )
        self._check_ret(ret, f"Create symlink {link_path}")
    
    def link(self, old_path: str, new_path: str):
        """Create hard link"""
        ret = _libnfs.nfs_link(
            self._ctx,
            old_path.encode('utf-8'),
            new_path.encode('utf-8')
        )
        self._check_ret(ret, f"Create hard link {new_path}")
    
    def _stat_to_filestat(self, st: NFSStat64) -> FileStat:
        """Convert NFSStat64 to FileStat"""
        return FileStat(
            size=st.nfs_size,
            mode=st.nfs_mode,
            uid=st.nfs_uid,
            gid=st.nfs_gid,
            atime=st.nfs_atime,
            mtime=st.nfs_mtime,
            ctime=st.nfs_ctime,
            nlink=st.nfs_nlink,
            ino=st.nfs_ino,
            dev=st.nfs_dev,
            blocks=st.nfs_blocks,
            blksize=st.nfs_blksize
        )


# ============================================================================
# NFS File Object (High-level Wrapper)
# ============================================================================

class NFSFile:
    """
    NFS File Object
    
    Simulates Python native file object, supports:
    - Read/write operations
    - seek/tell
    - File locks (lockf/fcntl style)
    - Context manager
    """
    
    def __init__(self, ctx: NFSContext, path: str, mode: str = 'r',
                 encoding: Optional[str] = None, errors: Optional[str] = None):
        """
        Open NFS file
        
        Args:
            ctx: NFS context
            path: File path
            mode: Open mode ('r', 'w', 'a', 'r+', 'w+', 'a+', with 'b' for binary)
            encoding: Text encoding (default: 'utf-8', ignored in binary mode)
            errors: Encoding error handling ('strict', 'ignore', 'replace', etc.)
        """
        self._ctx = ctx
        self._path = path
        self._mode = mode
        self._binary = 'b' in mode
        self._encoding = None if self._binary else (encoding or 'utf-8')
        self._errors = None if self._binary else (errors or 'strict')
        self._closed = False
        self._lock_held = False
        
        # Parse mode to flags
        flags = self._parse_mode(mode)
        
        # Open file
        self._fh = ctx.open(path, flags)
        
        # Append mode: move to end of file
        if 'a' in mode:
            ctx.lseek(self._fh, 0, Whence.SEEK_END)
    
    def _parse_mode(self, mode: str) -> int:
        """Parse mode string to open flags"""
        mode = mode.replace('b', '')
        
        if mode == 'r':
            return os.O_RDONLY
        elif mode == 'w':
            return os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        elif mode == 'a':
            return os.O_WRONLY | os.O_CREAT | os.O_APPEND
        elif mode in ('r+', 'rw'):
            return os.O_RDWR
        elif mode == 'w+':
            return os.O_RDWR | os.O_CREAT | os.O_TRUNC
        elif mode == 'a+':
            return os.O_RDWR | os.O_CREAT | os.O_APPEND
        elif mode == 'x':
            return os.O_WRONLY | os.O_CREAT | os.O_EXCL
        elif mode == 'x+':
            return os.O_RDWR | os.O_CREAT | os.O_EXCL
        else:
            raise ValueError(f"Invalid mode: {mode}")
    
    @property
    def closed(self) -> bool:
        return self._closed
    
    @property
    def mode(self) -> str:
        return self._mode
    
    @property
    def name(self) -> str:
        return self._path
    
    @property
    def encoding(self) -> Optional[str]:
        return self._encoding
    
    @property
    def errors(self) -> Optional[str]:
        return self._errors
    
    def read(self, size: int = -1) -> Union[bytes, str]:
        """Read data"""
        if self._closed:
            raise ValueError("I/O operation on closed file")
        
        if size == -1:
            # Read all
            st = self._ctx.fstat(self._fh)
            pos = self.tell()
            size = st.size - pos
        
        if size <= 0:
            return b'' if self._binary else ''
        
        data = self._ctx.read(self._fh, size)
        
        if self._binary:
            return data
        return data.decode(self._encoding, errors=self._errors)
    
    def readline(self, size: int = -1) -> Union[bytes, str]:
        """Read a line"""
        line = []
        while True:
            char = self.read(1)
            if not char:
                break
            line.append(char)
            if char == (b'\n' if self._binary else '\n'):
                break
            if size > 0 and len(line) >= size:
                break
        
        if self._binary:
            return b''.join(line)
        return ''.join(line)
    
    def readlines(self) -> List[Union[bytes, str]]:
        """Read all lines"""
        lines = []
        while True:
            line = self.readline()
            if not line:
                break
            lines.append(line)
        return lines
    
    def write(self, data: Union[bytes, str]) -> int:
        """Write data"""
        if self._closed:
            raise ValueError("I/O operation on closed file")
        
        if isinstance(data, str):
            data = data.encode(self._encoding or 'utf-8', errors=self._errors or 'strict')
        
        return self._ctx.write(self._fh, data)
    
    def writelines(self, lines):
        """Write multiple lines"""
        for line in lines:
            self.write(line)
    
    def seek(self, offset: int, whence: int = 0) -> int:
        """Move file pointer"""
        if self._closed:
            raise ValueError("I/O operation on closed file")
        return self._ctx.lseek(self._fh, offset, whence)
    
    def tell(self) -> int:
        """Return current position"""
        return self._ctx.lseek(self._fh, 0, Whence.SEEK_CUR)
    
    def truncate(self, size: Optional[int] = None) -> int:
        """Truncate file"""
        if size is None:
            size = self.tell()
        self._ctx.ftruncate(self._fh, size)
        return size
    
    def flush(self):
        """Flush buffer"""
        if not self._closed:
            self._ctx.fsync(self._fh)
    
    def fileno(self) -> int:
        """Return file descriptor (actually returns handle value)"""
        return self._fh.value if self._fh else -1
    
    def isatty(self) -> bool:
        return False
    
    def readable(self) -> bool:
        return 'r' in self._mode or '+' in self._mode
    
    def writable(self) -> bool:
        return 'w' in self._mode or 'a' in self._mode or '+' in self._mode
    
    def seekable(self) -> bool:
        return True
    
    # ============ Lock Operations ============
    
    def lock(self, exclusive: bool = True, blocking: bool = True, 
             start: int = 0, length: int = 0) -> bool:
        """
        Acquire file lock
        
        Args:
            exclusive: True for exclusive lock, False for shared lock
            blocking: True for blocking mode, False for non-blocking
            start: Lock start position (0 means from file start)
            length: Lock length (0 means to end of file)
            
        Returns:
            True on success, may return False in non-blocking mode
        """
        if self._closed:
            raise ValueError("I/O operation on closed file")
        
        lock_type = LockType.F_WRLCK if exclusive else LockType.F_RDLCK
        cmd = FcntlOp.F_SETLKW if blocking else FcntlOp.F_SETLK
        
        result = self._ctx.fcntl_lock(self._fh, cmd, lock_type, start, length)
        if result:
            self._lock_held = True
        return result
    
    def unlock(self, start: int = 0, length: int = 0) -> bool:
        """
        Release file lock
        
        Args:
            start: Unlock start position
            length: Unlock length (0 means to end of file)
        """
        if self._closed:
            return False
        
        result = self._ctx.fcntl_lock(
            self._fh, FcntlOp.F_SETLK, LockType.F_UNLCK, start, length
        )
        if result:
            self._lock_held = False
        return result
    
    def try_lock(self, exclusive: bool = True, 
                 start: int = 0, length: int = 0) -> bool:
        """
        Try to acquire lock (non-blocking)
        
        Returns:
            True on success, False if lock is held by others
        """
        return self.lock(exclusive=exclusive, blocking=False, 
                        start=start, length=length)
    
    # ============ Context Manager ============
    
    def close(self):
        """Close file"""
        if not self._closed:
            if self._lock_held:
                try:
                    self.unlock()
                except:
                    pass
            self._ctx.close_file(self._fh)
            self._closed = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def __iter__(self):
        return self
    
    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line


# ============================================================================
# NFS FileSystem Class (High-level Wrapper)
# ============================================================================

class NFSFileSystem:
    """
    NFS FileSystem Client
    
    Provides os/pathlib-like file system operation interface, supports:
    - File read/write
    - Directory operations
    - File locks (distributed locks)
    - Thread safety
    """
    
    def __init__(self, server: str, export: str = "/"):
        """
        Connect to NFS server
        
        Args:
            server: NFS server address (IP or hostname)
            export: Export path
        """
        self._server = server
        self._export = export
        self._local = threading.local()
    
    @property
    def _ctx(self) -> NFSContext:
        """Get current thread's NFS context (thread-safe)"""
        if not hasattr(self._local, 'ctx') or self._local.ctx is None:
            self._local.ctx = NFSContext(self._server, self._export)
        return self._local.ctx
    
    def close(self):
        """Close connection"""
        if hasattr(self._local, 'ctx') and self._local.ctx:
            self._local.ctx.close()
            self._local.ctx = None
    
    # ============ File Operations ============
    
    def open(self, path: str, mode: str = 'r', 
             encoding: Optional[str] = None, errors: Optional[str] = None) -> NFSFile:
        """
        Open file
        
        Args:
            path: File path
            mode: Open mode ('r', 'w', 'a', 'r+', 'w+', 'a+', with 'b')
            encoding: Text encoding (default: 'utf-8', ignored in binary mode)
            errors: Encoding error handling ('strict', 'ignore', 'replace', etc.)
        """
        return NFSFile(self._ctx, path, mode, encoding, errors)
    
    # ============ Locked Operations ============
    
    @contextmanager
    def locked_open(self, path: str, mode: str = 'r', 
                    exclusive: bool = True, blocking: bool = True):
        """
        Open file with lock (context manager)
        
        Args:
            path: File path
            mode: Open mode
            exclusive: Whether exclusive lock
            blocking: Whether blocking wait
            
        Usage:
            with fs.locked_open('/data/file.txt', 'rw') as f:
                content = f.read()
                f.seek(0)
                f.write(new_content)
        """
        f = self.open(path, mode)
        try:
            if not f.lock(exclusive=exclusive, blocking=blocking):
                raise NFSLockError(f"Failed to acquire file lock: {path}")
            yield f
        finally:
            f.close()
    
    @contextmanager
    def lock_file(self, path: str, exclusive: bool = True, 
                  blocking: bool = True, timeout: float = None):
        """
        Lock file (without opening content)
        
        For scenarios requiring mutual exclusion without reading/writing file content
        
        Args:
            path: File path (must exist)
            exclusive: Whether exclusive lock
            blocking: Whether blocking
            timeout: Timeout in seconds (only effective in non-blocking mode)
        """
        f = self.open(path, 'r')
        try:
            if timeout and not blocking:
                import time
                start = time.time()
                while not f.try_lock(exclusive=exclusive):
                    if time.time() - start > timeout:
                        raise NFSLockError(f"Lock timeout: {path}")
                    time.sleep(0.1)
            else:
                if not f.lock(exclusive=exclusive, blocking=blocking):
                    raise NFSLockError(f"Failed to acquire lock: {path}")
            yield
        finally:
            f.close()
    
    # ============ Directory Operations ============
    
    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False):
        """
        Create directory
        
        Args:
            path: Directory path
            parents: Whether to create parent directories
            exist_ok: Whether to ignore if directory exists
        """
        if parents:
            parts = path.strip('/').split('/')
            current = ""
            for part in parts:
                current = current + "/" + part
                if not self.exists(current):
                    try:
                        self._ctx.mkdir(current)
                    except NFSError as e:
                        if not exist_ok or "exist" not in str(e).lower():
                            raise
        else:
            try:
                self._ctx.mkdir(path)
            except NFSError as e:
                if not exist_ok or "exist" not in str(e).lower():
                    raise
    
    def rmdir(self, path: str):
        """Remove empty directory"""
        self._ctx.rmdir(path)
    
    def listdir(self, path: str = "/") -> List[str]:
        """List directory contents (filenames only)"""
        entries = self._ctx.listdir(path)
        return [e.name for e in entries]
    
    def scandir(self, path: str = "/") -> List[DirEntry]:
        """List directory contents (with detailed info)"""
        return self._ctx.listdir(path)
    
    def walk(self, path: str = "/") -> Generator:
        """
        Recursively traverse directory
        
        Yields:
            (dirpath, dirnames, filenames) tuple
        """
        import stat as stat_module
        
        entries = self._ctx.listdir(path)
        dirs = []
        files = []
        
        for entry in entries:
            if stat_module.S_ISDIR(entry.mode):
                dirs.append(entry.name)
            else:
                files.append(entry.name)
        
        yield (path, dirs, files)
        
        for d in dirs:
            subpath = path.rstrip('/') + '/' + d
            yield from self.walk(subpath)
    
    # ============ File Management ============
    
    def exists(self, path: str) -> bool:
        """Check if path exists"""
        try:
            self._ctx.stat(path)
            return True
        except NFSError:
            return False
    
    def isfile(self, path: str) -> bool:
        """Check if path is a file"""
        try:
            st = self._ctx.stat(path)
            return st.is_file
        except NFSError:
            return False
    
    def isdir(self, path: str) -> bool:
        """Check if path is a directory"""
        try:
            st = self._ctx.stat(path)
            return st.is_dir
        except NFSError:
            return False
    
    def islink(self, path: str) -> bool:
        """Check if path is a symbolic link"""
        try:
            st = self._ctx.lstat(path)
            return st.is_link
        except NFSError:
            return False
    
    def stat(self, path: str) -> FileStat:
        """Get file status"""
        return self._ctx.stat(path)
    
    def lstat(self, path: str) -> FileStat:
        """Get file status (do not follow symlinks)"""
        return self._ctx.lstat(path)
    
    def getsize(self, path: str) -> int:
        """Get file size"""
        return self._ctx.stat(path).size
    
    def remove(self, path: str):
        """Remove file"""
        self._ctx.unlink(path)
    
    unlink = remove
    
    def rename(self, src: str, dst: str):
        """Rename/move file"""
        self._ctx.rename(src, dst)
    
    def copy(self, src: str, dst: str, buffer_size: int = 1024 * 1024):
        """Copy file"""
        with self.open(src, 'rb') as src_f:
            with self.open(dst, 'wb') as dst_f:
                while True:
                    data = src_f.read(buffer_size)
                    if not data:
                        break
                    dst_f.write(data)
    
    def chmod(self, path: str, mode: int):
        """Change file permissions"""
        self._ctx.chmod(path, mode)
    
    def chown(self, path: str, uid: int, gid: int):
        """Change file owner"""
        self._ctx.chown(path, uid, gid)
    
    def truncate(self, path: str, length: int):
        """Truncate file"""
        self._ctx.truncate(path, length)
    
    def symlink(self, target: str, link_path: str):
        """Create symbolic link"""
        self._ctx.symlink(target, link_path)
    
    def link(self, src: str, dst: str):
        """Create hard link"""
        self._ctx.link(src, dst)
    
    # ============ Context Manager ============
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # High-level API
    'NFSFileSystem',
    'NFSFile',
    # Data types
    'FileStat',
    'DirEntry',
    # Exception classes
    'NFSError',
    'NFSLockError',
]
