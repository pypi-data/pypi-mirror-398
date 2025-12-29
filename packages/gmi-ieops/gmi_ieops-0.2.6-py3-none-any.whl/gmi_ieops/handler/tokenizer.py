# pyright: strict, reportUnusedFunction=false

from concurrent.futures import ProcessPoolExecutor
from typing import List, Dict, Union, Optional, Any, TYPE_CHECKING
import asyncio
import threading
import multiprocessing
from abc import ABC, abstractmethod
import signal
from ..utils.log import log, uvicorn_logger

if TYPE_CHECKING:
    from transformers import BatchEncoding  # type: ignore
    import numpy as np
    import torch  # type: ignore

class TokenizerBase(ABC):
    """Tokenizer abstract base class"""
    @abstractmethod
    def init_tokenizer(self) -> None:
        """initialize tokenizer"""
        pass

    @abstractmethod
    def encode(self, msg: Union[str, List[Dict[str, str]], List[List[Dict[str, str]]]]) -> Union[str, List[int], List[str], List[List[int]], Any]:
        """encode interface"""
        pass
    @abstractmethod
    def decode(self, token_ids: Union[int, List[int], Any]) -> str:
        """decode interface"""
        pass

class TokenizerPool():
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _shutting_down = False
    _process_pool: Optional[ProcessPoolExecutor] = None

    def __new__(cls, *args, **kwargs): # type: ignore
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(
        self,
        tokenizer: Union[TokenizerBase, None],
        max_workers: int = multiprocessing.cpu_count()
    ):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    if tokenizer is None:
                        raise ValueError("Tokenizer must be provided")
                    self._tokenizer = tokenizer
                    self._max_workers = max_workers
                    
                    # initialize tokenizer in main process first
                    self._tokenizer.init_tokenizer()
                    
                    # create process pool
                    self._start_pool()
                    
                    self._loop = asyncio.get_event_loop()
                    self._initialized = True

    def _start_pool(self):
        """start process pool"""
        try:
            self._process_pool = ProcessPoolExecutor(
                max_workers=self._max_workers,
                initializer=self._init_worker,
                initargs=(self._tokenizer,)
            )
            self._process_pool.submit(self._init_worker, self._tokenizer)
            uvicorn_logger.info(f"Started tokenizer pool with {self._max_workers} workers")
        except Exception as e:
            log.get_logger().error(f"Failed to start process pool: {e}")
            raise

    @staticmethod
    def _init_worker(tokenizer: TokenizerBase):
        """initialize worker process"""
        # set signal handler for child process
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        
        # initialize tokenizer
        global _worker_tokenizer
        _worker_tokenizer = tokenizer
        _worker_tokenizer.init_tokenizer()

    @staticmethod
    def _encode_worker(msg: Union[List[Dict[str, str]], List[List[Dict[str, str]]]], tokenize: bool = True) -> "Union[str, List[int], List[str], List[List[int]], BatchEncoding]": # type: ignore
        """worker process encode function"""
        global _worker_tokenizer
        if not hasattr(_worker_tokenizer, 'tokenizer') or _worker_tokenizer.tokenizer is None: # type: ignore
            raise RuntimeError("Worker tokenizer not initialized")
        return _worker_tokenizer.encode(msg, tokenize) # type: ignore

    @staticmethod
    def _decode_worker(token_ids: Union[int, List[int], "np.ndarray", "torch.Tensor"]) -> str: # type: ignore
        """worker process decode function"""
        global _worker_tokenizer
        if not hasattr(_worker_tokenizer, 'tokenizer') or _worker_tokenizer.tokenizer is None: # type: ignore
            raise RuntimeError("Worker tokenizer not initialized")
        return _worker_tokenizer.decode(token_ids) # type: ignore

    async def encode(self, msg: Union[List[Dict[str, str]], List[List[Dict[str, str]]]], tokenize: bool = True) -> "Union[str, List[int], List[str], List[List[int]], BatchEncoding]": # type: ignore
        """async encode interface"""
        if self._shutting_down:
            raise RuntimeError("TokenizerPool is shutting down")
        if not self._initialized or not self._process_pool:
            raise RuntimeError("TokenizerPool not initialized")
        try:
            return await self._loop.run_in_executor(self._process_pool, self._encode_worker, msg, tokenize) # type: ignore
        except Exception as e:
            log.get_logger().error(f"Encode error: {e}")
            raise

    async def decode(self, token_ids: Union[int, List[int], "np.ndarray", "torch.Tensor"]) -> str: # type: ignore
        """async decode interface"""
        if self._shutting_down:
            raise RuntimeError("TokenizerPool is shutting down")
        if not self._initialized or not self._process_pool:
            raise RuntimeError("TokenizerPool not initialized")
        try:
            return await self._loop.run_in_executor(self._process_pool, self._decode_worker, token_ids) # type: ignore
        except Exception as e:
            log.get_logger().error(f"Decode error: {e}")
            raise

    def shutdown(self, wait: bool = True) -> None:
        """shutdown process pool"""
        if not hasattr(self, '_initialized') or not self._initialized or self._shutting_down:
            return
        with self._lock:
            if not self._initialized or self._shutting_down:
                return
            self._shutting_down = True
            try:
                if self._process_pool:
                    uvicorn_logger.info("Shutting down TokenizerPool...")
                    # save process reference
                    # processes = {}
                    # if hasattr(self._process_pool, '_processes'):
                    #     processes = self._process_pool._processes.copy() # type: ignore
                    # cancel all pending tasks
                    if hasattr(self._process_pool, '_work_queue'):
                        try:
                            self._process_pool._work_queue.queue.clear()  # type: ignore
                        except Exception as e:
                            log.get_logger().warning(f"Error clearing work queue: {e}")
                    # shutdown process pool
                    self._process_pool.shutdown(wait=False)
                    # wait for processes to finish
                    if wait and self._process_pool._processes:
                        for pid, p in self._process_pool._processes.items():
                            try:
                                p.kill()
                            except Exception as e:
                                log.get_logger().warning(f"Error terminating process {pid}: {e}")
                                
            except Exception as e:
                log.get_logger().error(f"Error during shutdown TokenizerPool: {e}")
            finally:
                if self._initialized:
                    uvicorn_logger.info("TokenizerPool shutdown completed")
                self._process_pool = None
                self._initialized = False
                self._shutting_down = False

    def __del__(self):
        """destructor"""
        if not self._shutting_down:
            self.shutdown(wait=False)