"""Admin panel — CRUD management for all entities."""

import streamlit as st
import pandas as pd
from dashboard import api_client

st.header("🛠 Управление данными")

tab_goals, tab_projects, tab_tasks, tab_employees, tab_documents = st.tabs(
    ["🎯 Цели", "📁 Проекты", "✅ Задачи", "👤 Сотрудники", "📄 Документы"]
)

# ──────────────────────────── Goals ────────────────────────────

GOAL_STATUSES = ["on_track", "at_risk", "critical", "completed", "cancelled"]
GOAL_STATUS_LABELS = {
    "on_track": "В норме",
    "at_risk": "Под угрозой",
    "critical": "Критический",
    "completed": "Завершён",
    "cancelled": "Отменён",
}
GOAL_PRIORITIES = ["high", "medium", "low"]

with tab_goals:
    st.subheader("Стратегические цели")
    goals = api_client.get_goals()

    with st.expander("➕ Создать новую цель", expanded=False):
        with st.form("create_goal", clear_on_submit=True):
            g_title = st.text_input("Название *", key="g_title")
            g_desc = st.text_area("Описание", key="g_desc")
            g_col1, g_col2, g_col3 = st.columns(3)
            with g_col1:
                g_owner = st.text_input("Ответственный", key="g_owner")
            with g_col2:
                g_status = st.selectbox(
                    "Статус",
                    GOAL_STATUSES,
                    format_func=lambda x: GOAL_STATUS_LABELS.get(x, x),
                    key="g_status",
                )
            with g_col3:
                g_priority = st.selectbox(
                    "Приоритет", GOAL_PRIORITIES, index=1, key="g_priority"
                )
            g_col4, g_col5 = st.columns(2)
            with g_col4:
                g_progress = st.slider("Прогресс %", 0.0, 100.0, 0.0, key="g_progress")
            with g_col5:
                g_target = st.text_input("Целевая дата (ГГГГ-ММ-ДД)", key="g_target")

            if st.form_submit_button("Создать цель", type="primary"):
                if not g_title:
                    st.error("Название обязательно")
                else:
                    result = api_client.create_goal(
                        {
                            "title": g_title,
                            "description": g_desc or None,
                            "owner": g_owner or None,
                            "status": g_status,
                            "priority": g_priority,
                            "progress": g_progress,
                            "target_date": g_target or None,
                        }
                    )
                    if "error" in result:
                        st.error(f"Ошибка: {result['error']}")
                    else:
                        st.success(f"Цель «{g_title}» создана!")
                        st.rerun()

    if goals:
        for goal in goals:
            emoji = {
                "on_track": "🟢",
                "at_risk": "🟡",
                "critical": "🔴",
                "completed": "🔵",
            }.get(goal["status"], "⚪")
            with st.expander(f"{emoji} {goal['title']}"):
                with st.form(f"edit_goal_{goal['id']}"):
                    eg_title = st.text_input("Название", value=goal["title"])
                    eg_desc = st.text_area(
                        "Описание", value=goal.get("description") or ""
                    )
                    eg_c1, eg_c2, eg_c3 = st.columns(3)
                    with eg_c1:
                        eg_owner = st.text_input(
                            "Ответственный", value=goal.get("owner") or ""
                        )
                    with eg_c2:
                        eg_status = st.selectbox(
                            "Статус",
                            GOAL_STATUSES,
                            index=(
                                GOAL_STATUSES.index(goal["status"])
                                if goal["status"] in GOAL_STATUSES
                                else 0
                            ),
                            format_func=lambda x: GOAL_STATUS_LABELS.get(x, x),
                        )
                    with eg_c3:
                        eg_priority = st.selectbox(
                            "Приоритет",
                            GOAL_PRIORITIES,
                            index=(
                                GOAL_PRIORITIES.index(goal["priority"])
                                if goal["priority"] in GOAL_PRIORITIES
                                else 1
                            ),
                        )
                    eg_c4, eg_c5 = st.columns(2)
                    with eg_c4:
                        eg_progress = st.slider(
                            "Прогресс %", 0.0, 100.0, float(goal.get("progress", 0))
                        )
                    with eg_c5:
                        eg_target = st.text_input(
                            "Целевая дата", value=goal.get("target_date") or ""
                        )

                    btn_col1, btn_col2 = st.columns([1, 1])
                    with btn_col1:
                        save = st.form_submit_button("💾 Сохранить", type="primary")
                    with btn_col2:
                        remove = st.form_submit_button("🗑 Удалить", type="secondary")

                    if save:
                        result = api_client.update_goal(
                            str(goal["id"]),
                            {
                                "title": eg_title,
                                "description": eg_desc or None,
                                "owner": eg_owner or None,
                                "status": eg_status,
                                "priority": eg_priority,
                                "progress": eg_progress,
                                "target_date": eg_target or None,
                            },
                        )
                        if "error" in result:
                            st.error(f"Ошибка: {result['error']}")
                        else:
                            st.success("Цель обновлена!")
                            st.rerun()

                    if remove:
                        api_client.delete_goal(str(goal["id"]))
                        st.success("Цель удалена!")
                        st.rerun()
    else:
        st.info("Целей пока нет.")


