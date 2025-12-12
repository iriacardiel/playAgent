import logging
import signal
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.map import router as map_router
        

signal.signal(signal.SIGINT, sys.exit)  # Ctrl+C
signal.signal(signal.SIGTERM, sys.exit)  # Termination signal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define the FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(map_router, prefix="/api")

