#!/usr/bin/env python3
"""
Import Yougile boards into Corptracker PostgreSQL (existing schema only).

Creates separate strategic goals + projects (not linked to Excel seed data).
Upserts employees, goals, projects, tasks. Subtasks become separate tasks.

Usage (repo root):
  python3 -m yougilereader.import_to_db

From yougilereader/:
  python3 import_to_db.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _DIR.parent

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy.orm import Session

from shared.database import get_db_session
from shared.models.employee import Employee
from shared.models.goal import GoalPriority, GoalStatus, StrategicGoal
from shared.models.project import Project, ProjectStatus
from shared.models.task import Task, TaskPriority, TaskStatus
from yougilereader.client import YougileAPIError, YougileClient
from yougilereader.transform import (
    SOURCE,
    YOUGILE_GOAL_MARKER,
    build_task_description,
    column_to_status,
    employee_display_name,
    task_external_id,
    yougile_goal_description,
)

load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_DIR / ".env")


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _load_api_key() -> tuple[str, str | None, str | None]:
    api_key = os.environ.get("YOUGILE_API_KEY", "").strip().strip('"').strip("'")
    if not api_key or api_key == "your_api_key_here":
        print("Ошибка: задайте YOUGILE_API_KEY в yougilereader/.env", file=sys.stderr)
        sys.exit(1)
    board_id = os.environ.get("YOUGILE_BOARD_ID", "").strip() or None
    base_url = os.environ.get("YOUGILE_API_BASE_URL", "").strip() or None
    return api_key, board_id, base_url


def _find_goal_for_yougile_project(db: Session, project_id: str) -> StrategicGoal | None:
    marker = f"{YOUGILE_GOAL_MARKER}{project_id}"
    return db.query(StrategicGoal).filter(StrategicGoal.description.contains(marker)).first()


def _expand_tasks_with_subtasks(
    tasks: list[dict[str, Any]],
    client: YougileClient,
) -> list[tuple[dict[str, Any], dict[str, Any] | None]]:
    """Return (task, parent_or_none) for import; subtasks fetched if missing."""
    by_id = {t["id"]: t for t in tasks}
    missing: set[str] = set()
    for t in tasks:
        for sid in t.get("subtasks") or []:
            if sid not in by_id:
                missing.add(sid)

    for sid in missing:
        try:
            by_id[sid] = client.get_task(sid)
        except YougileAPIError as e:
            _log(f"  предупреждение: подзадача {sid} не загружена: {e}")

    result: list[tuple[dict[str, Any], dict[str, Any] | None]] = []
    seen: set[str] = set()

    for t in tasks:
        if t["id"] not in seen:
            seen.add(t["id"])
            result.append((t, None))
        plabel = task_external_id(t)
        for sid in t.get("subtasks") or []:
            sub = by_id.get(sid)
            if sub and sub["id"] not in seen:
                seen.add(sub["id"])
                sub_copy = dict(sub)
                sub_copy["_parent_label"] = plabel
                result.append((sub_copy, t))
    return result


def _upsert_employees(db: Session, users: list[dict[str, Any]]) -> dict[str, Employee]:
    by_yougile_id: dict[str, Employee] = {}
    for u in users:
        email = (u.get("email") or "").strip().lower()
        if not email:
            continue
        emp = db.query(Employee).filter(Employee.email == email).first()
        name = employee_display_name(u)
        if emp:
            emp.full_name = name
            emp.is_active = True
        else:
            emp = Employee(
                full_name=name,
                email=email,
                department="Yougile",
                position="Участник доски",
                is_active=True,
            )
            db.add(emp)
        by_yougile_id[u["id"]] = emp
    db.flush()
    return by_yougile_id


def _upsert_goal_and_project(
    db: Session,
    yg_project: dict[str, Any],
    users_by_id: dict[str, Employee],
) -> Project:
    pid = yg_project["id"]
    title = yg_project.get("title") or "Yougile проект"
    marker_desc = yougile_goal_description(pid)

    goal = _find_goal_for_yougile_project(db, pid)
    if not goal:
        admin_ids = [uid for uid, role in (yg_project.get("users") or {}).items() if role == "admin"]
        owner_name = "Yougile"
        for uid in admin_ids:
            emp = users_by_id.get(uid)
            if emp:
                owner_name = emp.full_name
                break

        goal = StrategicGoal(
            title=f"[Yougile] {title}",
            description=marker_desc,
            owner=owner_name,
            status=GoalStatus.ON_TRACK,
            priority=GoalPriority.MEDIUM,
            progress=0.0,
            risk_score=0.0,
            target_date=None,
        )
        db.add(goal)
        db.flush()
    else:
        goal.title = f"[Yougile] {title}"

    project = db.query(Project).filter(Project.goal_id == goal.id).first()
    lead = goal.owner
    if not project:
        project = Project(
            title=title,
            description=marker_desc,
            status=ProjectStatus.ACTIVE,
            progress=0.0,
            lead=lead,
            goal_id=goal.id,
        )
        db.add(project)
    else:
        project.title = title
        project.description = marker_desc
        project.lead = lead
        project.status = ProjectStatus.ACTIVE
    db.flush()
    return project


def _resolve_assignee(
    task: dict[str, Any],
    users_by_id: dict[str, Employee],
    yg_users: list[dict[str, Any]],
) -> tuple[Employee | None, list[str]]:
    assigned_ids = task.get("assigned") or []
    names: list[str] = []
    for uid in assigned_ids:
        emp = users_by_id.get(uid)
        if emp:
            names.append(emp.full_name)
        else:
            for u in yg_users:
                if u["id"] == uid:
                    names.append(employee_display_name(u))
                    break

    primary = users_by_id.get(assigned_ids[0]) if assigned_ids else None
    extra = names[1:] if len(names) > 1 else []
    return primary, extra


def _upsert_task(
    db: Session,
    task: dict[str, Any],
    *,
    project: Project,
    column_title: str,
    users_by_id: dict[str, Employee],
    yg_users: list[dict[str, Any]],
    parent_label: str | None,
) -> tuple[Task, bool]:
    """Returns (task_row, created)."""
    ext_id = task_external_id(task)
    row = (
        db.query(Task)
        .filter(Task.external_id == ext_id, Task.source_system == SOURCE)
        .first()
    )
    created = row is None

    primary, extra = _resolve_assignee(task, users_by_id, yg_users)
    description = build_task_description(
        task,
        extra_assignees=extra,
        parent_label=parent_label or task.get("_parent_label"),
    )

    status = column_to_status(
        column_title,
        completed=bool(task.get("completed")),
        archived=bool(task.get("archived")),
    )

    fields = {
        "title": (task.get("title") or "Без названия")[:500],
        "description": description,
        "status": status,
        "priority": TaskPriority.MEDIUM,
        "source_system": SOURCE,
        "story_points": 0,
        "assignee_id": primary.id if primary else None,
        "project_id": project.id,
    }

    if row:
        for k, v in fields.items():
            setattr(row, k, v)
        return row, False

    row = Task(external_id=ext_id, **fields)
    db.add(row)
    return row, True


def _update_progress(db: Session, project: Project, goal: StrategicGoal) -> None:
    tasks = db.query(Task).filter(Task.project_id == project.id, Task.source_system == SOURCE).all()
    if not tasks:
        return
    done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
    progress = round(100.0 * done / len(tasks), 1)
    project.progress = progress
    goal.progress = progress
    if progress >= 100:
        project.status = ProjectStatus.COMPLETED
        goal.status = GoalStatus.COMPLETED
    elif progress >= 50:
        goal.status = GoalStatus.ON_TRACK
    else:
        goal.status = GoalStatus.AT_RISK


def run_import() -> None:
    api_key, board_filter, base_url = _load_api_key()

    with YougileClient(api_key, base_url=base_url) if base_url else YougileClient(api_key) as client:
        _log("Загрузка данных из Yougile…")
        users = client.get_users()
        yg_projects = client.get_projects()
        boards = client.get_boards()
        columns = client.get_columns()
        all_tasks = client.get_tasks()

        if board_filter:
            boards = [b for b in boards if b["id"] == board_filter]
            if not boards:
                raise ValueError(f"Доска {board_filter} не найдена")
            allowed_project_ids = {b["projectId"] for b in boards}
            yg_projects = [p for p in yg_projects if p["id"] in allowed_project_ids]

        board_ids = {b["id"] for b in boards}
        column_by_id = {c["id"]: c for c in columns if c.get("boardId") in board_ids}
        column_ids = set(column_by_id)

        board_to_project = {b["id"]: b["projectId"] for b in boards}
        column_to_project: dict[str, str] = {}
        for cid, col in column_by_id.items():
            bid = col.get("boardId")
            if bid and bid in board_to_project:
                column_to_project[cid] = board_to_project[bid]

        board_tasks = [t for t in all_tasks if t.get("columnId") in column_ids]
        import_rows = _expand_tasks_with_subtasks(board_tasks, client)

        _log(
            f"Проектов: {len(yg_projects)}, колонок: {len(column_by_id)}, "
            f"задач к импорту: {len(import_rows)}"
        )

        stats = {"employees": 0, "goals": 0, "projects": 0, "tasks": 0, "tasks_updated": 0}

        with get_db_session() as db:
            employees = _upsert_employees(db, users)
            stats["employees"] = len(employees)

            projects_by_yg: dict[str, Project] = {}
            goals_by_yg: dict[str, StrategicGoal] = {}

            for yp in yg_projects:
                existed = _find_goal_for_yougile_project(db, yp["id"]) is not None
                proj = _upsert_goal_and_project(db, yp, employees)
                projects_by_yg[yp["id"]] = proj
                goal = db.query(StrategicGoal).filter(StrategicGoal.id == proj.goal_id).one()
                goals_by_yg[yp["id"]] = goal
                if not existed:
                    stats["goals"] += 1
                stats["projects"] += 1
                _log(f"  проект: {proj.title}")

            for task, parent in import_rows:
                cid = task.get("columnId") or (parent.get("columnId") if parent else None)
                if not cid or cid not in column_by_id:
                    if parent and parent.get("columnId") in column_by_id:
                        cid = parent["columnId"]
                    else:
                        _log(f"  пропуск задачи без колонки: {task_external_id(task)}")
                        continue

                yg_pid = column_to_project.get(cid)
                if not yg_pid or yg_pid not in projects_by_yg:
                    continue

                col_title = column_by_id[cid].get("title") or ""
                parent_label = None
                if parent:
                    parent_label = task_external_id(parent)
                elif task.get("_parent_label"):
                    parent_label = task["_parent_label"]

                _, created = _upsert_task(
                    db,
                    task,
                    project=projects_by_yg[yg_pid],
                    column_title=col_title,
                    users_by_id=employees,
                    yg_users=users,
                    parent_label=parent_label,
                )
                if created:
                    stats["tasks"] += 1
                else:
                    stats["tasks_updated"] += 1

            for yg_pid, proj in projects_by_yg.items():
                goal = goals_by_yg[yg_pid]
                _update_progress(db, proj, goal)

        print("Импорт завершён:")
        print(f"  сотрудников (Yougile): {stats['employees']}")
        print(f"  целей [Yougile]:       {stats['goals']}")
        print(f"  проектов:              {stats['projects']}")
        print(f"  задач создано:         {stats['tasks']}")
        print(f"  задач обновлено:       {stats['tasks_updated']}")


def main() -> None:
    try:
        run_import()
    except YougileAPIError as e:
        print(f"Ошибка API: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка БД: {e}", file=sys.stderr)
        print("Проверьте POSTGRES_* в .env и что PostgreSQL запущен.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
