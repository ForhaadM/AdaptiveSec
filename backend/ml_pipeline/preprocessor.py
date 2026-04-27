'''Before any ML happens, every raw click event from the Chrome Extension passes through here first. 
It strips PII, replaces email addresses and phone numbers with placeholders, and SHA-256 hashes the user_id so 
the real identity never touches the ML pipeline. It also validates that all required fields are present and 
normalizes the timestamp to a consistent format'''


import hashlib
import re
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_PII_PATTERNS: list[tuple[str, str]] = [
    (r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
    (r"\+?[\d\s\-().]{7,15}\d", "[PHONE]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    (r"\b(?:\d[ \-]?){13,16}\b", "[CC]"),
]

_COMPILED_PII = [(re.compile(pattern), replacement) for pattern, replacement in _PII_PATTERNS]
_REQUIRED_FIELDS = {"user_id", "url", "page_context", "timestamp"}


class PreprocessingError(Exception):
    pass

class DataPreprocessor:
    def sanitize(self, payload: dict[str, Any]) -> dict[str, Any]:

        self._validate_fields(payload)

        sanitized = {
            "user_id_hash":  self._hash_user_id(payload["user_id"]),
            "url":           self._sanitize_text(str(payload["url"])),
            "page_context":  self._sanitize_text(str(payload["page_context"])),
            "timestamp":     self._normalize_timestamp(payload["timestamp"]),
            "simulation_id": payload.get("simulation_id"),
            "trigger_type":  payload.get("trigger_type"),
        }

        logger.info(
            "Payload sanitized | user_id_hash=%s | simulation_id=%s | trigger_type=%s",
            sanitized["user_id_hash"][:8] + "...",
            sanitized["simulation_id"],
            sanitized["trigger_type"],
        )
        return sanitized

    def _validate_fields(self, payload: dict[str, Any]) -> None:
        missing = _REQUIRED_FIELDS - set(payload.keys())
        if missing:
            raise PreprocessingError(
                f"Payload is missing required fields: {sorted(missing)}"
            )
        # Type guards for critical fields
        if not isinstance(payload["user_id"], str) or not payload["user_id"].strip():
            raise PreprocessingError("user_id must be a non-empty string.")
        if not isinstance(payload["url"], str) or not payload["url"].strip():
            raise PreprocessingError("url must be a non-empty string.")

    def _hash_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.strip().encode("utf-8")).hexdigest()

    def _sanitize_text(self, text: str) -> str:
        for pattern, replacement in _COMPILED_PII:
            text = pattern.sub(replacement, text)
        return text.strip()

    def _normalize_timestamp(self, timestamp: str) -> str:
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue

        raise PreprocessingError(
            f"Cannot parse timestamp '{timestamp}'. "
            f"Expected ISO-8601 format (e.g., 2026-03-10T14:00:00Z)."
        )