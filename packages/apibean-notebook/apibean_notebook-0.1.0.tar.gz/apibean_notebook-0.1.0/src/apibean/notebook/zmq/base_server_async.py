import asyncio
import zmq.asyncio
import threading
from abc import ABC, abstractmethod

from .conf_logger import logger

class ZmqServerAsync(ABC):
    def __init__(self, host="127.0.0.1", port=5555,
            socket_poll_timeout:int|None=None,
            break_time:float=0.05,
            use_json=True):
        self.host = host
        self.port = port
        self.socket_poll_timeout = socket_poll_timeout
        self.break_time = break_time
        self.use_json = use_json
        self.context = None
        self.socket = None
        self._thread = None
        self._loop = None
        self._stop_event_async = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] Already running.")
            return
        self._thread = threading.Thread(target=self._start_event_loop, daemon=True)
        self._thread.start()
        logger.debug(f"[{self.__class__.__name__}] Thread started.")

    def _start_event_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._stop_event_async = asyncio.Event()
        self._loop = asyncio.get_event_loop()
        try:
            self._loop.run_until_complete(self._run())
        finally:
            self._loop.close()
        logger.debug(f"[{self.__class__.__name__}] Event loop closed.")

    async def _run(self):
        self.context = zmq.asyncio.Context()
        self.setup_socket()
        try:
            while not self._stop_event_async.is_set():
                await self._process()
        except Exception as exc:
            logger.warning(f"[{self.__class__.__name__}] Server error: {str(exc)}")
        finally:
            self.socket.close()
            self.context.term()
            logger.debug(f"[{self.__class__.__name__}] Socket closed.")

    async def _process(self):
        if await self.socket_poll(timeout=self.socket_poll_timeout):
            await self.server_loop()
        else:
            if self.break_time > 0:
                await asyncio.sleep(self.break_time)

    def stop(self):
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] Stopping server...")
            if self._loop and self._stop_event_async:
                self._loop.call_soon_threadsafe(self._stop_event_async.set)
            self._thread.join(timeout=5)
            logger.debug(f"[{self.__class__.__name__}] Server stopped.")
        else:
            logger.debug(f"[{self.__class__.__name__}] Server has already stopped.")

    def restart(self):
        logger.debug(f"[{self.__class__.__name__}] Restarting server...")
        self.stop()
        self.start()

    @abstractmethod
    def setup_socket(self):
        pass

    @abstractmethod
    async def server_loop(self):
        pass

    @abstractmethod
    async def socket_poll(self, timeout):
        pass
