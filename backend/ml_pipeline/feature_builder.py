"""
FeatureVectorBuilder
====================
Pipeline Step 2 of 6 (DDD Section 4.2.C)

Responsibilities:
    - Convert a sanitized telemetry payload into a standardized 8-feature
      numerical array for consumption by the XGBoost RiskScoringEngine.
    - Each feature maps to a fixed index position [F1..F8] as defined
      in the DDD Feature Encoding Strategy (Section 4.2.B).

DDD Contract:
    Method : FeatureVectorBuilder.extract(sanitized_data) -> list[float]
    Input  : Sanitized dict from DataPreprocessor.sanitize()
    Output : Array of 8 floats [F1, F2, F3, F4, F5, F6, F7, F8]

Feature Index Map (DDD Section 4.2.B):
    F1 [0] url_length               — Integer cast to float
    F2 [1] num_subdomains           — Integer cast to float
    F3 [2] has_suspicious_keywords  — Binary: 0.0 or 1.0
    F4 [3] contains_ip_address      — Binary: 0.0 or 1.0
    F5 [4] is_https                 — Binary: 0.0 or 1.0
    F6 [5] time_of_day_encoded      — Ordinal: 0.0=Morning, 1.0=Afternoon, 2.0=Night
    F7 [6] session_fatigue_index    — Continuous float 0.0–1.0 (runtime default: 0.0)
    F8 [7] trigger_type_encoded     — Categorical int: 0=None,1=Urgency,2=Authority,
                                      3=Scarcity,4=Social_Proof

Notes on F7:
    session_fatigue_index cannot be derived from a single click event at runtime.
    It will be enriched by the synthetic injection script during model training.
    At inference time it defaults to 0.0 unless the caller provides a value
    via the optional `session_context` argument to extract().
"""

import re
import logging
from urllib.parse import urlparse
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Suspicious keyword lexicon — used for F3
# Drawn from DDD simulation templates + common phishing vocabulary
# ---------------------------------------------------------------------------
_SUSPICIOUS_KEYWORDS: frozenset[str] = frozenset([
    "urgent", "verify", "update", "confirm", "reset", "suspend",
    "suspended", "expire", "expired", "expires", "immediately",
    "action required", "account", "credentials", "password",
    "click here", "login", "sign in", "validate", "unusual",
    "security alert", "locked", "limited", "access denied",
    "unauthorized", "invoice", "payment", "overdue",
])

# ---------------------------------------------------------------------------
# IP address pattern — used for F4
# ---------------------------------------------------------------------------
_IP_IN_URL_PATTERN = re.compile(
    r"https?://(\d{1,3}\.){3}\d{1,3}"
)

# ---------------------------------------------------------------------------
# Trigger type encoding map — used for F8 (DDD Section 4.2.B)
# ---------------------------------------------------------------------------
_TRIGGER_ENCODING: dict[str | None, float] = {
    None:           0.0,
    "none":         0.0,
    "urgency":      1.0,
    "authority":    2.0,
    "scarcity":     3.0,
    "social_proof": 4.0,
    # Accept the Urgency_Bias format returned by CognitiveModel
    "urgency_bias":      1.0,
    "authority_bias":    2.0,
    "scarcity_bias":     3.0,
    "social_proof_bias": 4.0,
}

# Time-of-day encoding boundaries (24h) — used for F6
_MORNING_RANGE   = range(5, 12)    # 05:00 – 11:59
_AFTERNOON_RANGE = range(12, 18)   # 12:00 – 17:59
# Night: everything else (18:00–04:59)


class FeatureExtractionError(Exception):
    """Raised when a feature cannot be extracted from sanitized data."""
    pass


