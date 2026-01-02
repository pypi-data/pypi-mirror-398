import json
import logging
from confluent_kafka import Consumer
import os

def consume_message(topics_with_priority, group_id: str, as_json: bool = False, wait_time: float = 10.0, max_poll_attempts: int = 1):
    return consume_messages(
        topics_with_priority=topics_with_priority,
        group_id=group_id,
        as_json=as_json,
        wait_time=wait_time,
        max_messages=1,
        max_poll_attempts=max_poll_attempts
    )


def consume_messages(topics_with_priority, group_id: str, as_json: bool = False, wait_time: float = 10.0, max_messages: int = 1, max_poll_attempts: int = 5):
    if max_messages is None:
        raise ValueError("max_messages cannot be None to avoid infinite message consumption")

    logging.info("Consuming messages from topics...")
    consumer = Consumer({
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,  # Disable auto commit
        'auto.commit.interval.ms': 1000
    })
    
    # Sort topics by priority (assuming lower number means higher priority)
    sorted_topic_names = (
        [topics_with_priority] if isinstance(topics_with_priority, str)
        else [topic['name'] for topic in sorted(topics_with_priority, key=lambda x: x['priority'])]
    )

    consumed_messages = []
    consumed_message_count = 0

    for topic_name in sorted_topic_names:
        logging.info(f"Subscribing to topic: {topic_name}")
        consumer.subscribe([topic_name])

        current_poll_attempts = 0
        while consumed_message_count <= max_messages and current_poll_attempts < max_poll_attempts:
            logging.info(f"Polling messages from topic: {topic_name}")
            message = consumer.poll(timeout=wait_time)

            if message is None:
                logging.info(f"No messages found in topic: {topic_name}")
                current_poll_attempts += 1
                continue

            if message.error():
                logging.error(f"Consumer error: {message.error()}")
                current_poll_attempts += 1
                continue

            decoded_message = message.value().decode('utf-8')
            logging.info(f"Consumed message from topic: {message.topic()}")

            if as_json:
                try:
                    decoded_message = json.loads(decoded_message)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")
                    decoded_message = None

            consumed_messages.append(decoded_message)
            consumed_message_count += 1

            if consumed_message_count >= max_messages:
                break

        if consumed_message_count >= max_messages:
            break

    # Commit offsets once at the end
    logging.info("Committing offsets for all consumed messages")
    consumer.commit()
    consumer.close()
    logging.info(f"Consumed {consumed_message_count} messages.")
    return consumed_messages if max_messages > 1 else (consumed_messages[0] if consumed_messages else None)