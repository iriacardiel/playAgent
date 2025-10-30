import logging
import os
import tempfile
import traceback
from termcolor import cprint

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from config import Settings
from services.stt import STTModel

logger = logging.getLogger(__name__)
router = APIRouter()
# cprint(f"Using STT Model: {Settings.STT_MODEL} on device: {Settings.STT_DEVICE}", "red")

# Lazy load the STT model to avoid import-time errors
stt_model = None


def get_stt_model():
    """Get or initialize the STT model lazily."""
    global stt_model
    if stt_model is None:
        stt_model = STTModel(
            model_id=Settings.STT_MODEL,
            device=Settings.STT_DEVICE,
            language=Settings.STT_LANGUAGE,
        )
    return stt_model


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio using Whisper."""
    try:
        # print(f"Received file: {audio.filename}, size: {audio.size} bytes")

        # Validate file type
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Check if file is empty
        if audio.size == 0:
            raise HTTPException(
                status_code=400,
                detail="Audio file is empty. Please record for at least 1 second.",
            )

        # Check if file is too small (less than 1KB might indicate an issue)
        if audio.size < 1024:
            raise HTTPException(
                status_code=400,
                detail="Audio file is too small. Please record for at least 1 second.",
            )

        # Create a temporary file to save the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Additional check: verify file exists and has content
            if (
                not os.path.exists(temp_file_path)
                or os.path.getsize(temp_file_path) == 0
            ):
                raise HTTPException(
                    status_code=400, detail="Failed to save audio file or file is empty"
                )

            # Transcribe the audio using Whisper from transformers
            transcription = get_stt_model().transcribe_audio(temp_file_path)
            logger.info(f"Transcription: {transcription}")

            if not transcription:
                raise HTTPException(
                    status_code=400, detail="No speech detected in audio"
                )

            return JSONResponse(
                content={"transcription": transcription, "status": "success"}
            )

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
