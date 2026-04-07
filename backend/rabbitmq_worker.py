import json
import pika

from ml_pipeline.preprocessor import DataPreprocessor
from ml_pipeline.feature_builder import FeatureVectorBuilder
from ml_pipeline.risk_engine import RiskScoringEngine
from neo4j_client import test_vulnerable_to_edge

QUEUE_NAME = "simulation_events"


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
        f"Threat score: {threat_score}, Risk delta: {risk_delta}, model_source: {model_source}"
    )

    user_id = event["user_id"]
    trigger = event.get("trigger_type", "unknown")

    test_vulnerable_to_edge(user_id, trigger, threat_score)


def callback(ch, method, properties, body):

    process_event(body)

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