import os

from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()


class Settings:

    MODEL_SERVER = os.environ.get("MODEL_SERVER", "OLLAMA")
    MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-oss:20b")

    NEO4J_USER = os.environ.get("NEO4J_USER") or "neo4j"
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD") or "test1234"
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    
    LOG_METRICS = os.environ.get("LOG_METRICS", 1)
    ENABLE_JUDGE = os.environ.get("ENABLE_JUDGE", 1)
    
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    EMB_MODEL=os.environ.get("EMB_MODEL")
    EMB_DIMENSION=os.environ.get("EMB_DIMENSION")
    EMB_PROPERTY=os.environ.get("EMB_PROPERTY")
    EMB_SIMILARITY=os.environ.get("EMB_SIMILARITY")
