"""PDF document processor"""
from typing import Dict, Any
from pathlib import Path

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFProcessor:
    """Processes PDF documents and extracts text"""

    def __init__(self):
        if not (PDFPLUMBER_AVAILABLE or PYPDF2_AVAILABLE):
            raise ImportError(
                "PDF processing requires pdfplumber or PyPDF2. "
                "Install with: pip install pdfplumber PyPDF2"
            )

    def process(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF"""
        file_path = Path(file_path)
        logger.info(f"Processing PDF: {file_path.name}")

        # Try pdfplumber first (better for tables)
        if PDFPLUMBER_AVAILABLE:
            return self._process_with_pdfplumber(file_path)
        else:
            return self._process_with_pypdf2(file_path)

    def _process_with_pdfplumber(self, file_path: Path) -> Dict[str, Any]:
        """Use pdfplumber to extract text and tables"""
        text_blocks = []
        table_count = 0

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text
                text = page.extract_text()
                if text:
                    text_blocks.append(f"--- Page {page_num} ---\n{text}")

                # Extract tables
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables, 1):
                    table_count += 1
                    # Convert table to text
                    if table:
                        table_text = self._table_to_text(table)
                        text_blocks.append(f"\n[Table {table_idx} on Page {page_num}]\n{table_text}")

        raw_text = "\n\n".join(text_blocks)

        logger.info(f"Extracted {len(raw_text)} chars, {table_count} tables from PDF")

        return {
            "raw_text": raw_text,
            "metadata": {
                "source": "pdf",
                "pages": len(pdf.pages),
                "tables_count": table_count,
                "file_name": file_path.name
            }
        }

    def _process_with_pypdf2(self, file_path: Path) -> Dict[str, Any]:
        """Fallback to PyPDF2"""
        text_blocks = []

        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_blocks.append(f"--- Page {page_num + 1} ---\n{text}")

        raw_text = "\n\n".join(text_blocks)

        logger.info(f"Extracted {len(raw_text)} chars from PDF using PyPDF2")

        return {
            "raw_text": raw_text,
            "metadata": {
                "source": "pdf",
                "pages": num_pages,
                "file_name": file_path.name
            }
        }

    @staticmethod
    def _table_to_text(table: list) -> str:
        """Convert table array to readable text"""
        if not table:
            return ""

        # Use first row as headers if available
        lines = []
        for row in table:
            row_text = " | ".join(str(cell or "").strip() for cell in row)
            lines.append(row_text)

        return "\n".join(lines)
