"""
AI Processor Service — consumes events from Kafka and runs AI analysis.

Processes corporate events through the AI pipeline:
1. Text analysis (signal extraction)
2. Entity matching (linking across systems)
3. Embedding generation (for vector search)
4. Stores processed data in PostgreSQL
"""
import json
import time
import structlog
from datetime import datetime, timezone

from shared.kafka_utils import create_consumer, TOPICS
from shared.database import get_db_session, engine
from shared.models import Base
from shared.models.event import Event, EventType as EventTypeModel
from shared.models.task import Task, TaskStatus, TaskPriority
from shared.models.document import Document, DocumentStatus, DocumentType
from processor.ai.text_analyzer import TextAnalyzer
from processor.ai.entity_matcher import EntityMatcher
from processor.ai.embeddings import generate_embedding

logger = structlog.get_logger()

text_analyzer = TextAnalyzer()
entity_matcher = EntityMatcher()


def init_db():
    logger.info("Waiting for database schema...")
    for attempt in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(Base.metadata.tables["strategic_goals"].select().limit(0))
            logger.info("Database schema ready")
            return
        except Exception:
            logger.info("Schema not ready, retrying...", attempt=attempt + 1)
            time.sleep(2)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("create_all failed", error=str(e))


def process_task_event(payload: dict) -> None:
    with get_db_session() as db:
        event_type_str = payload.get("event_type", "task_created")
        try:
            event_type_val = EventTypeModel(event_type_str)
        except ValueError:
            event_type_val = EventTypeModel.TASK_CREATED

        event = Event(
            event_type=event_type_val,
            source_system=payload.get("source_system", "unknown"),
            entity_type="task",
            entity_id=payload.get("entity_id", ""),
            payload=payload.get("payload", {}),
            processed="completed",
        )
        db.add(event)

        task_payload = payload.get("payload", {})
        title = task_payload.get("title", "")

        signals = text_analyzer.analyze(title)
        for signal in signals:
            logger.info(
                "Signal detected",
                signal_type=signal.signal_type,
                confidence=signal.confidence,
                task=title[:80],
            )

        goal_match = entity_matcher.match_project_to_goal(
            task_payload.get("project_key", "")
        )
        if goal_match:
            logger.info(
                "Entity matched",
                project=goal_match.source_entity,
                goal=goal_match.target_entity,
            )


def process_document_event(payload: dict) -> None:
    with get_db_session() as db:
        event_type_str = payload.get("event_type", "document_created")
        try:
            event_type_val = EventTypeModel(event_type_str)
        except ValueError:
            event_type_val = EventTypeModel.DOCUMENT_CREATED

        event = Event(
            event_type=event_type_val,
            source_system=payload.get("source_system", "unknown"),
            entity_type="document",
            entity_id=payload.get("entity_id", ""),
            payload=payload.get("payload", {}),
            processed="completed",
        )
        db.add(event)

        doc_payload = payload.get("payload", {})
        content = doc_payload.get("content_preview", doc_payload.get("title", ""))

        if content:
            signals = text_analyzer.analyze(content)
            for signal in signals:
                logger.info(
                    "Document signal",
                    signal_type=signal.signal_type,
                    confidence=signal.confidence,
                )

            goal_matches = entity_matcher.match_text_to_goal(content)
            for match in goal_matches[:1]:
                logger.info(
                    "Document matched to goal",
                    goal=match.target_entity,
                    confidence=match.confidence,
                )


def main():
    logger.info("Starting AI Processor Service")
    init_db()

    consumer = create_consumer(
        group_id="ai-processor",
        topics=[TOPICS["task_events"], TOPICS["document_events"], TOPICS["all_events"]],
    )
    logger.info("Kafka consumer created, waiting for events...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error", error=str(msg.error()))
                continue

            try:
                payload = json.loads(msg.value().decode("utf-8"))
                entity_type = payload.get("entity_type", "")

                if entity_type == "task":
                    process_task_event(payload)
                elif entity_type == "document":
                    process_document_event(payload)
                else:
                    logger.info("Unknown entity type", entity_type=entity_type)

            except json.JSONDecodeError:
                logger.error("Failed to parse message", raw=msg.value())
            except Exception as e:
                logger.error("Event processing failed", error=str(e))
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
