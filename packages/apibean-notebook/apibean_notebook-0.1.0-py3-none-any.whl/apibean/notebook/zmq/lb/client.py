import zmq
import time
import threading

from ..conf_logger import logger

class ZmqLBClient:
    def __init__(self, endpoint="tcp://localhost:6666",
                 identity=None,
                 message_generator=None,
                 message_processor=None,
                 total_messages=5):
        self.context = zmq.Context()
        self.client = self.context.socket(zmq.DEALER)
        self.identity = identity or f"Client-{time.time()}"
        self.client.identity = self.identity.encode()
        self.client.connect(endpoint)

        self._message_generator = message_generator or (lambda i: f"Job-{i}")
        self._message_processor = message_processor or (lambda reply: print(f"[{self.identity}] Got reply: {reply}"))
        self.total_messages = total_messages

        self._stop_event = threading.Event()
        self._thread = None

    def _run(self):
        logger.debug(f"[{self.__class__.__name__}] is running ...")
        for i in range(self.total_messages):
            if self._stop_event.is_set():
                break
            msg = self._message_generator(i)
            self.client.send_multipart([b'', msg.encode()])
            time.sleep(0.1)

        for _ in range(self.total_messages):
            if self._stop_event.is_set():
                break
            try:
                msg = self.client.recv_multipart(flags=zmq.NOBLOCK)
                logger.debug(f"[{self.__class__.__name__}] Received from broker: {msg}")
                empty, reply = msg
                self._message_processor(reply.decode())
            except zmq.Again:
                time.sleep(0.1)
            except Exception as exc:
                logger.warning(f"[{self.__class__.__name__}] error: {exc}")

    def __call__(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def start(self):
        self.__call__()

    def terminate(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.client.close()
        self.context.term()
