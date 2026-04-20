#!/usr/bin/env python3
"""
Fix Grafana dashboard rawSql: PostgreSQL enum labels are UPPERCASE in the DB
(goalstatus, taskstatus, taskpriority, documentstatus, documenttype, recommendation*).

risk_assessments.risk_level is VARCHAR with lowercase values — preserve CASE ra.risk_level ... blocks.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RISK_PLACEHOLDER = "<<<__RISK_LEVEL_CASE__>>>"

# Order: longer substrings first
REPLACEMENTS: list[tuple[str, str]] = [
    ("'confluence_page'", "'CONFLUENCE_PAGE'"),
    ("'in_progress'", "'IN_PROGRESS'"),
    ("'in_review'", "'IN_REVIEW'"),
    ("'on_track'", "'ON_TRACK'"),
    ("'at_risk'", "'AT_RISK'"),
    ("'completed'", "'COMPLETED'"),
    ("'blocked'", "'BLOCKED'"),
    ("'todo'", "'TODO'"),
    ("'done'", "'DONE'"),
    ("'draft'", "'DRAFT'"),
    ("'review'", "'REVIEW'"),
    ("'approved'", "'APPROVED'"),
    ("'rejected'", "'REJECTED'"),
    ("'specification'", "'SPECIFICATION'"),
    ("'contract'", "'CONTRACT'"),
    ("'report'", "'REPORT'"),
    ("'urgent'", "'URGENT'"),
    ("'active'", "'ACTIVE'"),
    ("'critical'", "'CRITICAL'"),
    ("'high'", "'HIGH'"),
    ("'medium'", "'MEDIUM'"),
    ("'low'", "'LOW'"),
]


def strip_risk_case(sql: str) -> tuple[str, str | None]:
    """Temporarily remove CASE ra.risk_level ... END so global enum fix does not break varchar labels."""
    m = re.search(r"(CASE\s+ra\.risk_level\s+WHEN.+?END)(\s+AS\s+)", sql, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        return sql, None
    inner = m.group(1)
    new_sql = sql[: m.start()] + RISK_PLACEHOLDER + m.group(2) + sql[m.end() :]
    return new_sql, inner


def apply_enum_fixes(sql: str) -> str:
    for old, new in REPLACEMENTS:
        sql = sql.replace(old, new)
    return sql


def fix_raw_sql(sql: str) -> str:
    sql, risk = strip_risk_case(sql)
    sql = apply_enum_fixes(sql)
    if risk is not None:
        sql = sql.replace(RISK_PLACEHOLDER, risk, 1)
    return sql


def walk(obj):
    if isinstance(obj, dict):
        if "rawSql" in obj and isinstance(obj["rawSql"], str):
            obj["rawSql"] = fix_raw_sql(obj["rawSql"])
        for v in obj.values():
            walk(v)
    elif isinstance(obj, list):
        for item in obj:
            walk(item)


def main():
    root = Path(__file__).parent / "dashboards"
    for path in sorted(root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        walk(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK {path.name}")


if __name__ == "__main__":
    main()
