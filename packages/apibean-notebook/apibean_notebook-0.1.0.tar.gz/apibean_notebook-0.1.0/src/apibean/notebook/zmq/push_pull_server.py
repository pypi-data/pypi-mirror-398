import zmq
import json

from typing import Callable, Optional

from .base_server import ZmqServer
from .conf_logger import logger

class ZmqPushPullServer(ZmqServer):
    def __init__(self, *args, message_builder: Optional[Callable[...,dict]]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_builder = message_builder
        self._count = 0

    def setup_socket(self):
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.bind(f"tcp://{self.host}:{self.port}")
        logger.debug(f"[{self.__class__.__name__}] Bound to {self.host}:{self.port}")

    def server_loop(self):
        result = self.generate_message(self._count)
        data = result.get("data", json.dumps({}))
        self.socket.send_string(data)
        logger.debug(f"[{self.__class__.__name__}] Sent: {data}")
        self._count += 1

    def socket_poll(self, timeout:int|None):
        return self.socket.poll(timeout=(100 if timeout is None else timeout), flags=zmq.POLLOUT)

    def generate_message(self, count):
        if callable(self._message_builder):
            return self._message_builder(count=count)
        if self.use_json:
            return dict(data=json.dumps({"task_id": count, "task": f"Task #{count}"}))
        else:
            return dict(data=f"task_id: {count}")
