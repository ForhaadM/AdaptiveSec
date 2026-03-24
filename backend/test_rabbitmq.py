import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost")
)
channel = connection.channel()

channel.queue_declare(queue="simulation_events", durable=True)

print("RabbitMQ connected successfully")

connection.close()