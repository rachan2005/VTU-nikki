"""Audio transcription processor using Whisper"""
import os
import tempfile
from typing import Dict, Any
from pathlib import Path

try:
    import whisper
    import torch
    from pydub import AudioSegment
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from config import WHISPER_MODEL, WHISPER_LANGUAGE
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """Processes audio files via Whisper transcription"""

    def __init__(self):
        if not WHISPER_AVAILABLE:
            raise ImportError(
                "Whisper not available. Install with: "
                "pip install openai-whisper torch pydub"
            )

        self.model = None
        self.model_name = WHISPER_MODEL

    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")

    def process(self, file_path: str) -> Dict[str, Any]:
        """Transcribe audio file"""
        self._load_model()

        file_path = Path(file_path)
        logger.info(f"Transcribing audio: {file_path.name}")

        # Convert to WAV if needed (Whisper prefers WAV)
        audio_path = self._prepare_audio(file_path)

        try:
            # Transcribe with Whisper
            result = self.model.transcribe(
                str(audio_path),
                language=WHISPER_LANGUAGE,
                task="transcribe",
                word_timestamps=True,
                verbose=False
            )

            raw_text = result["text"].strip()
            segments = result.get("segments", [])

            # Calculate duration
            duration_seconds = segments[-1]["end"] if segments else 0

            logger.info(f"Transcription complete: {len(raw_text)} chars, {duration_seconds:.1f}s")

            return {
                "raw_text": raw_text,
                "metadata": {
                    "source": "audio",
                    "duration_seconds": duration_seconds,
                    "segments_count": len(segments),
                    "language": result.get("language", WHISPER_LANGUAGE),
                    "file_name": file_path.name
                }
            }

        finally:
            # Cleanup temp file if created
            if audio_path != file_path and audio_path.exists():
                audio_path.unlink()

    def _prepare_audio(self, file_path: Path) -> Path:
        """Convert audio to WAV if needed"""
        if file_path.suffix.lower() == ".wav":
            return file_path

        logger.info(f"Converting {file_path.suffix} to WAV")

        # Load audio and convert
        audio = AudioSegment.from_file(str(file_path))

        # Create temp WAV file
        temp_wav = Path(tempfile.gettempdir()) / f"{file_path.stem}_temp.wav"
        audio.export(str(temp_wav), format="wav")

        return temp_wav
