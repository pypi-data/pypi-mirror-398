from .base import BaseLogger

class CloudWatchLogger(BaseLogger):

    def __init__(self, log_group="nd-sdk", stream="default"):
        # Stub implementation
        self.log_group = log_group
        self.stream = stream

    def info(self, msg: str):
        print(f"[CLOUDWATCH][INFO] {msg}")

    def error(self, msg: str):
        print(f"[CLOUDWATCH][ERROR] {msg}")

    def debug(self, msg: str):
        print(f"[CLOUDWATCH][DEBUG] {msg}")

    def warning(self, msg: str):
        print(f"[CLOUDWATCH][WARNING] {msg}")

    def critical(self, msg: str):
        print(f"[CLOUDWATCH][CRITICAL] {msg}")
