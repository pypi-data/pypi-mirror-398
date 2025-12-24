import asyncio
import json
import zmq

from typing import Awaitable, Callable, Optional

from .base_server_async import ZmqServerAsync
from .conf_logger import logger

class ZmqPubSubServerAsync(ZmqServerAsync):
    def __init__(self, *args, message_builder: Optional[Callable[...,Awaitable[dict|str]]]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_builder = message_builder
        self._count = 0

    def setup_socket(self):
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://{self.host}:{self.port}")
        logger.debug(f"[{self.__class__.__name__}] Bound to tcp://{self.host}:{self.port}")

    async def server_loop(self):
        result = await self.generate_message(self._count)
        topic = result.get("topic", "topic1")
        data = result.get("data", json.dumps({}))
        await self.socket.send_multipart([topic.encode(), data.encode()])
        logger.debug(f"[{self.__class__.__name__}] Sent: {data} as '{topic}'")
        self._count += 1

    async def socket_poll(self, timeout:int|None):
        return await self.socket.poll(timeout=(100 if timeout is None else timeout), flags=zmq.POLLOUT)

    async def generate_message(self, count):
        if callable(self._message_builder):
            return await self._message_builder(count=count)
        if self.use_json:
            return dict(topic="topic1", data=json.dumps({"task_id": count, "task": f"Task #{count}"}))
        else:
            return dict(topic="topic1", data=f"task_id: {count}")
