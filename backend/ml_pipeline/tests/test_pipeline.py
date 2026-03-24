"""
Unit Tests — ML Pipeline (W1-010 / W1-011)
===========================================
Covers DDD Section 5.1.1 test cases:

    ✓ Data sanitization (PII removal)         → TestDataPreprocessor
    ✓ Feature vector extraction               → TestFeatureVectorBuilder
    ✓ Risk score calculation (placeholder)    → TestRiskScoringEngine

Run with:
    pytest backend/ml_pipeline/tests/test_pipeline.py -v
"""

import pytest
from backend.ml_pipeline.preprocessor    import DataPreprocessor, PreprocessingError
from backend.ml_pipeline.feature_builder import FeatureVectorBuilder, FeatureExtractionError
from backend.ml_pipeline.risk_engine     import RiskScoringEngine, ScoringError


# ===========================================================================
# Fixtures — shared across test classes
# ===========================================================================

@pytest.fixture
def raw_payload():
    """Valid raw telemetry payload matching DDD Section 4.4 Step 1."""
    return {
        "user_id":      "uuid-1234",
        "url":          "http://update-payroll-now.com/reset",
        "page_context": "URGENT: Verify your credentials now",
        "timestamp":    "2026-03-10T14:00:00Z",
        "trigger_type": "urgency",
        "simulation_id": "SIM-001",
    }

@pytest.fixture
def preprocessor():
    return DataPreprocessor()

@pytest.fixture
def builder():
    return FeatureVectorBuilder()

@pytest.fixture
def engine():
    return RiskScoringEngine()


# ===========================================================================
# DataPreprocessor Tests
# ===========================================================================

class TestDataPreprocessor:
    """DDD 5.1.1 — Data sanitization (PII removal)."""

    def test_user_id_is_hashed(self, preprocessor, raw_payload):
        """user_id must never appear in the output — only its SHA-256 hash."""
        result = preprocessor.sanitize(raw_payload)
        assert "user_id" not in result
        assert "user_id_hash" in result
        assert result["user_id_hash"] != raw_payload["user_id"]
        assert len(result["user_id_hash"]) == 64  # SHA-256 hex digest

    def test_hash_is_deterministic(self, preprocessor, raw_payload):
        """Same user_id must always produce the same hash."""
        r1 = preprocessor.sanitize(raw_payload)
        r2 = preprocessor.sanitize(raw_payload)
        assert r1["user_id_hash"] == r2["user_id_hash"]

    def test_hash_is_unique_per_user(self, preprocessor, raw_payload):
        """Different user_ids must produce different hashes."""
        payload_b = {**raw_payload, "user_id": "uuid-5678"}
        r1 = preprocessor.sanitize(raw_payload)
        r2 = preprocessor.sanitize(payload_b)
        assert r1["user_id_hash"] != r2["user_id_hash"]

    def test_email_pii_stripped_from_page_context(self, preprocessor, raw_payload):
        """Email addresses in page_context must be replaced with [EMAIL]."""
        raw_payload["page_context"] = "Contact admin@company.com for help"
        result = preprocessor.sanitize(raw_payload)
        assert "admin@company.com" not in result["page_context"]
        assert "[EMAIL]" in result["page_context"]

    def test_phone_pii_stripped(self, preprocessor, raw_payload):
        """Phone numbers in page_context must be replaced with [PHONE]."""
        raw_payload["page_context"] = "Call us at 555-123-4567 now"
        result = preprocessor.sanitize(raw_payload)
        assert "555-123-4567" not in result["page_context"]

    def test_url_is_preserved(self, preprocessor, raw_payload):
        """URL must pass through to output unchanged for FeatureVectorBuilder."""
        result = preprocessor.sanitize(raw_payload)
        assert result["url"] == raw_payload["url"]

    def test_timestamp_normalized_to_utc(self, preprocessor, raw_payload):
        """Timestamp output must be in ISO-8601 UTC format."""
        result = preprocessor.sanitize(raw_payload)
        assert result["timestamp"].endswith("Z")
        assert "T" in result["timestamp"]

    def test_optional_simulation_id_preserved(self, preprocessor, raw_payload):
        """simulation_id must be passed through if present."""
        result = preprocessor.sanitize(raw_payload)
        assert result["simulation_id"] == "SIM-001"

    def test_optional_simulation_id_defaults_to_none(self, preprocessor, raw_payload):
        """simulation_id must default to None if absent."""
        del raw_payload["simulation_id"]
        result = preprocessor.sanitize(raw_payload)
        assert result["simulation_id"] is None

    def test_missing_required_field_raises(self, preprocessor, raw_payload):
        """Missing any required field must raise PreprocessingError."""
        for field in ["user_id", "url", "page_context", "timestamp"]:
            bad_payload = {k: v for k, v in raw_payload.items() if k != field}
            with pytest.raises(PreprocessingError):
                preprocessor.sanitize(bad_payload)

    def test_empty_user_id_raises(self, preprocessor, raw_payload):
        """Empty user_id string must raise PreprocessingError."""
        raw_payload["user_id"] = "   "
        with pytest.raises(PreprocessingError):
            preprocessor.sanitize(raw_payload)

    def test_invalid_timestamp_raises(self, preprocessor, raw_payload):
        """Unparseable timestamp must raise PreprocessingError."""
        raw_payload["timestamp"] = "not-a-date"
        with pytest.raises(PreprocessingError):
            preprocessor.sanitize(raw_payload)


