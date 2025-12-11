FROM python:3.12-slim

# Install ffmpeg for audio decoding
RUN apt-get update && rm -rf /var/lib/apt/lists/*

# Install CUDA runtime libs from PyPI
RUN pip install --no-cache-dir \
    nvidia-cublas-cu12 \
    "nvidia-cudnn-cu12==9.*"

# Install your app dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    faster-whisper \
    python-multipart \
    requests \
    prometheus-client

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Set default environment variables
ENV STT_HOST=0.0.0.0
ENV STT_PORT=8024

# Expose port
EXPOSE ${STT_PORT}

# Run the application with dynamic LD_LIBRARY_PATH
CMD ["sh", "-c", "export LD_LIBRARY_PATH=\"$(python3 -c 'import nvidia.cublas.lib, nvidia.cudnn.lib; print(nvidia.cublas.lib.__path__[0] + \":\" + nvidia.cudnn.lib.__path__[0])')\" && python3 main.py"]