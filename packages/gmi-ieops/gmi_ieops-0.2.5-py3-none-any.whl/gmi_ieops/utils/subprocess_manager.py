# /root/code/python/ieops-python/sdk/src/utils/subprocess_manager.py
"""
Generic Subprocess Manager

Provides subprocess startup, shutdown, monitoring, log forwarding, etc.
Can be reused by various Workers (e.g., ComfyUI Worker).

Usage Example:
    manager = SubprocessManager(
        start_cmd="python main.py --port 8188",
        work_dir="/app/comfyui",
        health_check=lambda: check_http("http://localhost:8188/health"),
        startup_timeout=120,
        exit_on_failure=True,
    )
    
    # Start subprocess
    await manager.start()
    
    # Check status
    if manager.is_running:
        print("Process is running")
    
    # Stop subprocess
    await manager.stop()
"""

import asyncio
import atexit
import os
import signal
import subprocess
import sys
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from .log import uvicorn_logger

# Global list of registered subprocess managers for atexit cleanup
_registered_managers: List["SubprocessManager"] = []


def _cleanup_all_subprocesses():
    """atexit callback: cleanup all registered subprocesses"""
    for manager in _registered_managers:
        manager._sync_kill()


# Register atexit cleanup function
atexit.register(_cleanup_all_subprocesses)