# ===========================================================================
# FeatureVectorBuilder Tests
# ===========================================================================

class TestFeatureVectorBuilder:
    """DDD 5.1.1 — Feature vector extraction."""

    @pytest.fixture
    def sanitized(self, preprocessor, raw_payload):
        return preprocessor.sanitize(raw_payload)

    def test_returns_eight_features(self, builder, sanitized):
        """Output must always be exactly 8 elements (F1–F8)."""
        vector = builder.extract(sanitized)
        assert len(vector) == 8

    def test_all_elements_are_floats(self, builder, sanitized):
        """Every element of the feature vector must be a float."""
        vector = builder.extract(sanitized)
        for i, val in enumerate(vector):
            assert isinstance(val, float), f"F{i+1} is not a float: {type(val)}"

    # F1 — url_length
    def test_f1_url_length(self, builder, sanitized):
        """F1 must equal the character length of the URL."""
        vector = builder.extract(sanitized)
        assert vector[0] == float(len(sanitized["url"]))

    # F2 — num_subdomains
    def test_f2_subdomains_for_simple_domain(self, builder, sanitized):
        """A URL with no subdomains (e.g. google.com) should produce F2=0."""
        sanitized["url"] = "https://google.com/path"
        vector = builder.extract(sanitized)
        assert vector[1] == 0.0

    def test_f2_subdomains_counted_correctly(self, builder, sanitized):
        """mail.accounts.google.com has 2 subdomains."""
        sanitized["url"] = "https://mail.accounts.google.com/inbox"
        vector = builder.extract(sanitized)
        assert vector[1] == 2.0

    # F3 — has_suspicious_keywords
    def test_f3_suspicious_keyword_in_context(self, builder, sanitized):
        """'URGENT' in page_context must set F3=1.0."""
        sanitized["page_context"] = "URGENT: Verify your credentials"
        vector = builder.extract(sanitized)
        assert vector[2] == 1.0

    def test_f3_no_suspicious_keyword(self, builder, sanitized):
        """Benign context must set F3=0.0."""
        sanitized["url"] = "https://en.wikipedia.org/wiki/Python"
        sanitized["page_context"] = "Python is a programming language."
        vector = builder.extract(sanitized)
        assert vector[2] == 0.0

    # F4 — contains_ip_address
    def test_f4_ip_in_url(self, builder, sanitized):
        """URL with raw IP address must set F4=1.0."""
        sanitized["url"] = "http://192.168.1.1/login"
        vector = builder.extract(sanitized)
        assert vector[3] == 1.0

    def test_f4_no_ip_in_url(self, builder, sanitized):
        """Normal domain URL must set F4=0.0."""
        sanitized["url"] = "https://legitimate-bank.com/login"
        vector = builder.extract(sanitized)
        assert vector[3] == 0.0

    # F5 — is_https
    def test_f5_https_url(self, builder, sanitized):
        """HTTPS URL must set F5=1.0."""
        sanitized["url"] = "https://secure-site.com"
        vector = builder.extract(sanitized)
        assert vector[4] == 1.0

    def test_f5_http_url(self, builder, sanitized):
        """HTTP URL must set F5=0.0."""
        sanitized["url"] = "http://insecure-site.com"
        vector = builder.extract(sanitized)
        assert vector[4] == 0.0

    # F6 — time_of_day_encoded
    def test_f6_morning(self, builder, sanitized):
        """08:00 must encode as 0.0 (Morning)."""
        sanitized["timestamp"] = "2026-03-10T08:00:00Z"
        vector = builder.extract(sanitized)
        assert vector[5] == 0.0

    def test_f6_afternoon(self, builder, sanitized):
        """14:00 must encode as 1.0 (Afternoon)."""
        sanitized["timestamp"] = "2026-03-10T14:00:00Z"
        vector = builder.extract(sanitized)
        assert vector[5] == 1.0

    def test_f6_night(self, builder, sanitized):
        """22:00 must encode as 2.0 (Night)."""
        sanitized["timestamp"] = "2026-03-10T22:00:00Z"
        vector = builder.extract(sanitized)
        assert vector[5] == 2.0

    # F7 — session_fatigue_index
    def test_f7_defaults_to_zero(self, builder, sanitized):
        """Without session_context, F7 must default to 0.0."""
        vector = builder.extract(sanitized)
        assert vector[6] == 0.0

    def test_f7_accepts_session_context(self, builder, sanitized):
        """F7 must reflect provided session_fatigue_index."""
        vector = builder.extract(sanitized, session_context={"session_fatigue_index": 0.7})
        assert vector[6] == pytest.approx(0.7)

    def test_f7_clamped_above_one(self, builder, sanitized):
        """F7 must clamp values > 1.0 to 1.0."""
        vector = builder.extract(sanitized, session_context={"session_fatigue_index": 1.5})
        assert vector[6] == 1.0

    # F8 — trigger_type_encoded
    def test_f8_urgency_encodes_to_one(self, builder, sanitized):
        """trigger_type='urgency' must encode F8=1.0."""
        sanitized["trigger_type"] = "urgency"
        vector = builder.extract(sanitized)
        assert vector[7] == 1.0

    def test_f8_authority_encodes_to_two(self, builder, sanitized):
        """trigger_type='authority' must encode F8=2.0."""
        sanitized["trigger_type"] = "authority"
        vector = builder.extract(sanitized)
        assert vector[7] == 2.0

    def test_f8_none_encodes_to_zero(self, builder, sanitized):
        """Absent trigger_type must encode F8=0.0."""
        sanitized["trigger_type"] = None
        vector = builder.extract(sanitized)
        assert vector[7] == 0.0

    def test_f8_cognitive_model_format_accepted(self, builder, sanitized):
        """CognitiveModel output format 'Urgency_Bias' must encode F8=1.0."""
        sanitized["trigger_type"] = "Urgency_Bias"
        vector = builder.extract(sanitized)
        assert vector[7] == 1.0

    def test_missing_url_raises(self, builder, sanitized):
        """Missing URL in sanitized data must raise FeatureExtractionError."""
        sanitized["url"] = ""
        with pytest.raises(FeatureExtractionError):
            builder.extract(sanitized)


