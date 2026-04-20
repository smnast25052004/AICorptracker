import json
import structlog
from confluent_kafka import Producer, Consumer, KafkaError
from shared.config import get_settings

logger = structlog.get_logger()

TOPICS = {
    "task_events": "corptracker.task_events",
    "document_events": "corptracker.document_events",
    "priority_events": "corptracker.priority_events",
    "risk_events": "corptracker.risk_events",
    "all_events": "corptracker.all_events",
}


def create_producer() -> Producer:
    settings = get_settings()
    return Producer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": "corptracker-producer",
            "acks": "all",
        }
    )


def create_consumer(group_id: str, topics: list[str] | None = None) -> Consumer:
    settings = get_settings()
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
    )
    if topics:
        consumer.subscribe(topics)
    return consumer


def publish_event(producer: Producer, topic: str, event: dict) -> None:
    try:
        producer.produce(
            topic,
            key=event.get("entity_id", ""),
            value=json.dumps(event, default=str),
            callback=_delivery_callback,
        )
        producer.flush(timeout=5)
    except Exception as e:
        logger.error("Failed to publish event", topic=topic, error=str(e))


def _delivery_callback(err, msg):
    if err:
        logger.error("Message delivery failed", error=str(err))
    else:
        logger.info("Message delivered", topic=msg.topic(), partition=msg.partition())