# ──────────────────────────── Projects ────────────────────────────

PROJECT_STATUSES = ["active", "on_hold", "completed", "cancelled"]
PROJECT_STATUS_LABELS = {
    "active": "Активный",
    "on_hold": "Приостановлен",
    "completed": "Завершён",
    "cancelled": "Отменён",
}

with tab_projects:
    st.subheader("Проекты")
    projects = api_client.get_projects()

    goal_options = {str(g["id"]): g["title"] for g in goals} if goals else {}
    goal_ids = list(goal_options.keys())

    with st.expander("➕ Создать проект", expanded=False):
        with st.form("create_project", clear_on_submit=True):
            p_title = st.text_input("Название *", key="p_title")
            p_desc = st.text_area("Описание", key="p_desc")
            p_c1, p_c2, p_c3 = st.columns(3)
            with p_c1:
                p_lead = st.text_input("Руководитель", key="p_lead")
            with p_c2:
                p_status = st.selectbox(
                    "Статус",
                    PROJECT_STATUSES,
                    format_func=lambda x: PROJECT_STATUS_LABELS.get(x, x),
                    key="p_status",
                )
            with p_c3:
                p_goal = st.selectbox(
                    "Цель",
                    [""] + goal_ids,
                    format_func=lambda x: goal_options.get(x, "— Не выбрано —"),
                    key="p_goal",
                )
            p_progress = st.slider("Прогресс %", 0.0, 100.0, 0.0, key="p_progress")

            if st.form_submit_button("Создать проект", type="primary"):
                if not p_title:
                    st.error("Название обязательно")
                else:
                    result = api_client.create_project(
                        {
                            "title": p_title,
                            "description": p_desc or None,
                            "lead": p_lead or None,
                            "status": p_status,
                            "progress": p_progress,
                            "goal_id": p_goal or None,
                        }
                    )
                    if "error" in result:
                        st.error(f"Ошибка: {result['error']}")
                    else:
                        st.success(f"Проект «{p_title}» создан!")
                        st.rerun()

    if projects:
        for proj in projects:
            status_label = PROJECT_STATUS_LABELS.get(proj["status"], proj["status"])
            with st.expander(f"📁 {proj['title']} — {status_label}"):
                with st.form(f"edit_project_{proj['id']}"):
                    ep_title = st.text_input("Название", value=proj["title"])
                    ep_desc = st.text_area(
                        "Описание", value=proj.get("description") or ""
                    )
                    ep_c1, ep_c2, ep_c3 = st.columns(3)
                    with ep_c1:
                        ep_lead = st.text_input(
                            "Руководитель", value=proj.get("lead") or ""
                        )
                    with ep_c2:
                        ep_status = st.selectbox(
                            "Статус",
                            PROJECT_STATUSES,
                            index=(
                                PROJECT_STATUSES.index(proj["status"])
                                if proj["status"] in PROJECT_STATUSES
                                else 0
                            ),
                            format_func=lambda x: PROJECT_STATUS_LABELS.get(x, x),
                        )
                    with ep_c3:
                        current_goal = str(proj.get("goal_id") or "")
                        ep_goal = st.selectbox(
                            "Цель",
                            [""] + goal_ids,
                            index=(
                                (goal_ids.index(current_goal) + 1)
                                if current_goal in goal_ids
                                else 0
                            ),
                            format_func=lambda x: goal_options.get(x, "— Не выбрано —"),
                        )
                    ep_progress = st.slider(
                        "Прогресс %", 0.0, 100.0, float(proj.get("progress", 0))
                    )

                    btn1, btn2 = st.columns([1, 1])
                    with btn1:
                        save = st.form_submit_button("💾 Сохранить", type="primary")
                    with btn2:
                        remove = st.form_submit_button("🗑 Удалить", type="secondary")

                    if save:
                        result = api_client.update_project(
                            str(proj["id"]),
                            {
                                "title": ep_title,
                                "description": ep_desc or None,
                                "lead": ep_lead or None,
                                "status": ep_status,
                                "progress": ep_progress,
                                "goal_id": ep_goal or None,
                            },
                        )
                        if "error" in result:
                            st.error(f"Ошибка: {result['error']}")
                        else:
                            st.success("Проект обновлён!")
                            st.rerun()

                    if remove:
                        api_client.delete_project(str(proj["id"]))
                        st.success("Проект удалён!")
                        st.rerun()
    else:
        st.info("Проектов пока нет.")


