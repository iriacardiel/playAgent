import os

from dotenv import load_dotenv  # pip install python-dotenv

# Load local env first
load_dotenv()

class Settings:
    VERBOSE = os.environ.get("VERBOSE")
    VERBOSE_LLM = os.environ.get("VERBOSE_LLM")
    LOGGING = os.environ.get("LOGGING")
    MODEL_SERVER = os.environ.get("MODEL_SERVER")
    MODEL_NAME = os.environ.get("MODEL_NAME")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    
    EMB_MODEL=os.environ.get("EMB_MODEL")
    EMB_DIMENSION=os.environ.get("EMB_DIMENSION")
    EMB_PROPERTY=os.environ.get("EMB_PROPERTY")
    EMB_SIMILARITY=os.environ.get("EMB_SIMILARITY")

    STT_MODEL = os.environ.get("STT_MODEL")
    STT_DEVICE = os.environ.get("STT_DEVICE")
    STT_LANGUAGE = os.environ.get("STT_LANGUAGE")

    SOFTWARE_VERSION = os.environ.get("SOFTWARE_VERSION")
    
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j") 
    NEO4J_USER=os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD=os.environ.get("NEO4J_PASSWORD", "test1234")
    NEO4J_URI_PORT=os.environ.get("NEO4J_URI_PORT", "7687")
    NEO4J_HTTP_PORT=os.environ.get("NEO4J_HTTP_PORT", "7474")
    NEODASH_HTTP_PORT=os.environ.get("NEODASH_HTTP_PORT", "5005")