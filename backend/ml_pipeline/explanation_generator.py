import os
import json
import logging
import redis as sync_redis
from google import genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env")

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a supportive cybersecurity coach helping employees 
improve their security awareness. Your job is to explain why a simulated 
phishing attempt was successful in a kind, educational, and non-judgmental way.

STRICT RULES:
- Never use phrases like "you failed", "you should have known", "you made a mistake"
- Always be encouraging and forward-looking
- Keep explanations under 3 sentences
- Always end with one concrete actionable tip
"""

TRIGGER_DESCRIPTIONS = {
    "Urgency_Bias": "time pressure and urgency",
    "Authority_Bias": "authority and official-looking requests",
    "Scarcity_Bias": "scarcity and limited availability",
    "SocialProof_Bias": "social proof and peer influence",
    "None": "general deception tactics",
}

FALLBACK_TEMPLATES = {
    "Urgency_Bias": (
        "Your score increased because you clicked a link that used time pressure "
        "to encourage a quick decision — this is called an Urgency Bias trigger. "
        "Next time, pause for 10 seconds before clicking any link that claims "
        "something will expire or requires immediate action."
    ),
    "Authority_Bias": (
        "Your score increased because you clicked a link that appeared to come "
        "from an official or authoritative source — this is called an Authority "
        "Bias trigger. Next time, verify requests directly with the sender through "
        "a separate communication channel."
    ),
    "Scarcity_Bias": (
        "Your score increased because you clicked a link that created a sense of "
        "limited availability — this is called a Scarcity Bias trigger. Next time, "
        "be skeptical of any message claiming only a few spots or resources remain."
    ),
    "SocialProof_Bias": (
        "Your score increased because you clicked a link that suggested others "
        "had already taken action — this is called a Social Proof Bias trigger. "
        "Next time, verify claims about what your colleagues have done directly "
        "with them before acting."
    ),
    "None": (
        "Your score increased because you clicked a suspicious link. "
        "Next time, hover over links before clicking to verify the destination URL "
        "matches what you expect."
    ),
}


class ExplanationGenerator:

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(
        self,
        user_id: str,
        cognitive_trigger: str,
        risk_delta: int,
        page_context: str,
        event_id: str = None,
        new_score: int = None,
        new_training_id: str = None
    ) -> str:
        try:
            explanation = self._call_gemini(
                cognitive_trigger, risk_delta, page_context
            )
            logger.info(
                f"[ExplanationGenerator] Generated explanation for {user_id} "
                f"trigger={cognitive_trigger} delta={risk_delta}"
            )
        except Exception as e:
            logger.warning(
                f"[ExplanationGenerator] Gemini failed, using fallback: {e}"
            )
            explanation = self._fallback_explanation(cognitive_trigger, risk_delta)

        if event_id:
            try:
                from neo4j_client import store_explanation
                store_explanation(event_id, user_id, explanation, cognitive_trigger)
                logger.info(
                    f"[ExplanationGenerator] Stored explanation in Neo4j "
                    f"event_id={event_id}"
                )
            except Exception as e:
                logger.warning(
                    f"[ExplanationGenerator] Neo4j store failed: {e}"
                )

        alert_payload = {
            "event": "risk_update",
            "new_score": new_score,
            "score_change": risk_delta,
            "explanation": explanation,
            "new_training_id": new_training_id,
            "cognitive_trigger": cognitive_trigger
        }
        self.publish_to_redis(user_id, alert_payload)

        return explanation

    def publish_to_redis(self, user_id: str, alert_payload: dict):
        try:
            r = sync_redis.from_url(REDIS_URL)
            r.publish(f"alerts:{user_id}", json.dumps(alert_payload))
            logger.info(
                f"[ExplanationGenerator] Published alert to Redis "
                f"channel=alerts:{user_id}"
            )
        except Exception as e:
            logger.warning(
                f"[ExplanationGenerator] Redis publish failed: {e}"
            )

    def _call_gemini(
        self,
        cognitive_trigger: str,
        risk_delta: int,
        page_context: str
    ) -> str:
        trigger_desc = TRIGGER_DESCRIPTIONS.get(
            cognitive_trigger, "deception tactics"
        )

        prompt = f"""{SYSTEM_PROMPT}

A user just clicked a simulated phishing link during a security awareness training.

Phishing content they saw: "{page_context[:200]}"
Psychological tactic used: {trigger_desc}
Risk score increase: +{risk_delta} points

Write a 2-3 sentence explanation that:
1. Explains which cognitive bias was exploited and how it was used in this specific message
2. Mentions their score increased by {risk_delta} points
3. Gives one concrete tip to avoid this in the future

Be warm, encouraging, and specific to the message content above."""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()

    def _fallback_explanation(
        self,
        cognitive_trigger: str,
        risk_delta: int
    ) -> str:
        template = FALLBACK_TEMPLATES.get(
            cognitive_trigger,
            FALLBACK_TEMPLATES["None"]
        )
        return template.replace(
            "Your score increased",
            f"Your score increased by {risk_delta} points"
        )