# ──────────────────────────── Tasks ────────────────────────────

TASK_STATUSES = ["todo", "in_progress", "in_review", "done", "blocked"]
TASK_STATUS_LABELS = {
    "todo": "К выполнению",
    "in_progress": "В работе",
    "in_review": "На ревью",
    "done": "Выполнено",
    "blocked": "Заблокировано",
}
TASK_PRIORITIES = ["critical", "high", "medium", "low"]

with tab_tasks:
    st.subheader("Задачи")

    project_options = {str(p["id"]): p["title"] for p in projects} if projects else {}
    project_ids = list(project_options.keys())

    employees = api_client.get_employees()
    employee_options = (
        {str(e["id"]): e["full_name"] for e in employees} if employees else {}
    )
    employee_ids = list(employee_options.keys())

    tasks = api_client.get_tasks()

    with st.expander("➕ Создать задачу", expanded=False):
        with st.form("create_task", clear_on_submit=True):
            t_title = st.text_input("Название *", key="t_title")
            t_desc = st.text_area("Описание", key="t_desc")
            t_c1, t_c2 = st.columns(2)
            with t_c1:
                t_status = st.selectbox(
                    "Статус",
                    TASK_STATUSES,
                    format_func=lambda x: TASK_STATUS_LABELS.get(x, x),
                    key="t_status",
                )
            with t_c2:
                t_priority = st.selectbox(
                    "Приоритет", TASK_PRIORITIES, index=2, key="t_priority"
                )
            t_c3, t_c4 = st.columns(2)
            with t_c3:
                t_project = st.selectbox(
                    "Проект",
                    [""] + project_ids,
                    format_func=lambda x: project_options.get(x, "— Не выбран —"),
                    key="t_project",
                )
            with t_c4:
                t_assignee = st.selectbox(
                    "Исполнитель",
                    [""] + employee_ids,
                    format_func=lambda x: employee_options.get(x, "— Не выбран —"),
                    key="t_assignee",
                )
            t_c5, t_c6 = st.columns(2)
            with t_c5:
                t_sp = st.number_input("Story Points", min_value=0, value=0, key="t_sp")
            with t_c6:
                t_ext = st.text_input("Внешний ID", key="t_ext")

            if st.form_submit_button("Создать задачу", type="primary"):
                if not t_title:
                    st.error("Название обязательно")
                else:
                    result = api_client.create_task(
                        {
                            "title": t_title,
                            "description": t_desc or None,
                            "status": t_status,
                            "priority": t_priority,
                            "project_id": t_project or None,
                            "assignee_id": t_assignee or None,
                            "story_points": t_sp,
                            "external_id": t_ext or None,
                        }
                    )
                    if "error" in result:
                        st.error(f"Ошибка: {result['error']}")
                    else:
                        st.success(f"Задача «{t_title}» создана!")
                        st.rerun()

    if tasks:
        for task in tasks:
            t_emoji = {
                "done": "✅",
                "blocked": "🚫",
                "in_progress": "🔄",
                "in_review": "👀",
                "todo": "📋",
            }.get(task["status"], "📋")
            with st.expander(f"{t_emoji} {task['title']}"):
                with st.form(f"edit_task_{task['id']}"):
                    et_title = st.text_input("Название", value=task["title"])
                    et_desc = st.text_area(
                        "Описание", value=task.get("description") or ""
                    )
                    et_c1, et_c2 = st.columns(2)
                    with et_c1:
                        et_status = st.selectbox(
                            "Статус",
                            TASK_STATUSES,
                            index=(
                                TASK_STATUSES.index(task["status"])
                                if task["status"] in TASK_STATUSES
                                else 0
                            ),
                            format_func=lambda x: TASK_STATUS_LABELS.get(x, x),
                        )
                    with et_c2:
                        et_priority = st.selectbox(
                            "Приоритет",
                            TASK_PRIORITIES,
                            index=(
                                TASK_PRIORITIES.index(task["priority"])
                                if task["priority"] in TASK_PRIORITIES
                                else 2
                            ),
                        )
                    et_c3, et_c4 = st.columns(2)
                    with et_c3:
                        cur_proj = str(task.get("project_id") or "")
                        et_project = st.selectbox(
                            "Проект",
                            [""] + project_ids,
                            index=(
                                (project_ids.index(cur_proj) + 1)
                                if cur_proj in project_ids
                                else 0
                            ),
                            format_func=lambda x: project_options.get(
                                x, "— Не выбран —"
                            ),
                        )
                    with et_c4:
                        cur_assign = str(task.get("assignee_id") or "")
                        et_assignee = st.selectbox(
                            "Исполнитель",
                            [""] + employee_ids,
                            index=(
                                (employee_ids.index(cur_assign) + 1)
                                if cur_assign in employee_ids
                                else 0
                            ),
                            format_func=lambda x: employee_options.get(
                                x, "— Не выбран —"
                            ),
                        )
                    et_sp = st.number_input(
                        "Story Points", min_value=0, value=task.get("story_points", 0)
                    )

                    btn1, btn2 = st.columns([1, 1])
                    with btn1:
                        save = st.form_submit_button("💾 Сохранить", type="primary")
                    with btn2:
                        remove = st.form_submit_button("🗑 Удалить", type="secondary")

                    if save:
                        result = api_client.update_task(
                            str(task["id"]),
                            {
                                "title": et_title,
                                "description": et_desc or None,
                                "status": et_status,
                                "priority": et_priority,
                                "project_id": et_project or None,
                                "assignee_id": et_assignee or None,
                                "story_points": et_sp,
                            },
                        )
                        if "error" in result:
                            st.error(f"Ошибка: {result['error']}")
                        else:
                            st.success("Задача обновлена!")
                            st.rerun()

                    if remove:
                        api_client.delete_task(str(task["id"]))
                        st.success("Задача удалена!")
                        st.rerun()
    else:
        st.info("Задач пока нет.")


