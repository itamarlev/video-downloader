"""Shared logging setup, usable by any front end (desktop, web, CLI)."""

import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"


def setup_logging():
    """Configure root logging to a dated file plus stdout, and return the app logger."""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"download_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("youtube_downloader")
