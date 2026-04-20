from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from shared.database import get_db
from processor.vector_store import VectorStore

router = APIRouter()
vector_store = VectorStore()


@router.get("/semantic")
def semantic_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    results = vector_store.search_similar(db, q, limit=limit)
    if not results:
        results = vector_store.search_by_text(db, q, limit=limit)

    return {"query": q, "results": results, "count": len(results)}
