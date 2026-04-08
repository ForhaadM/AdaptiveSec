import json
import pika
import logging
import redis
import os
from datetime import datetime, timedelta

from ml_pipeline.preprocessor import DataPreprocessor
from ml_pipeline.feature_builder import FeatureVectorBuilder
from ml_pipeline.risk_engine import RiskScoringEngine
from ml_pipeline.cognitive_model import CognitiveModel
from neo4j_client import (
    update_trigger_weight, assign_training_module,
    get_active_assignment, persist_risk_score, create_score_history
)

logger = logging.getLogger(__name__)

QUEUE_NAME = "simulation_events"

TRIGGER_MAP = {
    "urgency": "Urgency",
    "authority": "Authority",
    "scarcity": "Scarcity",
    "social_proof": "Social Proof",
}

TRIGGER_TO_MODULE = {
    "Urgency": "TM-URG-01",
    "Authority": "TM-AUT-01",
    "Scarcity": "TM-SCA-01",
    "Social Proof": "TM-SOC-01",
}


def process_event(body):
    event = json.loads(body)
    print("Received click event:", event)

    pre = DataPreprocessor()
    sanitized = pre.sanitize(event)

    builder = FeatureVectorBuilder()
    features = builder.extract(sanitized)

    engine = RiskScoringEngine()
    result = engine.predict(features)

    threat_score = result["threat_score"]
    risk_delta = result["risk_delta"]
    model_source = result["model_source"]

    print("Sanitized payload:", sanitized)
    print("Feature vector:", features)
    print(
        f"Threat score: {threat_score}, Risk delta: {risk_delta}, "
        f"model_source: {model_source}"
    )

    user_id = event["user_id"]
    raw_trigger = event.get("trigger_type")

    # AC1 + AC2 + AC6 — Persist score to Neo4j and cache in Redis
    try:
        persist_risk_score(user_id, threat_score)
        create_score_history(
            user_id=user_id,
            score=threat_score,
            delta=risk_delta,
            reason=raw_trigger or "unknown"
        )
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.setex(f"risk_score:{user_id}", 60, str(threat_score))
        print(f"[Worker] Score persisted and cached for {user_id}: {threat_score}")
    except Exception as e:
        logger.warning(f"[Worker] Score persist failed: {e}")

    # AC1 + AC2: update VULNERABLE_TO edge with correct schema trigger name
    if raw_trigger:
        schema_trigger = TRIGGER_MAP.get(raw_trigger.lower())
        if schema_trigger:
            update_trigger_weight(user_id, schema_trigger)
            print(f"Updated VULNERABLE_TO: {user_id} -> {schema_trigger}")

            # AC3: assign training module if not already assigned
            existing = get_active_assignment(user_id, schema_trigger)
            if not existing:
                module_id = TRIGGER_TO_MODULE.get(schema_trigger)
                if module_id:
                    due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                    assign_training_module(user_id, module_id, due_date)
                    print(f"Assigned training: {user_id} -> {module_id} due={due_date}")
            else:
                print(f"Training already assigned: {user_id} -> {existing}")
        else:
            print(f"Unknown trigger type: {raw_trigger}, skipping Neo4j update")
    else:
        print("No trigger_type in event, skipping Neo4j update")

    # CognitiveModel confirmation
    try:
        cognitive_model = CognitiveModel()
        tag_result = cognitive_model.tag_trigger(
            sanitized.get("page_context", "")
        )
        cognitive_trigger = tag_result.get("cognitive_trigger")

        if cognitive_trigger and cognitive_trigger != "None":
            update_trigger_weight(user_id, cognitive_trigger)
            print(f"CognitiveModel confirmed trigger: {cognitive_trigger}")
    except Exception as e:
        logger.warning(f"CognitiveModel failed: {e}")


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
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()