import pytest
import sys
from unittest.mock import patch, MagicMock

# Mock neo4j_client before any imports touch it
sys.modules['neo4j_client'] = MagicMock()

from backend.ml_pipeline.recommendation_engine import RecommendationEngine

@pytest.fixture
def engine():
    return RecommendationEngine()


class TestAssignTraining:

    def test_ac1_returns_assigned_module_key(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Urgency")
        assert "assigned_module" in result

    def test_ac1_urgency_trigger_returns_module(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Urgency")
        assert result["assigned_module"] == "TM-URG-01"

    def test_ac2_urgency_maps_to_tm_urg_01(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Urgency")
        assert result["assigned_module"] == "TM-URG-01"

    def test_ac2_authority_maps_to_tm_aut_01(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Authority")
        assert result["assigned_module"] == "TM-AUT-01"

    def test_ac2_scarcity_maps_to_tm_sca_01(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Scarcity")
        assert result["assigned_module"] == "TM-SCA-01"

    def test_ac2_social_proof_maps_to_tm_soc_01(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Social Proof")
        assert result["assigned_module"] == "TM-SOC-01"

    def test_ac2_bias_label_format_accepted(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Urgency_Bias")
        assert result["assigned_module"] == "TM-URG-01"

    def test_ac4_due_date_set_7_days(self, engine):
        from datetime import datetime, timedelta
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Urgency")
        assert "due_date" in result
        due = datetime.fromisoformat(result["due_date"].replace("Z", ""))
        now = datetime.utcnow()
        delta = due - now
        assert 6 <= delta.days <= 7

    def test_ac4_assigned_training_neo4j_called(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None) as mock_get, \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module") as mock_assign:
            engine.assign_training("user-001", "Urgency")
        mock_assign.assert_called_once()
        call_args = mock_assign.call_args
        assert call_args[0][0] == "user-001"
        assert call_args[0][1] == "TM-URG-01"

    def test_ac5_existing_assignment_not_reassigned(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value="TM-URG-01"), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module") as mock_assign:
            result = engine.assign_training("user-001", "Urgency")
        mock_assign.assert_not_called()
        assert result["assigned_module"] == "TM-URG-01"
        assert result["status"] == "existing_assignment"

    def test_ac5_new_assignment_when_no_existing(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Urgency")
        assert result["status"] == "assigned"

    def test_unknown_trigger_returns_none_module(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            result = engine.assign_training("user-001", "Unknown_Trigger")
        assert result["assigned_module"] is None
        assert result["status"] == "unknown_trigger"


class TestMABConfidence:

    def test_ac3_initial_confidence_is_fifty_percent(self, engine):
        scores = engine.get_confidence_scores()
        assert scores["Urgency"]["TM-URG-01"] == pytest.approx(0.5, abs=0.01)

    def test_ac3_confidence_increases_after_positive_reward(self, engine):
        initial = engine.get_confidence_scores()["Urgency"]["TM-URG-01"]
        engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.25)
        updated = engine.get_confidence_scores()["Urgency"]["TM-URG-01"]
        assert updated > initial

    def test_ac3_confidence_decreases_after_zero_reward(self, engine):
        initial = engine.get_confidence_scores()["Urgency"]["TM-URG-01"]
        engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.0)
        updated = engine.get_confidence_scores()["Urgency"]["TM-URG-01"]
        assert updated < initial

    def test_ac3_confidence_between_zero_and_one(self, engine):
        for _ in range(5):
            engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.3)
        score = engine.get_confidence_scores()["Urgency"]["TM-URG-01"]
        assert 0.0 <= score <= 1.0

    def test_ac3_all_trigger_types_have_confidence_scores(self, engine):
        scores = engine.get_confidence_scores()
        for trigger in ["Urgency", "Authority", "Scarcity", "Social Proof"]:
            assert trigger in scores


class TestRecordCompletion:

    def test_ac6_returns_updated_status(self, engine):
        result = engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.25)
        assert result["status"] == "updated"

    def test_ac6_positive_delta_gives_reward_one(self, engine):
        result = engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.25)
        assert result["reward"] == 1.0

    def test_ac6_zero_delta_gives_reward_zero(self, engine):
        result = engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.0)
        assert result["reward"] == 0.0

    def test_ac6_returns_confidence_score(self, engine):
        result = engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.25)
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_ac6_unknown_module_returns_unknown_status(self, engine):
        result = engine.record_completion("user-001", "TM-UNKNOWN-99", susceptibility_delta=0.25)
        assert result["status"] == "unknown_module"

    def test_ac6_multiple_completions_converge_confidence(self, engine):
        for _ in range(10):
            engine.record_completion("user-001", "TM-URG-01", susceptibility_delta=0.3)
        score = engine.get_confidence_scores()["Urgency"]["TM-URG-01"]
        assert score > 0.7


class TestThompsonSampling:

    def test_thompson_always_returns_valid_module(self, engine):
        for trigger in ["Urgency", "Authority", "Scarcity", "Social Proof"]:
            module = engine._thompson_sample(trigger)
            assert module is not None
            assert module.startswith("TM-")

    def test_thompson_returns_correct_module_for_trigger(self, engine):
        assert engine._thompson_sample("Urgency") == "TM-URG-01"
        assert engine._thompson_sample("Authority") == "TM-AUT-01"
        assert engine._thompson_sample("Scarcity") == "TM-SCA-01"
        assert engine._thompson_sample("Social Proof") == "TM-SOC-01"


class TestEndToEnd:

    def test_ac7_urgency_click_assigns_tm_urg_01(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module") as mock_assign:
            result = engine.assign_training("agent_alex_001", "Urgency_Bias")

        assert result["assigned_module"] == "TM-URG-01"
        assert result["trigger"] == "Urgency"
        assert result["status"] == "assigned"
        mock_assign.assert_called_once()
        args = mock_assign.call_args[0]
        assert args[0] == "agent_alex_001"
        assert args[1] == "TM-URG-01"

    def test_full_mab_loop(self, engine):
        with patch("backend.ml_pipeline.recommendation_engine.get_active_assignment", return_value=None), \
             patch("backend.ml_pipeline.recommendation_engine.assign_training_module"):
            assignment = engine.assign_training("agent_alex_001", "Urgency_Bias")

        assert assignment["assigned_module"] == "TM-URG-01"

        completion = engine.record_completion(
            "agent_alex_001", "TM-URG-01", susceptibility_delta=0.25
        )
        assert completion["reward"] == 1.0
        assert completion["confidence"] > 0.5