# ──────────────────────────── Employees ────────────────────────────

with tab_employees:
    st.subheader("Сотрудники")
    employees = api_client.get_employees()

    with st.expander("➕ Добавить сотрудника", expanded=False):
        with st.form("create_employee", clear_on_submit=True):
            e_name = st.text_input("ФИО *", key="e_name")
            e_email = st.text_input("Email *", key="e_email")
            e_c1, e_c2 = st.columns(2)
            with e_c1:
                e_dept = st.text_input("Отдел", key="e_dept")
            with e_c2:
                e_pos = st.text_input("Должность", key="e_pos")
            e_active = st.checkbox("Активен", value=True, key="e_active")

            if st.form_submit_button("Добавить сотрудника", type="primary"):
                if not e_name or not e_email:
                    st.error("ФИО и Email обязательны")
                else:
                    result = api_client.create_employee(
                        {
                            "full_name": e_name,
                            "email": e_email,
                            "department": e_dept or None,
                            "position": e_pos or None,
                            "is_active": e_active,
                        }
                    )
                    if "error" in result:
                        st.error(f"Ошибка: {result['error']}")
                    else:
                        st.success(f"Сотрудник «{e_name}» добавлен!")
                        st.rerun()

    if employees:
        for emp in employees:
            active_icon = "🟢" if emp.get("is_active") else "🔴"
            with st.expander(
                f"{active_icon} {emp['full_name']} — {emp.get('position', '')}"
            ):
                with st.form(f"edit_emp_{emp['id']}"):
                    ee_name = st.text_input("ФИО", value=emp["full_name"])
                    ee_email = st.text_input("Email", value=emp["email"])
                    ee_c1, ee_c2 = st.columns(2)
                    with ee_c1:
                        ee_dept = st.text_input(
                            "Отдел", value=emp.get("department") or ""
                        )
                    with ee_c2:
                        ee_pos = st.text_input(
                            "Должность", value=emp.get("position") or ""
                        )
                    ee_active = st.checkbox("Активен", value=emp.get("is_active", True))

                    btn1, btn2 = st.columns([1, 1])
                    with btn1:
                        save = st.form_submit_button("💾 Сохранить", type="primary")
                    with btn2:
                        remove = st.form_submit_button("🗑 Удалить", type="secondary")

                    if save:
                        result = api_client.update_employee(
                            str(emp["id"]),
                            {
                                "full_name": ee_name,
                                "email": ee_email,
                                "department": ee_dept or None,
                                "position": ee_pos or None,
                                "is_active": ee_active,
                            },
                        )
                        if "error" in result:
                            st.error(f"Ошибка: {result['error']}")
                        else:
                            st.success("Сотрудник обновлён!")
                            st.rerun()

                    if remove:
                        api_client.delete_employee(str(emp["id"]))
                        st.success("Сотрудник удалён!")
                        st.rerun()
    else:
        st.info("Сотрудников пока нет.")


