import os

class Settings:
    ENV = os.getenv("SDK_ENV", "dev")
    DEBUG = os.getenv("SDK_DEBUG", "false").lower() == "true"
