"""Date inference from natural language text"""
import re
from typing import List, Optional
from datetime import date

try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

from src.utils.logger import get_logger

logger = get_logger(__name__)


def infer_dates_from_text(text: str, default_year: Optional[int] = None) -> List[date]:
    """
    Extract and infer dates from natural language text.

    Finds explicit date mentions in various formats:
    - ISO: 2025-01-15
    - US: 01/15/2025, 1/15/25
    - Written: January 15, 2025, Jan 15
    - European: 15/01/2025, 15-01-2025

    Args:
        text: Text to search for dates
        default_year: Year to assume if not specified (default: current year)

    Returns:
        List of unique dates found (sorted)
    """
    if not DATEUTIL_AVAILABLE:
        logger.warning("dateutil not available, date inference disabled")
        return []

    if default_year is None:
        default_year = date.today().year

    found_dates = []

    # Pattern 1: ISO format (2025-01-15)
    iso_pattern = r'\b\d{4}-\d{2}-\d{2}\b'
    for match in re.finditer(iso_pattern, text):
        try:
            d = date_parser.parse(match.group(0)).date()
            found_dates.append(d)
        except:
            pass

    # Pattern 2: Slash formats (01/15/2025, 1/15/25, 15/01/2025)
    slash_pattern = r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
    for match in re.finditer(slash_pattern, text):
        try:
            d = date_parser.parse(match.group(0), default=date(default_year, 1, 1)).date()
            found_dates.append(d)
        except:
            pass

    # Pattern 3: Dash formats (15-01-2025)
    dash_pattern = r'\b\d{1,2}-\d{1,2}-\d{4}\b'
    for match in re.finditer(dash_pattern, text):
        try:
            d = date_parser.parse(match.group(0)).date()
            found_dates.append(d)
        except:
            pass

    # Pattern 4: Written dates (January 15, 2025, Jan 15)
    month_names = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    written_pattern = rf'\b{month_names}\s+\d{{1,2}}(?:,?\s+\d{{4}})?\b'

    for match in re.finditer(written_pattern, text, re.IGNORECASE):
        try:
            d = date_parser.parse(match.group(0), default=date(default_year, 1, 1)).date()
            found_dates.append(d)
        except:
            pass

    # Remove duplicates and sort
    unique_dates = sorted(set(found_dates))

    if unique_dates:
        logger.info(f"Inferred {len(unique_dates)} dates from text")

    return unique_dates


def extract_date_keywords(text: str) -> List[str]:
    """
    Extract date-related keywords for further processing.

    Returns phrases like "last week", "yesterday", "this month", etc.
    """
    keywords = []

    relative_patterns = [
        r'\b(?:last|this|next)\s+(?:week|month|year)\b',
        r'\byesterday\b',
        r'\btoday\b',
        r'\btomorrow\b',
    ]

    for pattern in relative_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(matches)

    return keywords
