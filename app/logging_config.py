import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        ctx = getattr(record, "ctx", None)
        if isinstance(ctx, dict):
            payload.update(ctx)

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    """
    Central logging setup.

    Env vars:
      - LOG_LEVEL: DEBUG|INFO|WARNING|ERROR (default INFO)
      - LOG_FORMAT: json|text (default json)
      - LOG_FILE: path (default ./logs/app.log)
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json").lower()
    log_file = os.getenv("LOG_FILE", "./logs/app.log")

    logger = logging.getLogger("youtube_extractor")
    logger.setLevel(log_level)

    # Avoid duplicate handlers under reload.
    if logger.handlers:
        return logger

    formatter: logging.Formatter
    if log_format == "text":
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(ctx)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    else:
        formatter = JsonFormatter()

    # Always log to stdout (container-friendly).
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(log_level)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Also log to rotating file.
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception:
        # If file logging fails (permissions, etc), keep stdout logging.
        logger.exception("file logging setup failed", extra={"ctx": {"log_file": log_file}})

    # Keep other noisy loggers calmer (optional, but product-friendly).
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    return logger


def get_client_id(headers: Dict[str, str]) -> Optional[str]:
    # Product-friendly "who": caller can set X-Client-Id (best) or X-Api-Key (we'll log partially).
    client_id = headers.get("x-client-id")
    if client_id:
        return client_id[:128]

    api_key = headers.get("x-api-key")
    if api_key:
        api_key = api_key.strip()
        if len(api_key) <= 8:
            return "api_key:" + api_key
        return "api_key:…" + api_key[-6:]

    return None


def get_client_ip(headers: Dict[str, str], fallback_ip: Optional[str]) -> Optional[str]:
    """
    If TRUST_PROXY_HEADERS=1, use X-Forwarded-For / X-Real-IP. Otherwise use fallback_ip.
    """
    trust_proxy = os.getenv("TRUST_PROXY_HEADERS", "").strip() in {"1", "true", "TRUE", "yes", "YES"}
    if trust_proxy:
        xff = headers.get("x-forwarded-for")
        if xff:
            # First IP is the original client in standard XFF format.
            return xff.split(",")[0].strip()
        xri = headers.get("x-real-ip")
        if xri:
            return xri.strip()
    return fallback_ip

