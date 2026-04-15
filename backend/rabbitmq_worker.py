import json
import pika
import logging
import redis
import os
import uuid
from datetime import datetime, timedelta

from ml_pipeline.preprocessor import DataPreprocessor
from ml_pipeline.feature_builder import FeatureVectorBuilder
from ml_pipeline.risk_engine import RiskScoringEngine
from ml_pipeline.cognitive_model import CognitiveModel
from ml_pipeline.recommendation_engine import RecommendationEngine
from ml_pipeline.explanation_generator import ExplanationGenerator
from neo4j_client import (
    update_trigger_weight,
    persist_risk_score,
    create_score_history,
)

logger = logging.getLogger(__name__)

QUEUE_NAME = "simulation_events"

COGNITIVE_TO_SCHEMA = {
    "Urgency_Bias":      "Urgency",
    "Authority_Bias":    "Authority",
    "Scarcity_Bias":     "Scarcity",
    "Social_Proof_Bias": "Social Proof",
}

TRIGGER_TO_SCHEMA = {
    "urgency":      "Urgency",
    "authority":    "Authority",
    "scarcity":     "Scarcity",
    "social_proof": "Social Proof",
}

SCHEMA_TO_EXPLANATION_TRIGGER = {
    "Urgency":      "Urgency_Bias",
    "Authority":    "Authority_Bias",
    "Scarcity":     "Scarcity_Bias",
    "Social Proof": "SocialProof_Bias",
}


def process_event(body):
    event = json.loads(body)
    print("Received click event:", event)

    # Step 1 — DataPreprocessor
    pre = DataPreprocessor()
    sanitized = pre.sanitize(event)

    # Step 2 — FeatureVectorBuilder
    builder = FeatureVectorBuilder()
    features = builder.extract(sanitized)

    # Step 3 — RiskScoringEngine
    engine = RiskScoringEngine()
    result = engine.predict(features)

    threat_score = result["threat_score"]
    risk_delta   = result["risk_delta"]
    model_source = result["model_source"]

    print(f"Threat score: {threat_score}, Risk delta: {risk_delta}, model_source: {model_source}")

    user_id      = event["user_id"]
    raw_trigger  = event.get("trigger_type")
    page_context = sanitized.get("page_context", "")
    event_id     = event.get("event_id", str(uuid.uuid4()))

    # Persist score to Neo4j and cache in Redis
    try:
        persist_risk_score(user_id, threat_score)
        create_score_history(
            user_id=user_id,
            score=threat_score,
            delta=risk_delta,
            reason=raw_trigger or "unknown",
        )
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.setex(f"risk_score:{user_id}", 60, str(threat_score))
        print(f"[Worker] Score persisted and cached for {user_id}: {threat_score}")
    except Exception as e:
        logger.warning(f"[Worker] Score persist failed: {e}")

    # Step 4 — CognitiveModel: classify the psychological trigger from page content
    cognitive_trigger = "None"
    schema_trigger    = None

    try:
        cognitive_model  = CognitiveModel()
        tag_result       = cognitive_model.tag_trigger(page_context)
        cognitive_trigger = tag_result.get("cognitive_trigger", "None")
        print(f"[Worker] CognitiveModel result: {cognitive_trigger}")
    except Exception as e:
        logger.warning(f"[Worker] CognitiveModel failed: {e}")

    # Resolve schema trigger — prefer CognitiveModel output, fall back to raw trigger_type
    if cognitive_trigger and cognitive_trigger != "None":
        schema_trigger = COGNITIVE_TO_SCHEMA.get(cognitive_trigger)
    elif raw_trigger:
        schema_trigger = TRIGGER_TO_SCHEMA.get(raw_trigger.lower())

    # Update VULNERABLE_TO edge with resolved trigger
    if schema_trigger:
        try:
            update_trigger_weight(user_id, schema_trigger)
            print(f"[Worker] Updated VULNERABLE_TO: {user_id} -> {schema_trigger}")
        except Exception as e:
            logger.warning(f"[Worker] update_trigger_weight failed: {e}")

    # Step 5 — RecommendationEngine: MAB Thompson Sampling assigns training module
    new_training_id = None

    if schema_trigger:
        try:
            rec_engine = RecommendationEngine()
            assignment = rec_engine.assign_training(
                user_id=user_id,
                cognitive_trigger=cognitive_trigger if cognitive_trigger != "None" else schema_trigger,
            )
            new_training_id = assignment.get("assigned_module")
            print(f"[Worker] RecommendationEngine: {assignment}")
        except Exception as e:
            logger.warning(f"[Worker] RecommendationEngine failed: {e}")

    # Step 6 — ExplanationGenerator: Gemini plain-English alert + Redis publish
    try:
        explanation_trigger = (
            cognitive_trigger if cognitive_trigger != "None"
            else SCHEMA_TO_EXPLANATION_TRIGGER.get(schema_trigger, "None")
        )

        generator = ExplanationGenerator()
        generator.generate(
            user_id=user_id,
            cognitive_trigger=explanation_trigger,
            risk_delta=risk_delta,
            page_context=page_context,
            event_id=event_id,
            new_score=threat_score,
            new_training_id=new_training_id,
        )
        print(f"[Worker] ExplanationGenerator completed for {user_id}")
    except Exception as e:
        logger.warning(f"[Worker] ExplanationGenerator failed: {e}")


def callback(ch, method, properties, body):
    try:
        process_event(body)
    except Exception as e:
        logger.error(f"Error processing event: {e}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    print("Worker listening to RabbitMQ queue:", QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()