"""Text input processor"""
import re
from typing import Dict, Any
from datetime import datetime


class TextProcessor:
    """Processes plain text input"""

    def process(self, file_path: str) -> Dict[str, Any]:
        """Process text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self.process_string(text)

    def process_string(self, text: str) -> Dict[str, Any]:
        """Process text string"""
        # Try to extract metadata from text
        date_mentioned = self._extract_date(text)
        hours_mentioned = self._extract_hours(text)

        return {
            "raw_text": text.strip(),
            "metadata": {
                "source": "text",
                "date": date_mentioned,
                "hours": hours_mentioned,
                "word_count": len(text.split()),
                "char_count": len(text)
            }
        }

    def _extract_date(self, text: str) -> str:
        """Try to extract date from text using common patterns"""
        # Common date patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2025-01-15
            r'\d{2}/\d{2}/\d{4}',  # 01/15/2025
            r'\d{2}-\d{2}-\d{4}',  # 15-01-2025
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _extract_hours(self, text: str) -> float:
        """Try to extract hours from text"""
        # Look for patterns like "6.5 hours", "7h", "8 hrs"
        patterns = [
            r'(\d+\.?\d*)\s*(?:hours?|hrs?|h)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass

        return None
