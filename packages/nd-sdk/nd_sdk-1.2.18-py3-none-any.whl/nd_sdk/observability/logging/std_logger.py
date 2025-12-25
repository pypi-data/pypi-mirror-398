import logging
from .base import BaseLogger

class StdLogger(BaseLogger):

    def __init__(self, name="nd_sdk"):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(name)

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)
