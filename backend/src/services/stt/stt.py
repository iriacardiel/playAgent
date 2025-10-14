from pathlib import Path

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


class STTModel:
    def __init__(
        self,
        model_id: str = "openai/whisper-large-v3-turbo",
        device: str | torch.device | None = None,
        language: str = "en",
    ):
        """Initialize the STTModel with a specified model ID, device, and language."""
        # Set up device and torch dtype
        if device is None:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        device = torch.device(device)

        torch_dtype = torch.float16 if device.type == "cuda" else torch.float32

        try:
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                local_files_only=True,
            )
            processor = AutoProcessor.from_pretrained(model_id)

            # Create the pipeline
            self._pipeline = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                chunk_length_s=30,
                dtype=torch_dtype,
                device=device,
                generate_kwargs={
                    "max_new_tokens": 128,
                    "task": "transcribe",
                    "language": language,
                },
            )
        except Exception as e:
            print("Error loading model:", e)

    def transcribe_audio(self, file_path: str | Path):
        """Transcribe audio file using the Whisper model."""
        if isinstance(file_path, Path):
            file_path = str(file_path)
        result = self._pipeline(file_path)
        return result["text"].strip()
