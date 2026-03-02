"""
Centralized logging configuration.
"""
import logging
import sys
from pathlib import Path


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """Setup logger with consistent formatting."""
    
    if level is None:
        import os
        level = os.getenv("LOG_LEVEL", "INFO")
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler (use utf-8 stream to avoid cp1252 encoding errors on Windows)
    if not logger.handlers:
        console_stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)
        console_handler = logging.StreamHandler(console_stream)
        console_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "vtu_automation.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Alias for compatibility
get_logger = setup_logger
