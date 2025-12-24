import zmq
import threading

from ..conf_logger import logger

class ZmqLBBroker:
    def __init__(self, frontend_port=6666, backend_port=6767):
        self.context = zmq.Context()

        self.frontend = self.context.socket(zmq.ROUTER)
        self.backend = self.context.socket(zmq.ROUTER)

        self.backend.setsockopt(zmq.ROUTER_MANDATORY, 1)

        self.frontend.bind(f"tcp://*:{frontend_port}")
        logger.debug(f"[{self.__class__.__name__}] Bound frontend to *:{frontend_port}")

        self.backend.bind(f"tcp://*:{backend_port}")
        logger.debug(f"[{self.__class__.__name__}] Bound backend to *:{backend_port}")

        self._poller = zmq.Poller()
        self._poller.register(self.frontend, zmq.POLLIN)
        self._poller.register(self.backend, zmq.POLLIN)

        self._stop_event = threading.Event()
        self._thread = None

    def _run(self):
        logger.debug(f"[{self.__class__.__name__}] is running ...")
        while not self._stop_event.is_set():
            try:
                socks = dict(self._poller.poll(timeout=100))
                if self.frontend in socks:
                    logger.debug(f"[{self.__class__.__name__}] Receive a request from frontend")
                    msg = self.frontend.recv_multipart()
                    logger.debug(f"[{self.__class__.__name__}] Received from frontend: {msg}")
                    logger.debug(f"[{self.__class__.__name__}] Dispatch the request to backend")
                    self.backend.send_multipart([b'Worker-1'] + msg)

                if self.backend in socks:
                    logger.debug(f"[{self.__class__.__name__}] Receive a reply from the backend")
                    msg = self.backend.recv_multipart()
                    logger.debug(f"[{self.__class__.__name__}] Received from backend: {msg}")
                    worker_id, *payload = msg
                    logger.debug(f"[{self.__class__.__name__}] Dispatch the reply to frontend")
                    self.frontend.send_multipart(payload)
            except zmq.ZMQError as exc:
                logger.warning(f"[{self.__class__.__name__}] Broker error: {str(exc)}")
                break

    def __call__(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def start(self):
        self.__call__()

    def terminate(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.frontend.close()
        self.backend.close()
        self.context.term()
