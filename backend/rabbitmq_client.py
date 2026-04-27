import pika

RABBITMQ_HOST = "localhost"
QUEUE_NAME = "simulation_events"

def get_channel():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    return connection, channel

def publish_event(payload: dict):
    import json
    connection, channel = get_channel()
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)  # persistent message
    )
    connection.close()