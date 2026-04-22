"""HTTP provider base with retry/timeout."""
from __future__ import annotations

import logging
import time
from typing import Any

import requests


class HttpProvider:
    def __init__(self, timeout: int = 15, retries: int = 3, backoff: float = 1.2):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.logger = logging.getLogger(self.__class__.__name__)

    def get(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                r = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                r.raise_for_status()
                return r.json()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.logger.warning("GET failed attempt %s/%s url=%s err=%s", attempt, self.retries, url, exc)
                time.sleep(self.backoff * attempt)
        raise RuntimeError(f"HTTP GET failed after retries: {last_error}")

    def post(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                r.raise_for_status()
                return r.json()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.logger.warning("POST failed attempt %s/%s url=%s err=%s", attempt, self.retries, url, exc)
                time.sleep(self.backoff * attempt)
        raise RuntimeError(f"HTTP POST failed after retries: {last_error}")
