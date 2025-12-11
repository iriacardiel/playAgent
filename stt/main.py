import logging
import os
import tempfile
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel

# Configure logging
HERE = Path(__file__).parent
log_file = HERE / "transcription.log"

class MetricsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Record.msg contains lines like:
        # "127.0.0.1:52726 - "GET /api/metrics HTTP/1.1" 200 OK"
        return "/metrics" not in record.getMessage()
    
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logging.getLogger("uvicorn.access").addFilter(MetricsFilter())

logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Transcription Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


base_model = WhisperModel(
    "large-v3-turbo",
    device="cuda",
    compute_type="int8_float16",
    download_root=HERE.as_posix(),
    local_files_only=False,
)

model = base_model


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file and returns the transcription text.
    """
    try:
        # Start timing
        start_time = time.time()

        # Save uploaded audio temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Run inference
        segments, _ = model.transcribe(
            tmp_path,
            temperature=0,
            beam_size=5,
            language="en",
            word_timestamps=False,
            without_timestamps=True,
        )

        # Combine all text segments
        text = " ".join([segment.text.strip() for segment in segments])

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Log transcription details
        logger.info(f"Transcription took {elapsed_time:.2f} seconds, text: {text}")

        return JSONResponse(content={"transcription": text})

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    host = os.getenv("STT_HOST", "0.0.0.0")
    port = int(os.getenv("STT_PORT", "8024"))
    uvicorn.run("main:app", host=host, port=port)
