import asyncio
import zmq
import json

from typing import Awaitable, Callable, Optional

from .base_server_async import ZmqServerAsync
from .conf_logger import logger

class ZmqReqRepServerAsync(ZmqServerAsync):
    def __init__(self, *args, message_handler: Optional[Callable[...,Awaitable[dict|str]]]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_handler = message_handler

    def setup_socket(self):
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.host}:{self.port}")
        logger.debug(f"[{self.__class__.__name__}] Bound to tcp://{self.host}:{self.port}")

    async def server_loop(self):
        msg = await self.socket.recv_string()
        logger.debug(f"[{self.__class__.__name__}] Received: {msg}")
        result = await self.process_message(data=msg)
        data = result.get("data", json.dumps({}))
        await self.socket.send_string(str(data))

    async def socket_poll(self, timeout:int):
        return await self.socket.poll(timeout=(1000 if timeout is None else timeout))

    async def process_message(self, data) -> dict:
        logger.debug(f"[{self.__class__.__name__}] Processing: {data}")
        if self._message_handler:
            return await self._message_handler(data=data)
        if self.use_json:
            return dict(data=json.dumps({"echo": data}))
        else:
            return dict(data=f"Echo: {data}")
