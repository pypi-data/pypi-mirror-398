import threading
import time
import zmq
from abc import ABC, abstractmethod

from .conf_logger import logger

class ZmqServer(ABC):
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
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] Server already running.")
            return
        logger.debug(f"[{self.__class__.__name__}] Starting server thread...")
        self._stop_event.clear()
        self.context = zmq.Context()
        self.setup_socket()
        self._thread = threading.Thread(target=self._target, daemon=True)
        self._thread.start()
        logger.debug(f"[{self.__class__.__name__}] Server started.")

    def stop(self):
        logger.debug(f"[{self.__class__.__name__}] Stopping server thread...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.debug(f"[{self.__class__.__name__}] Server stopped.")

    def restart(self):
        logger.debug(f"[{self.__class__.__name__}] Restarting server...")
        self.stop()
        self.start()

    def _target(self):
        while not self._stop_event.is_set():
            try:
                self._process()
            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM:
                    logger.debug(f"[{self.__class__.__name__}] Context terminated.")
                elif e.errno == zmq.ENOTSOCK:
                    logger.debug(f"[{self.__class__.__name__}] Invalid socket.")
                else:
                    raise

    def _process(self):
        if self.socket_poll(timeout=self.socket_poll_timeout):
            self.server_loop()
        elif self.break_time > 0:
            time.sleep(self.break_time)

    @abstractmethod
    def setup_socket(self):
        pass

    @abstractmethod
    def server_loop(self):
        pass

    @abstractmethod
    def socket_poll(self, timeout):
        pass
