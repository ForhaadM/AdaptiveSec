import re
import logging
from urllib.parse import urlparse
from typing import Any

logger = logging.getLogger(__name__)

_SUSPICIOUS_KEYWORDS: frozenset[str] = frozenset([
    "urgent", "verify", "update", "confirm", "reset", "suspend",
    "suspended", "expire", "expired", "expires", "immediately",
    "action required", "account", "credentials", "password",
    "click here", "login", "sign in", "validate", "unusual",
    "security alert", "locked", "limited", "access denied",
    "unauthorized", "invoice", "payment", "overdue",
])


_IP_IN_URL_PATTERN = re.compile(
    r"https?://(\d{1,3}\.){3}\d{1,3}"
)

_TRIGGER_ENCODING: dict[str | None, float] = {
    None:           0.0,
    "none":         0.0,
    "urgency":      1.0,
    "authority":    2.0,
    "scarcity":     3.0,
    "social_proof": 4.0,
    "urgency_bias":      1.0,
    "authority_bias":    2.0,
    "scarcity_bias":     3.0,
    "social_proof_bias": 4.0,
}

_MORNING_RANGE   = range(5, 12)    # 05:00 – 11:59
_AFTERNOON_RANGE = range(12, 18)   # 12:00 – 17:59



class FeatureExtractionError(Exception):
    pass


class FeatureVectorBuilder:

    def extract(
        self,
        sanitized_data: dict[str, Any],
        session_context: dict[str, Any] | None = None,
    ) -> list[float]:

        url          = sanitized_data.get("url", "")
        page_context = sanitized_data.get("page_context", "")
        timestamp    = sanitized_data.get("timestamp", "")
        trigger_type = sanitized_data.get("trigger_type")

        if not url:
            raise FeatureExtractionError("sanitized_data is missing 'url' field.")

        parsed_url = self._parse_url(url)

        vector = [
            self._f1_url_length(url),                              # F1
            self._f2_num_subdomains(parsed_url),                   # F2
            self._f3_has_suspicious_keywords(url, page_context),   # F3
            self._f4_contains_ip_address(url),                     # F4
            self._f5_is_https(parsed_url),                         # F5
            self._f6_time_of_day(timestamp),                       # F6
            self._f7_session_fatigue(session_context),             # F7
            self._f8_trigger_type(trigger_type),                   # F8
        ]

        logger.debug(
            "Feature vector extracted | url_len=%.0f subdomains=%.0f "
            "suspicious=%.0f ip=%.0f https=%.0f tod=%.0f fatigue=%.2f trigger=%.0f",
            *vector,
        )

        return vector

    def _f1_url_length(self, url: str) -> float:
        """F1: Total character length of the URL string."""
        return float(len(url))

    def _f2_num_subdomains(self, parsed: Any) -> float:

        hostname = parsed.hostname or ""
        parts = hostname.split(".")
        # Subtract the root domain (2 parts: 'google' + 'com')
        subdomain_count = max(0, len(parts) - 2)
        return float(subdomain_count)

    def _f3_has_suspicious_keywords(self, url: str, page_context: str) -> float:

        combined = (url + " " + page_context).lower()
        for keyword in _SUSPICIOUS_KEYWORDS:
            if keyword in combined:
                return 1.0
        return 0.0

    def _f4_contains_ip_address(self, url: str) -> float:

        return 1.0 if _IP_IN_URL_PATTERN.match(url) else 0.0

    def _f5_is_https(self, parsed: Any) -> float:

        return 1.0 if (parsed.scheme or "").lower() == "https" else 0.0

    def _f6_time_of_day(self, timestamp: str) -> float:

        try:
            # Timestamp is already normalized to HH:MM:SS by DataPreprocessor
            time_part = timestamp.split("T")[1].replace("Z", "")
            hour = int(time_part.split(":")[0])
            if hour in _MORNING_RANGE:
                return 0.0
            elif hour in _AFTERNOON_RANGE:
                return 1.0
            else:
                return 2.0
        except (IndexError, ValueError):
            logger.warning("Could not parse hour from timestamp '%s', defaulting to 0.0", timestamp)
            return 0.0

    def _f7_session_fatigue(self, session_context: dict[str, Any] | None) -> float:
        
        if session_context is None:
            return 0.0
        raw = session_context.get("session_fatigue_index", 0.0)
        # Clamp to valid range
        return float(max(0.0, min(1.0, raw)))

    def _f8_trigger_type(self, trigger_type: str | None) -> float:

        if trigger_type is None:
            return 0.0
        key = trigger_type.lower().replace(" ", "_")
        return _TRIGGER_ENCODING.get(key, 0.0)

    def _parse_url(self, url: str) -> Any:

        try:
            parsed = urlparse(url)
            return parsed
        except Exception as exc:
            raise FeatureExtractionError(f"Failed to parse URL '{url}': {exc}") from exc