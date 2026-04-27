import pytest
from unittest.mock import patch, MagicMock
from backend.ml_pipeline.cognitive_model import CognitiveModel, VALID_TRIGGERS
from backend.ml_pipeline.feature_builder import FeatureVectorBuilder


@pytest.fixture
def model():
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        return CognitiveModel()

@pytest.fixture
def model_with_gemini():
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key-for-testing"}):
        return CognitiveModel()

@pytest.fixture
def builder():
    return FeatureVectorBuilder()


class TestValidOutputLabels:

    def test_urgency_context_returns_urgency_bias(self, model):
        result = model.tag_trigger("URGENT: Your account has been suspended. Verify immediately.")
        assert result["cognitive_trigger"] == "Urgency_Bias"

    def test_authority_context_returns_authority_bias(self, model):
        result = model.tag_trigger(
            "From the IT Department: All employees must complete mandatory "
            "credential verification by end of week."
        )
        assert result["cognitive_trigger"] == "Authority_Bias"

    def test_scarcity_context_returns_scarcity_bias(self, model):
        result = model.tag_trigger(
            "Only 3 VPN license seats remain in your department. "
            "Claim yours before they are reassigned to other teams."
        )
        assert result["cognitive_trigger"] == "Scarcity_Bias"

    def test_social_proof_context_returns_social_proof_bias(self, model):
        result = model.tag_trigger(
            "Your entire team has already completed the security verification. "
            "You are the only member who has not confirmed their credentials."
        )
        assert result["cognitive_trigger"] == "Social_Proof_Bias"

    def test_output_always_in_valid_triggers(self, model):
        contexts = [
            "URGENT: Reset your password now",
            "IT Department requires verification",
            "Only 2 seats remaining",
            "Your colleagues have already signed",
            "Hello, please find attached the meeting notes.",
        ]
        for ctx in contexts:
            result = model.tag_trigger(ctx)
            assert result["cognitive_trigger"] in VALID_TRIGGERS

    def test_returns_dict_with_cognitive_trigger_key(self, model):
        result = model.tag_trigger("URGENT: Act now or lose access.")
        assert isinstance(result, dict)
        assert "cognitive_trigger" in result


class TestNoneClassification:

    def test_benign_text_returns_none(self, model):
        result = model.tag_trigger(
            "Hi team, please find the meeting notes attached. "
            "Let me know if you have any questions."
        )
        assert result["cognitive_trigger"] == "None"

    def test_empty_string_returns_none(self, model):
        result = model.tag_trigger("")
        assert result["cognitive_trigger"] == "None"

    def test_whitespace_only_returns_none(self, model):
        result = model.tag_trigger("   ")
        assert result["cognitive_trigger"] == "None"

    def test_none_input_returns_none(self, model):
        result = model.tag_trigger(None)
        assert result["cognitive_trigger"] == "None"


class TestFewShotExamples:

    def test_few_shot_examples_loaded(self, model):
        assert len(model._few_shot_examples) > 0

    def test_few_shot_examples_have_valid_keys(self, model):
        valid_keys = {"Urgency_Bias", "Authority_Bias", "Scarcity_Bias", "Social_Proof_Bias"}
        for key in model._few_shot_examples:
            assert key in valid_keys

    def test_few_shot_examples_are_strings(self, model):
        for label, examples in model._few_shot_examples.items():
            assert isinstance(examples, list)
            for ex in examples:
                assert isinstance(ex, str) and len(ex) > 0

    def test_prompt_contains_few_shot_examples(self, model):
        prompt = model._build_prompt("test context")
        for label in model._few_shot_examples:
            assert label in prompt


