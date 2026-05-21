"""Map Yougile API payloads to Corptracker DB fields (no schema changes)."""

from __future__ import annotations

import re
from typing import Any

from shared.models.task import TaskStatus

YOUGILE_GOAL_MARKER = "yougile:project_id="
SOURCE = "yougile"


def yougile_goal_description(project_id: str) -> str:
    return f"Импорт из Yougile. {YOUGILE_GOAL_MARKER}{project_id}"


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    plain = text
    plain = re.sub(r"<br\s*/?>", "\n", plain, flags=re.I)
    plain = re.sub(r"</p>", "\n", plain, flags=re.I)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    return plain.strip()


def column_to_status(column_title: str, *, completed: bool, archived: bool) -> TaskStatus:
    if archived or completed:
        return TaskStatus.DONE
    title = column_title.lower().strip()
    if "блок" in title:
        return TaskStatus.BLOCKED
    if "приём" in title or "прием" in title:
        return TaskStatus.IN_REVIEW
    if any(x in title for x in ("тест", "внедр", "разработ")):
        return TaskStatus.IN_PROGRESS
    if any(x in title for x in ("проект", "анализ", "описан")):
        return TaskStatus.TODO
    return TaskStatus.IN_PROGRESS


def task_external_id(task: dict[str, Any]) -> str:
    code = task.get("idTaskProject") or task.get("idTaskCommon")
    if code:
        return str(code)
    return f"YG-{task['id']}"


def build_task_description(
    task: dict[str, Any],
    *,
    extra_assignees: list[str] | None = None,
    parent_label: str | None = None,
) -> str | None:
    parts: list[str] = []
    body = strip_html(task.get("description"))
    if body:
        parts.append(body)
    if parent_label:
        parts.append(f"Подзадача родителя: {parent_label}")
    if extra_assignees:
        parts.append("Доп. исполнители: " + ", ".join(extra_assignees))
    if task.get("subtasks"):
        parts.append(f"Подзадач в Yougile: {len(task['subtasks'])}")
    return "\n\n".join(parts) if parts else None


def employee_display_name(user: dict[str, Any]) -> str:
    name = (user.get("realName") or "").strip()
    if name and "@" not in name:
        return name
    email = user.get("email") or ""
    local = email.split("@")[0] if email else "Сотрудник"
    return local.replace(".", " ").title()
