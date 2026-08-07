from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.constants import APP_NAME, APP_VERSION
from app.infrastructure.paths import logs_dir


def configure_logging() -> None:
    log_path = logs_dir() / "app.log"
    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
    logging.getLogger(__name__).info("%s %s iniciado", APP_NAME, APP_VERSION)
