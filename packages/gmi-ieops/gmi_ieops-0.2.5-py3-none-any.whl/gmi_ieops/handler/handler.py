# pyright: strict, reportUnusedFunction=false, reportUnknownVariableType=false

from typing import Optional
import asyncio
import signal
from ..utils.log import *
from .server import BaseServer as Server
from ..version import COMMIT_SHA
from .client import Register  # pyright: ignore[reportPrivateUsage]


print("GMICLOUD-IEOPS Python SDK version: %s" % COMMIT_SHA)


class Handler:
    def __init__(self,server: Optional[Server] = None) -> None:
        self._server = server
        self._stop : bool = False
        self._register_task: Optional[asyncio.Task[None]] = None

    def serve(self):
        assert self._server is not None
        loop = asyncio.get_event_loop()
        
        self._register = Register()
        async def run():
            assert self._server is not None
            # create register task
            self._register_task = asyncio.create_task(self._register.register())
            
            # set signal handler
            def handle_signal():
                uvicorn_logger.info("Received shutdown signal...")
                assert self._server is not None
                # notify uvicorn to stop
                self._server.shutdown()
                # cancel register task
                if self._register_task:
                    self._register_task.cancel()
            
            loop.add_signal_handler(signal.SIGINT, handle_signal)
            loop.add_signal_handler(signal.SIGTERM, handle_signal)
            
            try:
                # run server (will exit when signal is received)
                await self._server.serve()
            finally:
                # wait for register task to finish
                if self._register_task and not self._register_task.done():
                    self._register_task.cancel()
                    try:
                        await self._register_task
                    except asyncio.CancelledError:
                        pass
                # remove signal handler
                loop.remove_signal_handler(signal.SIGINT)
                loop.remove_signal_handler(signal.SIGTERM)
        
        try:
            loop.run_until_complete(run())
        except KeyboardInterrupt:
            pass
        finally:
            uvicorn_logger.info("Handler stopped")
        