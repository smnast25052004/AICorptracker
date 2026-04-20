"""
Fetcher Service — aggregates events from corporate systems and publishes to Kafka.

Runs as a standalone microservice with periodic polling.
"""

import time
import structlog

from shared.kafka_utils import create_producer, publish_event, TOPICS
from shared.database import engine
from shared.models import Base
from fetcher.sources.jira import JiraSource
from fetcher.sources.confluence import ConfluenceSource
from fetcher.sources.crm import CRMSource
from fetcher.sources.email_source import EmailSource

logger = structlog.get_logger()

POLL_INTERVAL_SECONDS = 60


def init_db():
    logger.info("Waiting for database schema (created by API service)...")
    for attempt in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(Base.metadata.tables["strategic_goals"].select().limit(0))
            logger.info("Database schema ready")
            return
        except Exception:
            logger.info("Schema not ready, retrying...", attempt=attempt + 1)
            time.sleep(2)
    logger.warning("Schema wait timed out, attempting create_all")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("create_all failed (likely already exists)", error=str(e))


def run_fetch_cycle(producer):
    sources = [
        JiraSource(),
        ConfluenceSource(),
        CRMSource(),
        EmailSource(),
    ]

    total_events = 0
    for source in sources:
        if not source.health_check():
            logger.warning("Source unavailable", source=source.source_name)
            continue

        logger.info("Fetching events", source=source.source_name)
        for event in source.fetch_events():
            event_dict = event.model_dump()

            topic = TOPICS["all_events"]
            if event.entity_type == "task":
                topic = TOPICS["task_events"]
            elif event.entity_type == "document":
                topic = TOPICS["document_events"]

            publish_event(producer, topic, event_dict)
            total_events += 1

    logger.info("Fetch cycle complete", total_events=total_events)


def main():
    logger.info("Starting Fetcher Service")
    init_db()

    producer = create_producer()
    logger.info("Kafka producer created")

    while True:
        try:
            run_fetch_cycle(producer)
        except Exception as e:
            logger.error("Fetch cycle failed", error=str(e))
        logger.info("Sleeping before next cycle", seconds=POLL_INTERVAL_SECONDS)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
