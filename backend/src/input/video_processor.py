"""Video processor - extracts audio and transcribes"""
import tempfile
from typing import Dict, Any
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from .audio_processor import AudioProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VideoProcessor:
    """Processes video files by extracting and transcribing audio"""

    def __init__(self):
        if not MOVIEPY_AVAILABLE:
            raise ImportError(
                "Video processing requires moviepy. "
                "Install with: pip install moviepy"
            )

        self.audio_processor = AudioProcessor()

    def process(self, file_path: str) -> Dict[str, Any]:
        """Extract audio from video and transcribe"""
        file_path = Path(file_path)
        logger.info(f"Processing video: {file_path.name}")

        # Create temp audio file
        temp_audio = Path(tempfile.gettempdir()) / f"{file_path.stem}_audio.wav"

        try:
            # Extract audio track
            logger.info("Extracting audio from video...")
            video = VideoFileClip(str(file_path))

            # Get duration
            video_duration = video.duration

            # Extract audio
            if video.audio is None:
                raise ValueError("Video has no audio track")

            video.audio.write_audiofile(str(temp_audio), verbose=False, logger=None)
            video.close()

            logger.info(f"Audio extracted ({video_duration:.1f}s)")

            # Transcribe audio
            result = self.audio_processor.process(str(temp_audio))

            # Update metadata to reflect video source
            result["metadata"]["source"] = "video"
            result["metadata"]["video_duration"] = video_duration
            result["metadata"]["video_file"] = file_path.name

            return result

        finally:
            # Cleanup temp audio file
            if temp_audio.exists():
                temp_audio.unlink()