# ===========================================================================
# RiskScoringEngine Tests (Placeholder Mode)
# ===========================================================================

class TestRiskScoringEngine:
    """DDD 5.1.1 — Risk score calculation."""

    @pytest.fixture
    def high_risk_vector(self):
        """Feature vector representing a highly suspicious phishing URL."""
        # url_length=80, subdomains=3, suspicious=1, ip=0, http=0,
        # night=2, fatigue=0.8, urgency=1
        return [80.0, 3.0, 1.0, 0.0, 0.0, 2.0, 0.8, 1.0]

    @pytest.fixture
    def low_risk_vector(self):
        """Feature vector representing a safe, benign URL."""
        # url_length=20, subdomains=0, suspicious=0, ip=0, https=1,
        # morning=0, fatigue=0.0, no_trigger=0
        return [20.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]

    def test_returns_threat_score_and_delta(self, engine, high_risk_vector):
        """Output must contain both 'threat_score' and 'risk_delta' keys."""
        result = engine.predict(high_risk_vector)
        assert "threat_score" in result
        assert "risk_delta" in result

    def test_threat_score_in_valid_range(self, engine, high_risk_vector):
        """threat_score must be an integer between 0 and 100 inclusive."""
        result = engine.predict(high_risk_vector)
        assert isinstance(result["threat_score"], int)
        assert 0 <= result["threat_score"] <= 100

    def test_high_risk_vector_scores_higher_than_low_risk(
        self, engine, high_risk_vector, low_risk_vector
    ):
        """A high-risk feature vector must produce a higher score than a low-risk one."""
        high_result = engine.predict(high_risk_vector)
        low_result  = engine.predict(low_risk_vector)
        assert high_result["threat_score"] > low_result["threat_score"]

    def test_risk_delta_is_positive_for_threat(self, engine, high_risk_vector):
        """A phishing detection should produce a positive risk_delta."""
        result = engine.predict(high_risk_vector)
        assert result["risk_delta"] > 0

    def test_model_source_is_placeholder(self, engine, high_risk_vector):
        """Until trained model is loaded, model_source must be 'placeholder'."""
        result = engine.predict(high_risk_vector)
        assert result["model_source"] == "placeholder"

    def test_wrong_vector_length_raises(self, engine):
        """Vectors that are not exactly 8 elements must raise ScoringError."""
        with pytest.raises(ScoringError):
            engine.predict([1.0, 2.0, 3.0])  # too short

    def test_wrong_type_raises(self, engine):
        """Non-list input must raise ScoringError."""
        with pytest.raises(ScoringError):
            engine.predict("not-a-vector")

    def test_ip_address_url_scores_high(self, engine):
        """F4=1 (IP in URL) is a strong phishing signal — score must be >= 40."""
        vector = [30.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        result = engine.predict(vector)
        assert result["threat_score"] >= 40

    def test_is_model_loaded_false_before_training(self, engine):
        """is_model_loaded() must return False until artifact is deployed."""
        assert engine.is_model_loaded() is False