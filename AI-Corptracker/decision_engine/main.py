"""
Decision Engine Service — runs periodic analysis of strategic goals.

Orchestrates the full analysis pipeline:
1. Aggregates data from DB
2. Runs risk prediction
3. Generates recommendations
4. Creates notifications
"""
import time
import structlog

from shared.database import get_db_session, engine
from shared.models import Base
from decision_engine.engine import run_full_analysis
from decision_engine.notifications import generate_notifications

logger = structlog.get_logger()

ANALYSIS_INTERVAL_SECONDS = 120


def wait_for_schema():
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


def main():
    logger.info("Starting Decision Engine Service")
    wait_for_schema()

    while True:
        try:
            with get_db_session() as db:
                results = run_full_analysis(db)
                logger.info("Analysis complete", goals_analyzed=len(results))

                for r in results:
                    logger.info(
                        "Goal status",
                        goal=r["goal"][:50],
                        risk_score=f"{r['risk_score']:.0%}",
                        risk_level=r["risk_level"],
                    )

                notifications = generate_notifications(db)
                for notif in notifications:
                    logger.warning(
                        "NOTIFICATION",
                        level=notif.level,
                        title=notif.title,
                        action=notif.action_required,
                    )
        except Exception as e:
            logger.error("Analysis cycle failed", error=str(e))

        logger.info("Sleeping before next analysis", seconds=ANALYSIS_INTERVAL_SECONDS)
        time.sleep(ANALYSIS_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
