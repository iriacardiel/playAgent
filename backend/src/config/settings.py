import os

from dotenv import load_dotenv  # pip install python-dotenv

# Load local env first
load_dotenv()

class Settings:
    MODEL_SERVER = os.environ.get("MODEL_SERVER")
    MODEL_NAME = os.environ.get("MODEL_NAME")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    
    EMB_MODEL=os.environ.get("EMB_MODEL")
    EMB_DIMENSION=os.environ.get("EMB_DIMENSION")
    EMB_PROPERTY=os.environ.get("EMB_PROPERTY")
    EMB_SIMILARITY=os.environ.get("EMB_SIMILARITY")

    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    STT_MODEL = os.environ.get("STT_MODEL")
    STT_DEVICE = os.environ.get("STT_DEVICE")
    STT_LANGUAGE = os.environ.get("STT_LANGUAGE")
    STT_ENABLED = os.environ.get("STT_ENABLED", "true").lower() == "true"

    SOFTWARE_VERSION = os.environ.get("SOFTWARE_VERSION")
    
    NEO4J_USER = os.environ.get("NEO4J_USER") or "neo4j"
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD") or "test1234"
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")