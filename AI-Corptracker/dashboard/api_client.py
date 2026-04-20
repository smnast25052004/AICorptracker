"""HTTP client for the CorpTracker API."""
import httpx
import os
API_BASE = os.getenv("API_BASE_URL", "http://api:8000")

_TIMEOUT = 15.0


def _get(endpoint: str, params: dict | None = None) -> dict | list:
    try:
        resp = httpx.get(f"{API_BASE}{endpoint}", params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def _post(endpoint: str, json: dict | None = None) -> dict:
    try:
        resp = httpx.post(f"{API_BASE}{endpoint}", json=json, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}


def _put(endpoint: str, json: dict | None = None) -> dict:
    try:
        resp = httpx.put(f"{API_BASE}{endpoint}", json=json, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}


def _delete(endpoint: str) -> dict:
    try:
        resp = httpx.delete(f"{API_BASE}{endpoint}", timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}


def _post_file(endpoint: str, file_bytes: bytes, filename: str, data: dict | None = None) -> dict:
    try:
        files = {"file": (filename, file_bytes)}
        resp = httpx.post(f"{API_BASE}{endpoint}", files=files, data=data or {}, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}


# --------------- Dashboard ---------------

def get_dashboard_summary() -> dict:
    return _get("/api/dashboard/summary")


def get_notifications() -> dict:
    return _get("/api/analysis/notifications")


def trigger_analysis() -> dict:
    return _post("/api/analysis/run")


def semantic_search(query: str, limit: int = 5) -> dict:
    return _get("/api/search/semantic", params={"q": query, "limit": limit})


# --------------- Goals ---------------

def get_goals() -> list:
    return _get("/api/goals/") or []


def get_goal_detail(goal_id: str) -> dict:
    return _get(f"/api/goals/{goal_id}")


def create_goal(data: dict) -> dict:
    return _post("/api/goals/", json=data)


def update_goal(goal_id: str, data: dict) -> dict:
    return _put(f"/api/goals/{goal_id}", json=data)


def delete_goal(goal_id: str) -> dict:
    return _delete(f"/api/goals/{goal_id}")


# --------------- Projects ---------------

def get_projects(goal_id: str | None = None) -> list:
    params = {"goal_id": goal_id} if goal_id else None
    return _get("/api/projects/", params=params) or []


def create_project(data: dict) -> dict:
    return _post("/api/projects/", json=data)


def update_project(project_id: str, data: dict) -> dict:
    return _put(f"/api/projects/{project_id}", json=data)


def delete_project(project_id: str) -> dict:
    return _delete(f"/api/projects/{project_id}")


# --------------- Tasks ---------------

def get_tasks(project_id: str | None = None) -> list:
    params = {"project_id": project_id} if project_id else None
    return _get("/api/tasks/", params=params) or []


def create_task(data: dict) -> dict:
    return _post("/api/tasks/", json=data)


def update_task(task_id: str, data: dict) -> dict:
    return _put(f"/api/tasks/{task_id}", json=data)


def delete_task(task_id: str) -> dict:
    return _delete(f"/api/tasks/{task_id}")


# --------------- Employees ---------------

def get_employees() -> list:
    return _get("/api/employees/") or []


def create_employee(data: dict) -> dict:
    return _post("/api/employees/", json=data)


def update_employee(employee_id: str, data: dict) -> dict:
    return _put(f"/api/employees/{employee_id}", json=data)


def delete_employee(employee_id: str) -> dict:
    return _delete(f"/api/employees/{employee_id}")


# --------------- Documents ---------------

def get_documents(project_id: str | None = None) -> list:
    params = {"project_id": project_id} if project_id else None
    return _get("/api/documents/", params=params) or []


def create_document(data: dict) -> dict:
    return _post("/api/documents/", json=data)


def upload_document(file_bytes: bytes, filename: str, **kwargs) -> dict:
    return _post_file("/api/documents/upload", file_bytes, filename, data=kwargs)


def update_document(document_id: str, data: dict) -> dict:
    return _put(f"/api/documents/{document_id}", json=data)


def delete_document(document_id: str) -> dict:
    return _delete(f"/api/documents/{document_id}")


# --------------- Risks ---------------

def get_risks() -> list:
    return _get("/api/risks/") or []


def get_recommendations(goal_id: str | None = None) -> list:
    params = {"goal_id": goal_id} if goal_id else None
    return _get("/api/risks/recommendations", params=params) or []