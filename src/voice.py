"""
voice.py — Handles voice recording and transcription using OpenAI Whisper.

The UI handles microphone recording natively using Streamlit's audio input.
The recording bytes are then saved as a temporary file and transcribed here
by Whisper locally on-device. No internet needed.
"""

import tempfile
import whisper

from config import WHISPER_MODEL


# ── Module-level singleton for the Whisper model ──────────────
_whisper_model = None


def _get_whisper():
    """Load the Whisper model once and keep it in memory."""
    global _whisper_model
    if _whisper_model is None:
        print(f"[voice] Loading Whisper model: {WHISPER_MODEL} ...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        print("[voice] Whisper model loaded.")
    return _whisper_model


def transcribe_audio_file(audio_path):
    """
    Run Whisper on a saved audio file and return the transcription text.
    This works with WAV, MP3, FLAC — anything ffmpeg can decode.
    """
    model = _get_whisper()
    print(f"[voice] Transcribing {audio_path} ...")
    result = model.transcribe(str(audio_path), language="en")
    text = result["text"].strip()
    print(f"[voice] Transcription: '{text}'")
    return text


def transcribe_uploaded_audio(audio_bytes, suffix=".wav"):
    """
    For the Streamlit UI: takes raw audio bytes (from the audio input component),
    writes them to a temp file, and transcribes.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(audio_bytes)
    tmp.flush()

    text = transcribe_audio_file(tmp.name)
    return text
