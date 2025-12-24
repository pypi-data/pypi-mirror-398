import threading
import zmq

from typing import Callable, Optional

from .conf_logger import logger

class ZmqPubSubClient:
    def __init__(self, topic="topic1", message_handler: Optional[Callable]=None,
            host="127.0.0.1", port=5555, timeout=5000):
        self.topic = topic
        self.host = host
        self.port = port
        self.timeout = timeout
        self._message_handler = message_handler
        self._stop_event = threading.Event()
        self._thread = None

    def __call__(self):
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] Already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        ctx = zmq.Context()
        sock = ctx.socket(zmq.SUB)
        sock.setsockopt_string(zmq.SUBSCRIBE, self.topic)
        sock.connect(f"tcp://{self.host}:{self.port}")
        logger.debug(f"[{self.__class__.__name__}] Subscribed to {self.topic}")
        poller = zmq.Poller()
        poller.register(sock, zmq.POLLIN)

        try:
            while not self._stop_event.is_set():
                socks = dict(poller.poll(self.timeout))
                if socks.get(sock) == zmq.POLLIN:
                    parts = sock.recv_multipart()
                    topic = parts[0].decode()
                    data = parts[1].decode()
                    logger.debug(f"[{self.__class__.__name__}] Received: {data} from '{topic}'")
                    if callable(self._message_handler):
                        self._message_handler(data, topic=self.topic)  # (data=data)
                else:
                    logger.debug(f"[{self.__class__.__name__}] No message received, retrying...")
        except Exception as exc:
            logger.debug(f"[{self.__class__.__name__}] Error: {exc}")
        finally:
            sock.close()
            ctx.term()
            logger.debug(f"[{self.__class__.__name__}] Cleaned up.")

    def terminate(self):
        logger.debug(f"[{self.__class__.__name__}] Terminating...")
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            logger.debug(f"[{self.__class__.__name__}] Thread joined.")
