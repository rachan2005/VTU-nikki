"""Advanced date management with ranges, inference, and holiday support"""
from .date_manager import DateManager
from .inference import infer_dates_from_text

__all__ = ["DateManager", "infer_dates_from_text"]