# ──────────────────────────── Documents ────────────────────────────

DOC_TYPES = ["specification", "contract", "report", "confluence_page", "email", "other"]
DOC_TYPE_LABELS = {
    "specification": "Спецификация",
    "contract": "Контракт",
    "report": "Отчёт",
    "confluence_page": "Confluence",
    "email": "Письмо",
    "other": "Другое",
}
DOC_STATUSES = ["draft", "review", "approved", "rejected", "archived"]
DOC_STATUS_LABELS = {
    "draft": "Черновик",
    "review": "На проверке",
    "approved": "Утверждён",
    "rejected": "Отклонён",
    "archived": "Архив",
}

with tab_documents:
    st.subheader("Документы")
    documents = api_client.get_documents()

    with st.expander("📤 Загрузить файл", expanded=False):
        uploaded_file = st.file_uploader(
            "Выберите файл (txt, csv, md, json, xml, html, ...)",
            type=[
                "txt",
                "csv",
                "md",
                "json",
                "xml",
                "html",
                "log",
                "yml",
                "yaml",
                "py",
                "js",
                "sql",
            ],
            key="doc_upload",
        )
        with st.form("upload_doc", clear_on_submit=True):
            ud_title = st.text_input(
                "Название (по умолчанию — имя файла)", key="ud_title"
            )
            ud_c1, ud_c2 = st.columns(2)
            with ud_c1:
                ud_type = st.selectbox(
                    "Тип документа",
                    DOC_TYPES,
                    index=5,
                    format_func=lambda x: DOC_TYPE_LABELS.get(x, x),
                    key="ud_type",
                )
            with ud_c2:
                ud_author = st.text_input("Автор", key="ud_author")
            ud_project = st.selectbox(
                "Проект",
                [""] + project_ids,
                format_func=lambda x: project_options.get(x, "— Не выбран —"),
                key="ud_project",
            )

            if st.form_submit_button("📤 Загрузить", type="primary"):
                if not uploaded_file:
                    st.error("Выберите файл для загрузки")
                else:
                    file_bytes = uploaded_file.getvalue()
                    kwargs = {
                        "title": ud_title or uploaded_file.name,
                        "doc_type": ud_type,
                        "author": ud_author or "",
                    }
                    if ud_project:
                        kwargs["project_id"] = ud_project
                    result = api_client.upload_document(
                        file_bytes, uploaded_file.name, **kwargs
                    )
                    if "error" in result:
                        st.error(f"Ошибка: {result['error']}")
                    else:
                        st.success(f"Документ «{kwargs['title']}» загружен!")
                        st.rerun()

    with st.expander("➕ Создать документ вручную", expanded=False):
        with st.form("create_doc_manual", clear_on_submit=True):
            dm_title = st.text_input("Название *", key="dm_title")
            dm_content = st.text_area("Содержимое", height=200, key="dm_content")
            dm_c1, dm_c2, dm_c3 = st.columns(3)
            with dm_c1:
                dm_type = st.selectbox(
                    "Тип",
                    DOC_TYPES,
                    index=5,
                    format_func=lambda x: DOC_TYPE_LABELS.get(x, x),
                    key="dm_type",
                )
            with dm_c2:
                dm_status = st.selectbox(
                    "Статус",
                    DOC_STATUSES,
                    format_func=lambda x: DOC_STATUS_LABELS.get(x, x),
                    key="dm_status",
                )
            with dm_c3:
                dm_author = st.text_input("Автор", key="dm_author")
            dm_project = st.selectbox(
                "Проект",
                [""] + project_ids,
                format_func=lambda x: project_options.get(x, "— Не выбран —"),
                key="dm_project",
            )

            if st.form_submit_button("Создать документ", type="primary"):
                if not dm_title:
                    st.error("Название обязательно")
                else:
                    result = api_client.create_document(
                        {
                            "title": dm_title,
                            "content": dm_content or None,
                            "doc_type": dm_type,
                            "status": dm_status,
                            "author": dm_author or None,
                            "project_id": dm_project or None,
                        }
                    )
                    if "error" in result:
                        st.error(f"Ошибка: {result['error']}")
                    else:
                        st.success(f"Документ «{dm_title}» создан!")
                        st.rerun()

    if documents:
        for doc in documents:
            doc_emoji = {
                "approved": "✅",
                "rejected": "❌",
                "draft": "📝",
                "review": "👀",
                "archived": "📦",
            }.get(doc["status"], "📄")
            type_label = DOC_TYPE_LABELS.get(
                doc.get("doc_type", ""), doc.get("doc_type", "")
            )
            with st.expander(f"{doc_emoji} {doc['title']} — {type_label}"):
                with st.form(f"edit_doc_{doc['id']}"):
                    ed_title = st.text_input("Название", value=doc["title"])
                    ed_content = st.text_area(
                        "Содержимое", value=doc.get("content") or "", height=150
                    )
                    ed_c1, ed_c2, ed_c3 = st.columns(3)
                    with ed_c1:
                        ed_type = st.selectbox(
                            "Тип",
                            DOC_TYPES,
                            index=(
                                DOC_TYPES.index(doc["doc_type"])
                                if doc.get("doc_type") in DOC_TYPES
                                else 5
                            ),
                            format_func=lambda x: DOC_TYPE_LABELS.get(x, x),
                        )
                    with ed_c2:
                        ed_status = st.selectbox(
                            "Статус",
                            DOC_STATUSES,
                            index=(
                                DOC_STATUSES.index(doc["status"])
                                if doc.get("status") in DOC_STATUSES
                                else 0
                            ),
                            format_func=lambda x: DOC_STATUS_LABELS.get(x, x),
                        )
                    with ed_c3:
                        ed_author = st.text_input(
                            "Автор", value=doc.get("author") or ""
                        )
                    cur_doc_proj = str(doc.get("project_id") or "")
                    ed_project = st.selectbox(
                        "Проект",
                        [""] + project_ids,
                        index=(
                            (project_ids.index(cur_doc_proj) + 1)
                            if cur_doc_proj in project_ids
                            else 0
                        ),
                        format_func=lambda x: project_options.get(x, "— Не выбран —"),
                    )

                    btn1, btn2 = st.columns([1, 1])
                    with btn1:
                        save = st.form_submit_button("💾 Сохранить", type="primary")
                    with btn2:
                        remove = st.form_submit_button("🗑 Удалить", type="secondary")

                    if save:
                        result = api_client.update_document(
                            str(doc["id"]),
                            {
                                "title": ed_title,
                                "content": ed_content or None,
                                "doc_type": ed_type,
                                "status": ed_status,
                                "author": ed_author or None,
                                "project_id": ed_project or None,
                            },
                        )
                        if "error" in result:
                            st.error(f"Ошибка: {result['error']}")
                        else:
                            st.success("Документ обновлён!")
                            st.rerun()

                    if remove:
                        api_client.delete_document(str(doc["id"]))
                        st.success("Документ удалён!")
                        st.rerun()
    else:
        st.info("Документов пока нет.")
