"""HTTP client for Yougile REST API v2 with pagination."""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_BASE_URL = "https://yougile.com/api-v2"
PAGE_SIZE = 50
REQUEST_TIMEOUT = 30.0


class YougileAPIError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Yougile API {status_code}: {message}")


class YougileClient:
    """Reuses one HTTP connection for all requests (much faster than per-call clients)."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> YougileClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self._http.request(method, url, params=params)
        if response.status_code >= 400:
            detail = response.text[:500] if response.text else response.reason_phrase
            raise YougileAPIError(response.status_code, detail)
        return response.json()

    def get_all(self, resource: str, **query: Any) -> list[dict[str, Any]]:
        """Fetch all pages for a list endpoint (content + paging)."""
        items: list[dict[str, Any]] = []
        offset = 0
        while True:
            params = {**query, "limit": PAGE_SIZE, "offset": offset}
            data = self._request("GET", resource, params)
            items.extend(data.get("content") or [])
            paging = data.get("paging") or {}
            if not paging.get("next"):
                break
            offset += int(paging.get("limit") or PAGE_SIZE)
        return items

    def get_projects(self) -> list[dict[str, Any]]:
        return self.get_all("projects")

    def get_boards(self, project_id: str | None = None) -> list[dict[str, Any]]:
        params = {"projectId": project_id} if project_id else {}
        return self.get_all("boards", **params)

    def get_columns(self, board_id: str | None = None) -> list[dict[str, Any]]:
        params = {"boardId": board_id} if board_id else {}
        return self.get_all("columns", **params)

    def get_tasks(self, column_id: str | None = None) -> list[dict[str, Any]]:
        params = {"columnId": column_id} if column_id else {}
        return self.get_all("tasks", **params)

    def get_users(self) -> list[dict[str, Any]]:
        return self.get_all("users")

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._request("GET", f"tasks/{task_id}")
