import subprocess

import numpy as np
import torch
import whisper
from fastapi import FastAPI, File, HTTPException, UploadFile

from ai_term.common.model_manager import ModelManager

app = FastAPI()


def load_whisper_model():
    # Detect device
    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Loading Whisper model on {device}...")
    # Using 'base' as in test_stt.py, 'turbo' was in main block but function defaulted
    # to base
    return whisper.load_model("base", device=device)


model_manager = ModelManager(load_model_fn=load_whisper_model)


def load_audio_from_bytes(file_bytes: bytes, sr: int = 16000):
    """
    Reads an audio file from bytes and returns a NumPy array containing the audio
    waveform, similar to whisper.load_audio but from bytes.
    """
    try:
        # This launches a subprocess to decode audio while down-mixing and resampling
        # as necessary. Requires the ffmpeg CLI and `ffmpeg-python` package is not
        # strictly needed if we use subprocess directly like whisper does, but
        # whisper.load_audio takes a file path.
        # We will mimic whisper.load_audio implementation but pipe input.

        cmd = [
            "ffmpeg",
            "-nostdin",
            "-threads",
            "0",
            "-i",
            "pipe:0",
            "-f",
            "s16le",
            "-ac",
            "1",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(sr),
            "-",
        ]

        process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        out, err = process.communicate(input=file_bytes)

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {err.decode()}")

        return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to process audio: {str(e)}"
        )


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Read file content
    content = await file.read()

    # helper to convert bytes to audio array
    audio = load_audio_from_bytes(content)

    # Get model (loads if necessary)
    model = model_manager.get_model()

    # Transcribe
    # We use internal transcribe because we already have audio array
    # whisper.transcribe can take np.ndarray
    result = model.transcribe(audio)

    return {"text": result["text"]}


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model_manager.model is not None}
