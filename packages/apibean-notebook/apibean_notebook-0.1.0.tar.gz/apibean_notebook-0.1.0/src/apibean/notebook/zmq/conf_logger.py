import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[ logging.StreamHandler() ]
)

logger = logging.getLogger("apibean.notebook.zmq")
logger.setLevel(logging.DEBUG)
