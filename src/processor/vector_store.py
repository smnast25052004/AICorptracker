"""
Vector Store — PGVector-based semantic search engine.

Stores document/task embeddings and enables similarity search
for the AI knowledge base.
"""

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.database import get_db_session
from shared.models.document import Document
from processor.ai.embeddings import generate_embedding, cosine_similarity

logger = structlog.get_logger()


class VectorStore:

    def index_document(self, db: Session, doc_id: str, content: str) -> bool:
        embedding = generate_embedding(content)
        if embedding is None:
            return False

        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.embedding = embedding
            db.commit()
            logger.info("Document indexed", doc_id=doc_id)
            return True

        return False

    def search_similar(self, db: Session, query: str, limit: int = 5) -> list[dict]:
        query_embedding = generate_embedding(query)
        if query_embedding is None:
            return []

        try:
            results = db.execute(
                text("""
                    SELECT id, title, content, source_system,
                           embedding <=> CAST(:embedding AS vector) AS distance
                    FROM documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :limit
                """),
                {"embedding": str(query_embedding), "limit": limit},
            ).fetchall()

            return [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "content": (row.content or "")[:500],
                    "source_system": row.source_system,
                    "similarity": 1.0 - row.distance,
                }
                for row in results
            ]
        except Exception as e:
            logger.error("Vector search failed", error=str(e))
            return []

    def search_by_text(self, db: Session, query: str, limit: int = 5) -> list[dict]:
        """Fallback text search when vector search is not available."""
        try:
            results = (
                db.query(Document)
                .filter(Document.content.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "content": (doc.content or "")[:500],
                    "source_system": doc.source_system,
                    "similarity": 0.5,
                }
                for doc in results
            ]
        except Exception as e:
            logger.error("Text search failed", error=str(e))
            return []