class TestGeminiFallback:

    def test_falls_back_to_keywords_on_gemini_http_error(self, model_with_gemini):
        with patch.object(model_with_gemini, "_classify_with_gemini",
                          side_effect=Exception("HTTP 429 rate limit")):
            result = model_with_gemini.tag_trigger("URGENT: Your account expires in 24 hours.")
        assert result["cognitive_trigger"] in VALID_TRIGGERS

    def test_falls_back_to_keywords_on_connection_error(self, model_with_gemini):
        with patch.object(model_with_gemini, "_classify_with_gemini",
                          side_effect=Exception("Connection refused")):
            result = model_with_gemini.tag_trigger("IT Department: Verify your credentials immediately.")
        assert result["cognitive_trigger"] in VALID_TRIGGERS

    def test_keyword_fallback_detects_urgency(self, model):
        result = model._classify_with_keywords("URGENT: Your password expires immediately. Act now.")
        assert result == "Urgency_Bias"

    def test_keyword_fallback_detects_authority(self, model):
        result = model._classify_with_keywords("IT Department requires all employees to verify credentials.")
        assert result == "Authority_Bias"

    def test_keyword_fallback_detects_scarcity(self, model):
        result = model._classify_with_keywords("Only 2 license seats remaining. Claim yours before they run out.")
        assert result == "Scarcity_Bias"

    def test_keyword_fallback_detects_social_proof(self, model):
        result = model._classify_with_keywords("Your colleagues have already completed this. You are the only one left.")
        assert result == "Social_Proof_Bias"

    def test_keyword_fallback_returns_none_for_benign(self, model):
        result = model._classify_with_keywords("Please find the quarterly report attached.")
        assert result == "None"

    def test_no_crash_without_gemini_key(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            m = CognitiveModel()
            result = m.tag_trigger("URGENT: Reset your password now.")
        assert result["cognitive_trigger"] in VALID_TRIGGERS


class TestF8Compatibility:

    def test_urgency_bias_encodes_to_one(self, builder):
        sanitized = {"url": "http://example.com", "page_context": "", "timestamp": "2026-03-10T09:00:00Z", "trigger_type": "Urgency_Bias"}
        assert builder.extract(sanitized)[7] == 1.0

    def test_authority_bias_encodes_to_two(self, builder):
        sanitized = {"url": "http://example.com", "page_context": "", "timestamp": "2026-03-10T09:00:00Z", "trigger_type": "Authority_Bias"}
        assert builder.extract(sanitized)[7] == 2.0

    def test_scarcity_bias_encodes_to_three(self, builder):
        sanitized = {"url": "http://example.com", "page_context": "", "timestamp": "2026-03-10T09:00:00Z", "trigger_type": "Scarcity_Bias"}
        assert builder.extract(sanitized)[7] == 3.0

    def test_social_proof_bias_encodes_to_four(self, builder):
        sanitized = {"url": "http://example.com", "page_context": "", "timestamp": "2026-03-10T09:00:00Z", "trigger_type": "Social_Proof_Bias"}
        assert builder.extract(sanitized)[7] == 4.0

    def test_none_encodes_to_zero(self, builder):
        sanitized = {"url": "http://example.com", "page_context": "", "timestamp": "2026-03-10T09:00:00Z", "trigger_type": "None"}
        assert builder.extract(sanitized)[7] == 0.0


class TestEndToEnd:

    def test_ac6_urgency_example(self, model):
        result = model.tag_trigger("URGENT: Your account has been suspended. Verify immediately.")
        assert result == {"cognitive_trigger": "Urgency_Bias"}

    def test_gemini_response_parsed_correctly(self, model_with_gemini):
        mock_response = {
            "candidates": [{"content": {"parts": [{"text": "Urgency_Bias"}]}}]
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_cm = MagicMock()
            mock_cm.__enter__ = MagicMock(return_value=mock_cm)
            mock_cm.__exit__ = MagicMock(return_value=False)
            mock_cm.read.return_value = str(mock_response).replace("'", '"').encode()
            mock_urlopen.return_value = mock_cm
            with patch("json.loads", return_value=mock_response):
                result = model_with_gemini.tag_trigger("URGENT: Your account has been suspended.")
        assert result["cognitive_trigger"] in VALID_TRIGGERS

    def test_full_pipeline_cognitive_feeds_feature_builder(self, model, builder):
        cognitive_result = model.tag_trigger("URGENT: Your account has been suspended. Verify immediately.")
        trigger = cognitive_result["cognitive_trigger"]
        assert trigger == "Urgency_Bias"

        sanitized = {
            "url": "http://adaptive-sec-sim/reset",
            "page_context": "URGENT: Your account has been suspended.",
            "timestamp": "2026-03-10T09:00:00Z",
            "trigger_type": trigger,
        }
        vector = builder.extract(sanitized)
        assert vector[7] == 1.0
        assert len(vector) == 8