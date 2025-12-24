import zmq
import time
import random
import threading

from ..conf_logger import logger

class ZmqLBWorker:
    def __init__(self, endpoint="tcp://localhost:6767",
                 identity=None,
                 message_handler=None):
        self.context = zmq.Context()
        self.worker = self.context.socket(zmq.DEALER)
        self.identity = identity or f"Worker-1"
        self.worker.identity = self.identity.encode()
        self.worker.connect(endpoint)

        self._message_handler = message_handler or (lambda msg, client: print(f"[{self.identity}] Received {msg} from {client}"))

        self._stop_event = threading.Event()
        self._thread = None

    def _run(self):
        logger.debug(f"[{self.__class__.__name__}] is running ...")
        while not self._stop_event.is_set():
            try:
                msg = self.worker.recv_multipart(flags=zmq.NOBLOCK)
                logger.debug(f"[{self.__class__.__name__}] Received from broker: {msg}")
                identity, empty, message = msg
                msg_decoded = message.decode()
                client_id = identity.decode()

                logger.debug(f"[{self.__class__.__name__}] Receive a request '{msg_decoded}' from '{client_id}'")
                time.sleep(random.uniform(0.3, 1.0))  # giả lập xử lý

                logger.debug(f"[{self.__class__.__name__}] Processing")
                self._message_handler(msg_decoded, client_id)

                result = f"{msg_decoded} OK"
                reply = result.encode()
                logger.debug(f"[{self.__class__.__name__}] Reply result '{result}' to '{client_id}'")
                self.worker.send_multipart([identity, b'', reply])
            except zmq.Again:
                time.sleep(0.1)
            except Exception as exc:
                logger.warning(f"[{self.__class__.__name__}] error: {exc}")

    def __call__(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def start(self):
        self.__call__()

    def terminate(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.worker.close()
        self.context.term()
