#!/usr/bin/env python3
"""
Read data from Yougile boards and write a human-readable snapshot to a txt file.

Usage:
  # из корня репозитория (рекомендуется):
  python3 -m yougilereader.fetch_board

  # из папки yougilereader:
  ./run.sh
  python3 fetch_board.py

Environment (yougilereader/.env or shell):
  YOUGILE_API_KEY   — required
  YOUGILE_BOARD_ID  — optional; if omitted, exports all boards
  YOUGILE_OUTPUT    — optional output path (default: yougilereader/output/board_snapshot.txt)
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _DIR.parent
_DEFAULT_OUTPUT = _DIR / "output" / "board_snapshot.txt"

# Запуск «python3 fetch_board.py» из yougilereader/ без -m
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(_REPO_ROOT))

from yougilereader.client import YougileAPIError, YougileClient


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _load_config() -> tuple[str, str | None, Path]:
    load_dotenv(_DIR / ".env")
    load_dotenv()
    api_key = os.environ.get("YOUGILE_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        print(
            "Ошибка: задайте YOUGILE_API_KEY в yougilereader/.env или в окружении.",
            file=sys.stderr,
        )
        sys.exit(1)
    if api_key in ("your_api_key_here", "changeme", "replace_me"):
        print(
            "Ошибка: в yougilereader/.env всё ещё стоит заглушка your_api_key_here.\n"
            "Вставьте реальный ключ из Yougile (Настройки компании → API).\n"
            "Если в ключе есть символ «+», возьмите значение в кавычки:\n"
            '  YOUGILE_API_KEY="ваш_ключ"',
            file=sys.stderr,
        )
        sys.exit(1)
    board_id = os.environ.get("YOUGILE_BOARD_ID", "").strip() or None
    output = Path(os.environ.get("YOUGILE_OUTPUT", str(_DEFAULT_OUTPUT)))
    return api_key, board_id, output


def _user_name(users_by_id: dict[str, dict], user_id: str) -> str:
    u = users_by_id.get(user_id, {})
    return u.get("realName") or u.get("email") or user_id


def _strip_html(text: str | None, max_len: int = 200) -> str:
    if not text:
        return ""
    plain = text.replace("<p>", "").replace("</p>", " ").replace("<br>", " ")
    for tag in ("<ul>", "</ul>", "<li>", "</li>", "<strong>", "</strong>"):
        plain = plain.replace(tag, " ")
    plain = " ".join(plain.split())
    if len(plain) > max_len:
        return plain[: max_len - 3] + "..."
    return plain


def build_snapshot(client: YougileClient, board_id: str | None) -> str:
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"Yougile snapshot — {now}")
    lines.append("=" * 60)

    _log("Загрузка пользователей…")
    users = client.get_users()
    users_by_id = {u["id"]: u for u in users}
    lines.append("")
    lines.append("Пользователи компании:")
    for u in users:
        role = "admin" if u.get("isAdmin") else "user"
        lines.append(f"  - {u.get('realName', '?')} <{u.get('email', '?')}> [{role}] id={u['id']}")

    _log("Загрузка проектов и досок…")
    projects = client.get_projects()
    projects_by_id = {p["id"]: p for p in projects}
    lines.append("")
    lines.append("Проекты:")
    for p in projects:
        lines.append(f"  - {p.get('title', '?')} id={p['id']}")

    boards = client.get_boards()
    if board_id:
        boards = [b for b in boards if b["id"] == board_id]
        if not boards:
            raise ValueError(f"Доска с id={board_id} не найдена")

    board_ids = {b["id"] for b in boards}

    _log("Загрузка колонок (один запрос)…")
    all_columns = client.get_columns()
    columns_by_board: dict[str, list[dict]] = defaultdict(list)
    for col in all_columns:
        if col.get("boardId") in board_ids:
            columns_by_board[col["boardId"]].append(col)

    _log("Загрузка задач (один проход по API)…")
    all_tasks = client.get_tasks()
    tasks_by_column: dict[str, list[dict]] = defaultdict(list)
    column_ids: set[str] = set()
    for col_list in columns_by_board.values():
        for col in col_list:
            column_ids.add(col["id"])
    for task in all_tasks:
        cid = task.get("columnId")
        if cid in column_ids:
            tasks_by_column[cid].append(task)

    lines.append("")
    lines.append(f"Досок к экспорту: {len(boards)}")
    lines.append("")

    for board in boards:
        bid = board["id"]
        project = projects_by_id.get(board.get("projectId", ""), {})
        lines.append("-" * 60)
        lines.append(f"Доска: {board.get('title', '?')}")
        lines.append(f"  board_id={bid}")
        lines.append(f"  project={project.get('title', '?')} ({board.get('projectId', '')})")

        columns = columns_by_board.get(bid, [])
        lines.append(f"  Колонок: {len(columns)}")
        lines.append("")

        for col in columns:
            cid = col["id"]
            tasks = tasks_by_column.get(cid, [])
            lines.append(f"  [{col.get('title', '?')}] (column_id={cid}) — задач: {len(tasks)}")
            for task in tasks:
                code = task.get("idTaskProject") or task.get("idTaskCommon") or task["id"]
                assignees = ", ".join(_user_name(users_by_id, uid) for uid in (task.get("assigned") or []))
                status = "done" if task.get("completed") else "open"
                if task.get("archived"):
                    status = "archived"
                desc = _strip_html(task.get("description"))
                line = f"    • [{code}] {task.get('title', '?')} [{status}]"
                if assignees:
                    line += f" → {assignees}"
                lines.append(line)
                if desc:
                    lines.append(f"      {desc}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    api_key, board_id, output_path = _load_config()
    base_url = os.environ.get("YOUGILE_API_BASE_URL", "").strip() or None

    try:
        with YougileClient(api_key, base_url=base_url) if base_url else YougileClient(api_key) as client:
            text = build_snapshot(client, board_id)
    except YougileAPIError as e:
        print(f"Ошибка API: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"Записано: {output_path} ({len(text)} байт)")


if __name__ == "__main__":
    main()
