import logging


def configure_logging():
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
    logger = logging.getLogger("httpx")
    logger.setLevel(logging.WARNING)
