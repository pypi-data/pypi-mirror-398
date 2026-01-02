FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# espeak-ng is required for Coqui TTS
# build-essential, rustc, cargo are required for compiling python dependencies like sudachipy on ARM64
RUN apt-get update && apt-get install -y \
    espeak-ng \
    build-essential \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to ensure we can find wheels if they exist
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
# 'tts' is the package name for Coqui TTS
RUN pip install --no-cache-dir \
    tts \
    fastapi \
    uvicorn \
    httpx \
    pydantic

# Copy source code
COPY src /app/src

# Set python path to allow imports from src
ENV PYTHONPATH=/app/src

# Run the service
CMD ["uvicorn", "ai_term.tts.main:app", "--host", "0.0.0.0", "--port", "8002"]
