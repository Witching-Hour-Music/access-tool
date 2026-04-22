"""Central logging setup."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str) -> None:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if root.handlers:
        return

    file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)
