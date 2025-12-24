import zmq
import json

from typing import Any, Callable, Optional

from .base_server import ZmqServer
from .conf_logger import logger

class ZmqReqRepServer(ZmqServer):
    def __init__(self, *args, message_handler: Optional[Callable]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_handler = message_handler

    def setup_socket(self):
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.host}:{self.port}")
        logger.debug(f"[{self.__class__.__name__}] Bound to {self.host}:{self.port}")

    def server_loop(self):
        msg = self.socket.recv_string()
        logger.debug(f"[{self.__class__.__name__}] Received: {msg}")
        result = self.process_message(data=msg)
        data = result.get("data", json.dumps({}))
        self.socket.send_string(str(data))

    def socket_poll(self, timeout:int|None):
        return self.socket.poll(timeout=(1000 if timeout is None else timeout))

    def process_message(self, data: Any) -> dict:
        logger.debug(f"[{self.__class__.__name__}] Processing: {data}")
        if self._message_handler:
            return self._message_handler(data=data) # -> { "data": ... }
        if self.use_json:
            return dict(data=json.dumps({"echo": data}))
        else:
            return dict(data=f"Echo: {data}")
