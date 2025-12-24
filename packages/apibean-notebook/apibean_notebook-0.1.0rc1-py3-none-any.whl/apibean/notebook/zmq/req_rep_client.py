import zmq
import json
import time

from .conf_logger import logger

class ZmqReqRepClient:
    def __init__(self, host="127.0.0.1", port=5555, retries=5, retry_interval=1.0,
            return_none_on_error: bool = False):
        self.host = host
        self.port = port
        self.retries = retries
        self.retry_interval = retry_interval
        self.return_none_on_error = return_none_on_error

    def __call__(self, msg: str) -> str|None:
        endpoint = f"tcp://{self.host}:{self.port}"

        reply = None
        for attempt in range(self.retries):
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(endpoint)

            try:
                logger.debug(f"[{self.__class__.__name__}] Attempt {attempt+1}: Sending '{msg}'")
                socket.send_string(str(msg))
                poller = zmq.Poller()
                poller.register(socket, zmq.POLLIN)
                socks = dict(poller.poll(timeout=2000))

                if socks.get(socket) == zmq.POLLIN:
                    reply = socket.recv_string()
                    logger.debug(f"[{self.__class__.__name__}] Reply: {reply}")
                    break
                else:
                    logger.debug(f"[{self.__class__.__name__}] No response, retrying...")
            except zmq.ZMQError as e:
                logger.debug(f"[{self.__class__.__name__}] ZMQ Error: {e}, retrying...")
            finally:
                socket.close()
                context.term()

            time.sleep(self.retry_interval)

        if reply is None:
            logger.debug(f"[{self.__class__.__name__}] Failed to connect after retries.")
            if self.return_none_on_error:
                return None
            raise Exception(f"Failed to connect after {self.retries} attempt retries")

        return reply


class ZmqReqRepJsonClient(ZmqReqRepClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, data: dict) -> dict|None:
        msg = json.dumps(data)

        reply = super().__call__(msg)

        if reply is None:
            return reply

        if not isinstance(reply, str):
            return reply

        try:
            reply = json.loads(reply)
        except json.JSONDecodeError as jde:
            logger.debug(f"[{self.__class__.__name__}] JSON decode error")
            if self.return_none_on_error:
                return None
            raise jde

        return reply
