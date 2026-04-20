"""
CorpTracker API — REST API for the strategic monitoring system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.database import engine
from shared.models import Base
from api.routes.goals import router as goals_router
from api.routes.risks import router as risks_router
from api.routes.dashboard import router as dashboard_router
from api.routes.search import router as search_router
from api.routes.analysis import router as analysis_router
from api.routes.employees import router as employees_router
from api.routes.projects import router as projects_router
from api.routes.tasks import router as tasks_router
from api.routes.documents import router as documents_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI CorpTracker",
    description="AI-powered strategic goal monitoring system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(goals_router, prefix="/api/goals", tags=["Goals"])
app.include_router(risks_router, prefix="/api/risks", tags=["Risks"])
app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(employees_router, prefix="/api/employees", tags=["Employees"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "corptracker-api"}
