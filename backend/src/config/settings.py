import os

from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()  # Load local environment variables

class Settings:
    VERBOSE = os.environ.get("VERBOSE")
    VERBOSE_LLM = os.environ.get("VERBOSE_LLM")
    LOGGING = os.environ.get("LOGGING")
    MODEL_SERVER = os.environ.get("MODEL_SERVER")
    MODEL_NAME = os.environ.get("MODEL_NAME")

    STT_MODEL = os.environ.get("STT_MODEL")
    STT_DEVICE = os.environ.get("STT_DEVICE")
    STT_LANGUAGE = os.environ.get("STT_LANGUAGE")

    SOFTWARE_VERSION = os.environ.get("SOFTWARE_VERSION")
    