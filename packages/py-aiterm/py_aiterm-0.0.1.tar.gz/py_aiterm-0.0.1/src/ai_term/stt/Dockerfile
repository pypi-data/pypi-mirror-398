FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# We install torch CPU version explicitly first to keep image size smaller if possible, 
# though standard pip install torch might pull CPU-only on linux now or cu117. 
# We'll stick to standard pip for simplicity as per plan.
RUN pip install --no-cache-dir \
    openai-whisper \
    fastapi \
    uvicorn \
    python-multipart \
    torch \
    numpy

# Copy source code
COPY src /app/src

# Set python path to allow imports from src
ENV PYTHONPATH=/app/src

# Run the service
CMD ["uvicorn", "ai_term.stt.main:app", "--host", "0.0.0.0", "--port", "8001"]
