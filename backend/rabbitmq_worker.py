import json
import pika

from ml_pipeline.preprocessor import DataPreprocessor
from ml_pipeline.feature_builder import FeatureVectorBuilder
from ml_pipeline.risk_engine import RiskScoringEngine

QUEUE_NAME = "simulation_events"


def process_event(body):

    event = json.loads(body)

    print("Received click event:", event)

    # Step 1: preprocessing
    pre = DataPreprocessor()
    sanitized = pre.sanitize(event)

    # Step 2: feature vector
    builder = FeatureVectorBuilder()
    features = builder.extract(sanitized)

    # Step 3: risk scoring
    engine = RiskScoringEngine()
    risk = engine.predict(features)

    print("Risk score:", risk)

    # TODO
    # later write to Neo4j and publish to Redis


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