class FeatureVectorBuilder:
    """
    Converts a sanitized telemetry payload into the 8-feature vector
    expected by the XGBoost RiskScoringEngine.

    Usage:
        builder = FeatureVectorBuilder()
        vector = builder.extract(sanitized_data)
        # Returns: [25.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    """

    def extract(
        self,
        sanitized_data: dict[str, Any],
        session_context: dict[str, Any] | None = None,
    ) -> list[float]:
        """
        Build the 8-feature array from a sanitized telemetry payload.

        Args:
            sanitized_data : Output dict from DataPreprocessor.sanitize()
            session_context: Optional dict with runtime enrichment values.
                             Currently supports:
                             { "session_fatigue_index": float (0.0–1.0) }

        Returns:
            List of 8 floats in the fixed DDD feature index order [F1..F8].

        Raises:
            FeatureExtractionError: If URL is missing or unparseable.
        """
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

    # ------------------------------------------------------------------
    # Feature extractors — one method per feature for testability
    # ------------------------------------------------------------------

    def _f1_url_length(self, url: str) -> float:
        """F1: Total character length of the URL string."""
        return float(len(url))

    def _f2_num_subdomains(self, parsed: Any) -> float:
        """
        F2: Number of subdomains.
        Counts dot-separated labels in the hostname, minus the registered
        domain (rightmost two labels, e.g. 'google.com').
        Example: 'mail.accounts.google.com' → 2 subdomains
        """
        hostname = parsed.hostname or ""
        parts = hostname.split(".")
        # Subtract the root domain (2 parts: 'google' + 'com')
        subdomain_count = max(0, len(parts) - 2)
        return float(subdomain_count)

    def _f3_has_suspicious_keywords(self, url: str, page_context: str) -> float:
        """
        F3: Binary flag — 1.0 if any known phishing keyword appears in the
        URL path or page context text, 0.0 otherwise.
        """
        combined = (url + " " + page_context).lower()
        for keyword in _SUSPICIOUS_KEYWORDS:
            if keyword in combined:
                return 1.0
        return 0.0

    def _f4_contains_ip_address(self, url: str) -> float:
        """
        F4: Binary flag — 1.0 if the URL uses a raw IP address as its
        hostname instead of a domain name.
        """
        return 1.0 if _IP_IN_URL_PATTERN.match(url) else 0.0

    def _f5_is_https(self, parsed: Any) -> float:
        """
        F5: Binary flag — 1.0 if the URL scheme is HTTPS, 0.0 otherwise.
        Note: absence of HTTPS is a phishing signal (higher risk).
        """
        return 1.0 if (parsed.scheme or "").lower() == "https" else 0.0

    def _f6_time_of_day(self, timestamp: str) -> float:
        """
        F6: Ordinal encoding of the hour the event occurred.
            0.0 = Morning   (05:00 – 11:59)
            1.0 = Afternoon (12:00 – 17:59)
            2.0 = Night     (18:00 – 04:59)

        Defaults to 0.0 (Morning) if timestamp cannot be parsed.
        """
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
        """
        F7: Session fatigue index — continuous float 0.0 to 1.0.

        At inference time this defaults to 0.0 unless provided by the caller.
        During training, the synthetic injection script will populate this
        column with behaviorally modeled values (DDD Section 4.2.A).

        A higher value indicates the user has been active longer and is
        more likely to make impulsive click decisions.
        """
        if session_context is None:
            return 0.0
        raw = session_context.get("session_fatigue_index", 0.0)
        # Clamp to valid range
        return float(max(0.0, min(1.0, raw)))

    def _f8_trigger_type(self, trigger_type: str | None) -> float:
        """
        F8: Categorical encoding of the cognitive trigger type.
            0 = None / unknown
            1 = Urgency
            2 = Authority
            3 = Scarcity
            4 = Social Proof

        Accepts both raw telemetry values ('urgency') and CognitiveModel
        output values ('Urgency_Bias'). Lookup is case-insensitive.
        """
        if trigger_type is None:
            return 0.0
        key = trigger_type.lower().replace(" ", "_")
        return _TRIGGER_ENCODING.get(key, 0.0)

    # ------------------------------------------------------------------
    # Internal utility
    # ------------------------------------------------------------------

    def _parse_url(self, url: str) -> Any:
        """
        Safely parse a URL string. Returns a ParseResult.
        Raises FeatureExtractionError if the URL is completely unparseable.
        """
        try:
            parsed = urlparse(url)
            return parsed
        except Exception as exc:
            raise FeatureExtractionError(f"Failed to parse URL '{url}': {exc}") from exc