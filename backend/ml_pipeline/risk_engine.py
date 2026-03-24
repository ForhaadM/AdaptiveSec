import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


_MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "models")
_MODEL_PATH = os.path.join(_MODEL_DIR, "xgboost_risk_model.json")

_DELTA_THRESHOLDS: list[tuple[int, int]] = [
    (80, 15),   # threat_score >= 80 → +15 delta (high risk)
    (60, 10),   # threat_score >= 60 → +10 delta
    (40,  5),   # threat_score >= 40 → +5 delta
    (20,  2),   # threat_score >= 20 → +2 delta
    (0,   1),   # threat_score >= 0  → +1 delta (baseline)
]

MODEL_LOADED = False
class ScoringError(Exception):
    pass
class RiskScoringEngine:
    FEATURE_COUNT = 8

    def __init__(self) -> None:
        self._model = None
        self._try_load_model()

    def predict(self, feature_vector: list[float]) -> dict[str, Any]:

        self._validate_vector(feature_vector)

        if self._model is not None:
            return self._predict_xgboost(feature_vector)
        else:
            return self._predict_placeholder(feature_vector)

    def is_model_loaded(self) -> bool:
        return self._model is not None
    def _try_load_model(self) -> None:

        try:
            import xgboost as xgb
            if os.path.exists(_MODEL_PATH):
                self._model = xgb.XGBClassifier()
                self._model.load_model(_MODEL_PATH)
                global MODEL_LOADED
                MODEL_LOADED = True
                logger.info("XGBoost model loaded from %s", _MODEL_PATH)
            else:
                logger.warning(
                    "Model artifact not found at '%s'. "
                    "Run scripts/train_xgboost.py to generate it. "
                    "Falling back to placeholder mode.",
                    _MODEL_PATH,
                )
        except ImportError:
            logger.warning(
                "xgboost package not installed. "
                "Run: pip install xgboost. "
                "Falling back to placeholder mode."
            )

    def _predict_xgboost(self, feature_vector: list[float]) -> dict[str, Any]:
        import numpy as np
        x            = np.array(feature_vector, dtype=float).reshape(1, -1)
        raw_score    = float(self._model.predict_proba(x)[0][1]) * 100
        threat_score = int(round(raw_score))
        risk_delta   = self._score_to_delta(threat_score)
        logger.debug("XGBoost scoring | threat_score=%d | risk_delta=%+d", threat_score, risk_delta)
        return {"threat_score": threat_score, "risk_delta": risk_delta, "model_source": "xgboost"}

    def _predict_placeholder(self, feature_vector: list[float]) -> dict[str, Any]:
        f1_url_length, f2_subdomains, f3_suspicious, f4_ip, f5_https, \
            f6_time_of_day, f7_fatigue, f8_trigger = feature_vector

        score = 0.0

        # URL structural signals
        if f1_url_length > 75:
            score += 15.0
        elif f1_url_length > 40:
            score += 8.0

        if f2_subdomains >= 3:
            score += 15.0
        elif f2_subdomains >= 2:
            score += 8.0

        # Content signals
        if f3_suspicious:
            score += 20.0

        if f4_ip:
            score += 25.0   # Raw IP in URL is a strong phishing signal

        # Protocol signal (absence of HTTPS increases risk)
        if not f5_https:
            score += 15.0

        # Behavioral modifiers
        if f6_time_of_day == 2.0:  # Night — elevated fatigue risk
            score += 5.0

        score += f7_fatigue * 10.0  # Fatigue index amplifier

        # Cognitive trigger amplifier (F8 weight)
        trigger_weights = {0.0: 1.0, 1.0: 1.3, 2.0: 1.2, 3.0: 1.1, 4.0: 1.1}
        trigger_multiplier = trigger_weights.get(f8_trigger, 1.0)
        score *= trigger_multiplier

        threat_score = int(min(100, max(0, round(score))))
        risk_delta   = self._score_to_delta(threat_score)

        logger.debug(
            "Placeholder scoring | threat_score=%d | risk_delta=%+d | trigger_weight=%.1f",
            threat_score, risk_delta, trigger_multiplier,
        )

        return {
            "threat_score": threat_score,
            "risk_delta":   risk_delta,
            "model_source": "placeholder",
        }

    def _score_to_delta(self, threat_score: int) -> int:
        for threshold, delta in _DELTA_THRESHOLDS:
            if threat_score >= threshold:
                return delta
        return 1

    def _validate_vector(self, feature_vector: list[float]) -> None:
        """Raise ScoringError if the vector is the wrong length or type."""
        if not isinstance(feature_vector, (list, tuple)):
            raise ScoringError(
                f"feature_vector must be a list or tuple, got {type(feature_vector).__name__}."
            )
        if len(feature_vector) != self.FEATURE_COUNT:
            raise ScoringError(
                f"feature_vector must have exactly {self.FEATURE_COUNT} elements "
                f"(F1–F8), got {len(feature_vector)}."
            )