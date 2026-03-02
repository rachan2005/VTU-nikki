"""Input router to handle different file formats"""
from pathlib import Path
from typing import Union, Dict, List, Any

from .text_processor import TextProcessor
from .audio_processor import AudioProcessor
from .excel_processor import ExcelProcessor
from .pdf_processor import PDFProcessor
from .video_processor import VideoProcessor


class InputRouter:
    """Routes input files to appropriate processors"""

    HANDLERS = {
        ".txt": TextProcessor,
        ".md": TextProcessor,
        ".mp3": AudioProcessor,
        ".wav": AudioProcessor,
        ".m4a": AudioProcessor,
        ".flac": AudioProcessor,
        ".xlsx": ExcelProcessor,
        ".xls": ExcelProcessor,
        ".csv": ExcelProcessor,
        ".pdf": PDFProcessor,
        ".mp4": VideoProcessor,
        ".mov": VideoProcessor,
        ".avi": VideoProcessor,
    }

    def __init__(self):
        self._processors = {}

    def process(self, file_path: Union[str, Path]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process input file and return normalized data.

        Returns:
            - Dict for single-entry inputs (text, audio, video, PDF)
            - List[Dict] for multi-entry inputs (Excel with multiple rows)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        ext = file_path.suffix.lower()
        handler_class = self.HANDLERS.get(ext)

        if not handler_class:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported: {', '.join(self.HANDLERS.keys())}"
            )

        # Get or create processor instance
        if ext not in self._processors:
            self._processors[ext] = handler_class()

        processor = self._processors[ext]
        return processor.process(str(file_path))

    def process_text(self, text: str) -> Dict[str, Any]:
        """Process raw text directly"""
        processor = TextProcessor()
        return processor.process_string(text)
