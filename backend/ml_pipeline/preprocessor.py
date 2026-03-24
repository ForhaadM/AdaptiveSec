"""
DataPreprocessor
================
Pipeline Step 1 of 6 (DDD Section 4.2.C)

Responsibilities:
    - Strip PII from the raw telemetry payload
    - Hash user_id using SHA-256 (one-way, non-reversible)
    - Validate required fields are present before downstream processing
    - Normalize timestamp to ISO-8601 UTC

DDD Contract:
    Method : DataPreprocessor.sanitize(payload) -> dict
    Input  : Raw JSON payload from POST /api/v1/telemetry/click
    Output : Sanitized dictionary with user_id hashed and PII removed

Input payload schema (DDD Section 4.4 Step 1):
    {
        "user_id"      : str   — raw UUID, will be hashed
        "url"          : str   — full URL string
        "page_context" : str   — raw page text / email subject
        "timestamp"    : str   — ISO-8601 datetime string
    }

Output schema:
    {
        "user_id_hash"  : str   — SHA-256 hex digest of original user_id
        "url"           : str   — preserved as-is for FeatureVectorBuilder
        "page_context"  : str   — stripped of email addresses and phone numbers
        "timestamp"     : str   — normalized ISO-8601 UTC string
        "simulation_id" : str | None  — preserved if present, else None
        "trigger_type"  : str | None  — preserved if present, else None
    }
"""

import hashlib
import re
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PII pattern registry
# ---------------------------------------------------------------------------
_PII_PATTERNS: list[tuple[str, str]] = [
    # Email addresses  →  [EMAIL]
    (r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
    # Phone numbers (US + international variants)  →  [PHONE]
    (r"\+?[\d\s\-().]{7,15}\d", "[PHONE]"),
    # Social Security Numbers  →  [SSN]
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    # Credit card patterns (basic Luhn-structure)  →  [CC]
    (r"\b(?:\d[ \-]?){13,16}\b", "[CC]"),
]

_COMPILED_PII = [(re.compile(pattern), replacement) for pattern, replacement in _PII_PATTERNS]

# ---------------------------------------------------------------------------
# Required fields — pipeline will raise if any are missing
# ---------------------------------------------------------------------------
_REQUIRED_FIELDS = {"user_id", "url", "page_context", "timestamp"}


class PreprocessingError(Exception):
    """Raised when the payload is malformed or missing required fields."""
    pass


class DataPreprocessor:
    """
    Sanitizes raw telemetry payloads before ML feature extraction.

    Usage:
        preprocessor = DataPreprocessor()
        sanitized = preprocessor.sanitize(raw_payload)
    """

    def sanitize(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize a raw telemetry click payload.

        Args:
            payload: Raw dict from POST /api/v1/telemetry/click

        Returns:
            Sanitized dict with user_id hashed and PII stripped from text fields.

        Raises:
            PreprocessingError: If required fields are missing or types are wrong.
        """
        self._validate_fields(payload)

        sanitized = {
            "user_id_hash":  self._hash_user_id(payload["user_id"]),
            "url":           self._sanitize_text(str(payload["url"])),
            "page_context":  self._sanitize_text(str(payload["page_context"])),
            "timestamp":     self._normalize_timestamp(payload["timestamp"]),
            # Optional fields — preserve if provided by telemetry layer
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_fields(self, payload: dict[str, Any]) -> None:
        """Raise PreprocessingError if any required field is absent."""
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
        """
        One-way SHA-256 hash of the raw user_id.
        Output is a 64-character hex digest.
        This satisfies the DDD requirement to never store raw PII identifiers
        in the ML pipeline (Section 4.2.C — DataPreprocessor step).
        """
        return hashlib.sha256(user_id.strip().encode("utf-8")).hexdigest()

    def _sanitize_text(self, text: str) -> str:
        """
        Apply all PII regex patterns to a text field.
        Replaces matches with their placeholder tokens (e.g., [EMAIL]).
        """
        for pattern, replacement in _COMPILED_PII:
            text = pattern.sub(replacement, text)
        return text.strip()

    def _normalize_timestamp(self, timestamp: str) -> str:
        """
        Parse and re-serialize a timestamp string to a consistent
        ISO-8601 UTC format: YYYY-MM-DDTHH:MM:SSZ

        Raises:
            PreprocessingError: If the timestamp cannot be parsed.
        """
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp, fmt)
                # Ensure UTC-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue

        raise PreprocessingError(
            f"Cannot parse timestamp '{timestamp}'. "
            f"Expected ISO-8601 format (e.g., 2026-03-10T14:00:00Z)."
        )