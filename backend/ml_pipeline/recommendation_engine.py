# ---------------------------------------------------------------------------
# MAB Algorithm: Thompson Sampling
#
# Current implementation uses Thompson Sampling as the sole selection
# algorithm. This was chosen because:
#   - The dataset starts small (one completion per user per trigger)
#   - Thompson Sampling handles low sample sizes better than UCB1
#   - Converges faster than e-Greedy in sparse reward environments
#
# Future upgrade path — Ensemble MAB:
#   When multiple training modules exist per trigger type, consider
#   combining all three algorithms via majority vote:
#   - Thompson Sampling  (probabilistic, handles uncertainty)
#   - UCB1               (deterministic, explainable confidence bounds)
#   - e-Greedy           (simple exploration/exploitation tradeoff)
#   The module recommended by 2+ algorithms wins; Thompson Sampling
#   breaks ties. This requires no interface changes to assign_training().
# ---------------------------------------------------------------------------

import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any

import numpy as np
try:
    from neo4j_client import assign_training_module, get_active_assignment
except ModuleNotFoundError:
    from backend.neo4j_client import assign_training_module, get_active_assignment

logger = logging.getLogger(__name__)

TRIGGER_LABEL_MAP = {
    "Urgency_Bias":      "Urgency",
    "Authority_Bias":    "Authority",
    "Scarcity_Bias":     "Scarcity",
    "Social_Proof_Bias": "Social Proof",
    "urgency":           "Urgency",
    "authority":         "Authority",
    "scarcity":          "Scarcity",
    "social proof":      "Social Proof",
    "social_proof":      "Social Proof",
}

DEFAULT_MODULE_MAP = {
    "Urgency":      ["TM-URG-01"],
    "Authority":    ["TM-AUT-01"],
    "Scarcity":     ["TM-SCA-01"],
    "Social Proof": ["TM-SOC-01"],
}

DUE_DATE_DAYS = 7


class RecommendationEngine:

    def __init__(self):
        self._mab_state: dict[str, dict[str, dict[str, float]]] = {
            trigger: {
                module: {"alpha": 1.0, "beta": 1.0}
                for module in modules
            }
            for trigger, modules in DEFAULT_MODULE_MAP.items()
        }
        logger.info("RecommendationEngine initialized | MAB state: Thompson Sampling")

    def assign_training(
        self,
        user_id: str,
        cognitive_trigger: str,
    ) -> dict[str, Any]:
       

        trigger_name = self._resolve_trigger(cognitive_trigger)
        if not trigger_name:
            logger.warning("Unknown cognitive trigger: %s — no module assigned.", cognitive_trigger)
            return {"assigned_module": None, "trigger": cognitive_trigger, "status": "unknown_trigger"}

        existing = get_active_assignment(user_id, trigger_name)
        if existing:
            logger.info(
                "User %s already has active assignment %s for %s — skipping reassignment.",
                user_id[:8], existing, trigger_name,
            )
            return {
                "assigned_module": existing,
                "trigger":         trigger_name,
                "status":          "existing_assignment",
            }

        module_id = self._thompson_sample(trigger_name)
        due_date  = (datetime.utcnow() + timedelta(days=DUE_DATE_DAYS)).isoformat() + "Z"

        assign_training_module(user_id, module_id, due_date)

        logger.info(
            "Assigned %s to user %s for trigger %s | due=%s",
            module_id, user_id[:8], trigger_name, due_date,
        )

        return {
            "assigned_module": module_id,
            "trigger":         trigger_name,
            "due_date":        due_date,
            "status":          "assigned",
        }

    def record_completion(
        self,
        user_id: str,
        module_id: str,
        susceptibility_delta: float,
    ) -> dict[str, Any]:
        trigger_name = self._find_trigger_for_module(module_id)
        if not trigger_name:
            logger.warning("Cannot find trigger for module %s — MAB not updated.", module_id)
            return {"status": "unknown_module"}

        reward = 1.0 if susceptibility_delta > 0 else 0.0

        if trigger_name in self._mab_state and module_id in self._mab_state[trigger_name]:
            if reward > 0:
                self._mab_state[trigger_name][module_id]["alpha"] += reward
            else:
                self._mab_state[trigger_name][module_id]["beta"] += 1.0

        confidence = self._get_confidence(trigger_name, module_id)

        logger.info(
            "MAB updated | trigger=%s | module=%s | reward=%.1f | "
            "alpha=%.1f | beta=%.1f | confidence=%.3f",
            trigger_name, module_id, reward,
            self._mab_state[trigger_name][module_id]["alpha"],
            self._mab_state[trigger_name][module_id]["beta"],
            confidence,
        )

        return {
            "status":        "updated",
            "trigger":       trigger_name,
            "module_id":     module_id,
            "reward":        reward,
            "confidence":    confidence,
        }

    def get_confidence_scores(self) -> dict[str, dict[str, float]]:
        scores = {}
        for trigger, modules in self._mab_state.items():
            scores[trigger] = {}
            for module_id, params in modules.items():
                scores[trigger][module_id] = self._get_confidence(trigger, module_id)
        return scores

    def _thompson_sample(self, trigger_name: str) -> str:
        if trigger_name not in self._mab_state:
            return DEFAULT_MODULE_MAP[trigger_name][0]

        modules = self._mab_state[trigger_name]
        samples = {
            module_id: np.random.beta(params["alpha"], params["beta"])
            for module_id, params in modules.items()
        }
        return max(samples, key=lambda k: samples[k])

    def _get_confidence(self, trigger_name: str, module_id: str) -> float:
        if trigger_name not in self._mab_state:
            return 0.0
        if module_id not in self._mab_state[trigger_name]:
            return 0.0
        params = self._mab_state[trigger_name][module_id]
        alpha  = params["alpha"]
        beta   = params["beta"]
        return round(alpha / (alpha + beta), 3)

    def _resolve_trigger(self, cognitive_trigger: str) -> str | None:
        if cognitive_trigger in DEFAULT_MODULE_MAP:
            return cognitive_trigger
        normalized = TRIGGER_LABEL_MAP.get(cognitive_trigger)
        if normalized:
            return normalized
        lower = cognitive_trigger.lower().replace("_bias", "").replace("_", " ").strip()
        return TRIGGER_LABEL_MAP.get(lower)

    def _find_trigger_for_module(self, module_id: str) -> str | None:
        for trigger, modules in DEFAULT_MODULE_MAP.items():
            if module_id in modules:
                return trigger
        return None