class SubprocessManager:
    """
    Generic Subprocess Manager
    
    Features:
    - Start subprocess and wait for ready
    - Forward subprocess logs
    - Background monitoring of subprocess status
    - Graceful subprocess shutdown
    - Optional termination of main process on abnormal exit
    """
    
    def __init__(
        self,
        start_cmd: str,
        work_dir: str,
        *,
        name: str = "subprocess",
        extra_env: Optional[Dict[str, str]] = None,
        health_check: Optional[Callable[[], Coroutine[Any, Any, bool]]] = None,
        startup_timeout: int = 120,
        health_check_interval: float = 1.0,
        monitor_interval: float = 5.0,
        graceful_shutdown_timeout: float = 5.0,
        exit_on_failure: bool = True,
        log_prefix: Optional[str] = None,
    ) -> None:
        """
        Args:
            start_cmd: Startup command, e.g., "python main.py --port 8188"
            work_dir: Working directory
            name: Process name (for logging)
            extra_env: Extra environment variables
            health_check: Health check function, returns True when ready
            startup_timeout: Startup timeout (seconds)
            health_check_interval: Health check interval (seconds)
            monitor_interval: Background monitoring interval (seconds)
            graceful_shutdown_timeout: Graceful shutdown timeout (seconds)
            exit_on_failure: Whether to call sys.exit(1) on subprocess abnormal exit
            log_prefix: Log prefix, defaults to name
        """
        self._start_cmd = start_cmd
        self._work_dir = work_dir
        self._name = name
        self._extra_env = extra_env or {}
        self._health_check = health_check
        self._startup_timeout = startup_timeout
        self._health_check_interval = health_check_interval
        self._monitor_interval = monitor_interval
        self._graceful_shutdown_timeout = graceful_shutdown_timeout
        self._exit_on_failure = exit_on_failure
        self._log_prefix = log_prefix or f"[{name}]"
        
        self._process: Optional[subprocess.Popen] = None
        self._is_ready = False
        self._shutting_down = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._log_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        """Check if subprocess is running"""
        return self._process is not None and self._process.poll() is None

    @property
    def is_ready(self) -> bool:
        """Check if subprocess is ready (via health check)"""
        return self._is_ready

    @property
    def exit_code(self) -> Optional[int]:
        """Get subprocess exit code, returns None if still running"""
        if self._process is None:
            return None
        return self._process.poll()

    @property
    def pid(self) -> Optional[int]:
        """Get subprocess PID"""
        if self._process is None:
            return None
        return self._process.pid

    async def start(self) -> None:
        """
        Start subprocess
        
        1. Start process
        2. Start log forwarding
        3. Wait for health check to pass
        4. Start background monitoring
        
        Raises:
            RuntimeError: Process startup failed or exited during startup
            TimeoutError: Startup timeout
        """
        uvicorn_logger.info(f"{self._log_prefix} Starting: {self._start_cmd}")
        uvicorn_logger.info(f"{self._log_prefix} Work directory: {self._work_dir}")
        
        # Prepare environment variables
        env = os.environ.copy()
        env.update(self._extra_env)
        
        # Start subprocess
        self._process = subprocess.Popen(
            self._start_cmd,
            shell=True,
            cwd=self._work_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=self._setup_child_process,  # Set subprocess attributes
        )
        
        uvicorn_logger.info(f"{self._log_prefix} Started with PID: {self._process.pid}")
        
        # Register to global manager list for atexit cleanup
        _registered_managers.append(self)
        
        # Start log forwarding
        self._log_task = asyncio.create_task(self._forward_logs())
        
        # Wait for health check to pass
        await self._wait_for_ready()
        
        # Start background monitoring
        self._monitor_task = asyncio.create_task(self._monitor_process())
    
    def _setup_child_process(self) -> None:
        """
        Setup before subprocess starts (called after fork, before exec)
        
        1. Create new process group (for killing entire group later)
        2. Set prctl PR_SET_PDEATHSIG (Linux feature: subprocess receives signal when parent dies)
        """
        # Create new process group
        os.setsid()
        
        # Linux feature: set signal subprocess receives when parent dies
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
            PR_SET_PDEATHSIG = 1
            # When parent process dies, subprocess receives SIGKILL
            libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)
        except Exception:
            pass  # Non-Linux system or no prctl support, ignore

    async def stop(self) -> None:
        """
        Gracefully stop subprocess
        
        1. Send SIGTERM
        2. Wait for process to exit
        3. Send SIGKILL after timeout
        """
        self._shutting_down = True
        
        # Cancel monitoring task
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        if not self._process:
            return
        
        uvicorn_logger.info(f"{self._log_prefix} Stopping process...")
        
        try:
            # First try SIGTERM
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            
            # Wait for process to exit
            wait_count = int(self._graceful_shutdown_timeout / 0.5)
            for _ in range(wait_count):
                if self._process.poll() is not None:
                    uvicorn_logger.info(f"{self._log_prefix} Process stopped gracefully")
                    return
                await asyncio.sleep(0.5)
            
            # Force SIGKILL
            uvicorn_logger.warning(f"{self._log_prefix} Force killing process...")
            os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
            self._process.wait()
            uvicorn_logger.info(f"{self._log_prefix} Process killed")
            
        except ProcessLookupError:
            pass  # Process already exited
        except Exception as e:
            uvicorn_logger.error(f"{self._log_prefix} Error stopping process: {e}")
        finally:
            self._process = None
            self._is_ready = False
            # Remove from global list
            if self in _registered_managers:
                _registered_managers.remove(self)
    
    def _sync_kill(self) -> None:
        """
        Synchronously force kill subprocess (for atexit and other scenarios where async is not available)
        """
        if not self._process:
            return
        
        try:
            # Send SIGKILL directly to entire process group
            os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
            self._process.wait(timeout=2)
        except ProcessLookupError:
            pass  # Process already exited
        except Exception:
            pass  # Ignore errors, this is cleanup phase
        finally:
            self._process = None

    async def _forward_logs(self) -> None:
        """Forward subprocess log output"""
        if not self._process or not self._process.stdout:
            return
        
        loop = asyncio.get_event_loop()
        
        def read_line():
            if self._process and self._process.stdout:
                return self._process.stdout.readline()
            return b""
        
        while self._process and self._process.poll() is None:
            try:
                line = await loop.run_in_executor(None, read_line)
                if line:
                    log_line = line.decode("utf-8", errors="ignore").strip()
                    uvicorn_logger.info(f"{self._log_prefix} {log_line}")
            except Exception:
                break

    async def _wait_for_ready(self) -> None:
        """Wait for subprocess to be ready"""
        if not self._health_check:
            # No health check, assume ready
            self._is_ready = True
            uvicorn_logger.info(f"{self._log_prefix} No health check configured, assuming ready")
            return
        
        uvicorn_logger.info(f"{self._log_prefix} Waiting for process to be ready...")
        
        start_time = time.time()
        
        while time.time() - start_time < self._startup_timeout:
            try:
                if await self._health_check():
                    self._is_ready = True
                    uvicorn_logger.info(f"{self._log_prefix} Process is ready!")
                    return
            except Exception:
                pass
            
            # Check if process is still alive
            if self._process and self._process.poll() is not None:
                exit_code = self._process.returncode
                uvicorn_logger.error(
                    f"{self._log_prefix} Process died during startup with exit code {exit_code}"
                )
                if self._exit_on_failure:
                    sys.exit(1)
                raise RuntimeError(f"Process died with exit code {exit_code}")
            
            await asyncio.sleep(self._health_check_interval)
        
        # Startup timeout
        uvicorn_logger.error(
            f"{self._log_prefix} Process failed to start within {self._startup_timeout}s"
        )
        if self._exit_on_failure:
            sys.exit(1)
        raise TimeoutError(f"Process failed to start within {self._startup_timeout}s")

    async def _monitor_process(self) -> None:
        """Background monitor subprocess status, handle abnormal exits"""
        while True:
            await asyncio.sleep(self._monitor_interval)
            
            # If shutting down normally, stop monitoring
            if self._shutting_down:
                break
            
            if self._process is None:
                break
            
            exit_code = self._process.poll()
            if exit_code is not None:
                # Process exited and not a normal shutdown
                uvicorn_logger.error(
                    f"{self._log_prefix} Process exited unexpectedly with code {exit_code}"
                )
                if self._exit_on_failure:
                    uvicorn_logger.error(f"{self._log_prefix} Shutting down main process...")
                    sys.exit(1)
                break


async def http_health_check(
    url: str,
    timeout: float = 5.0,
    expected_status: int = 200
) -> bool:
    """
    Generic HTTP health check function
    
    Args:
        url: Health check URL
        timeout: Timeout (seconds)
        expected_status: Expected status code
    
    Returns:
        True if health check passes
    """
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                return resp.status == expected_status
    except Exception:
        return False


def create_http_health_check(
    url: str,
    timeout: float = 5.0,
    expected_status: int = 200
) -> Callable[[], Coroutine[Any, Any, bool]]:
    """
    Factory method to create HTTP health check function
    
    Usage Example:
        health_check = create_http_health_check("http://localhost:8188/system_stats")
        manager = SubprocessManager(
            start_cmd="...",
            work_dir="...",
            health_check=health_check,
        )
    """
    async def check() -> bool:
        return await http_health_check(url, timeout, expected_status)
    return check

