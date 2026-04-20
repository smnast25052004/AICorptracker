"""Recommendations page — с фильтрами, сортировкой и отображением прогресса/дедлайна."""
import streamlit as st
import re
from dashboard.api_client import get_recommendations, get_goal_detail

# ---------- Функция для извлечения строк (для отображения) ----------
def extract_progress_deadline(summary_text: str | None) -> tuple[str, str]:
    """Возвращает (прогресс_строка, дни_до_дедлайна_строка)."""
    text = summary_text or ""
    progress_match = re.search(r"Прогресс:\s*([0-9]{1,3}%?)", text, re.IGNORECASE)
    deadline_match = re.search(r"дней до дедлайна:\s*([0-9]+)", text, re.IGNORECASE)
    progress = progress_match.group(1) if progress_match else "—"
    days_to_deadline = deadline_match.group(1) if deadline_match else "—"
    return progress, days_to_deadline

# ---------- Функции для извлечения чисел (для сортировки/фильтров) ----------
def extract_progress_num(description: str | None) -> int | None:
    if not description:
        return None
    match = re.search(r"Прогресс:\s*([0-9]{1,3})%?", description, re.IGNORECASE)
    return int(match.group(1)) if match else None

def extract_days_num(description: str | None) -> int | None:
    if not description:
        return None
    match = re.search(r"дней до дедлайна:\s*([0-9]+)", description, re.IGNORECASE)
    return int(match.group(1)) if match else None

def extract_risk_level(description: str | None) -> str | None:
    if not description:
        return None
    match = re.search(r"уровень риска\s+(\S+)", description, re.IGNORECASE)
    if match:
        risk_text = match.group(1).lower()
        if "высок" in risk_text:
            return "high"
        elif "средн" in risk_text:
            return "medium"
        elif "низк" in risk_text:
            return "low"
    return None

# ---------- Получение goal_id ----------
goal_id = st.session_state.get("selected_goal_id")

if not goal_id:
    st.warning("Цель не выбрана. Пожалуйста, вернитесь на страницу анализа рисков.")
    if st.button("Назад к целям"):
        st.switch_page("pages/risks.py")
    st.stop()

# ---------- Получение данных цели для карточки ----------
goal_detail = get_goal_detail(goal_id)
if not goal_detail or not goal_detail.get("goal"):
    st.error("Не удалось загрузить данные цели. Вернитесь на страницу рисков и попробуйте снова.")
    if st.button("Назад к целям"):
        st.switch_page("pages/risks.py")
    st.stop()

goal = goal_detail["goal"]
projects = goal_detail.get("projects", [])

# ---------- Заголовок и кнопка назад ----------
col_title, col_back = st.columns([4, 1])
with col_title:
    st.header("Рекомендации")
with col_back:
    if st.button("← Назад", use_container_width=True):
        st.switch_page("pages/risks.py")

# ---------- Карточка цели в expander (как на странице "Риски") ----------
status_emojis = {"on_track": "🟢", "at_risk": "🟡", "critical": "🔴", "completed": "🔵"}
status_labels = {"on_track": "В норме", "at_risk": "Под угрозой", "critical": "Критический", "completed": "Завершён"}

emoji = status_emojis.get(goal.get("status", "on_track"), "⚪")
risk_score = goal.get("risk_score", 0)

with st.expander(f"{emoji} {goal['title']} — Риск: {risk_score:.0%}", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Прогресс", f"{goal.get('progress', 0):.0f}%")
    with col2:
        st.metric("Проектов", len(projects))
    with col3:
        # Количество задач можно взять из goal_detail, если оно там есть, иначе посчитать
        tasks_count = goal_detail.get("tasks_count", sum(p.get("tasks_count", 0) for p in projects))
        st.metric("Задач", tasks_count)
    with col4:
        priority = goal.get("priority", "medium").upper()
        st.metric("Приоритет", priority)

    if goal.get("description"):
        st.write(goal["description"])

    if projects:
        st.write("**Проекты:**")
        for p in projects:
            st.write(f"  - {p['title']} ({status_labels.get(p.get('status', 'active'), p.get('status', 'active'))})")

st.markdown("---")

# ---------- Загрузка и фильтрация рекомендаций ----------
all_recs = get_recommendations()
recs = [rec for rec in all_recs if str(rec.get("goal_id")) == goal_id]

if not recs:
    st.info("Для этой цели нет рекомендаций.")
    st.stop()

# Обогащаем данными для сортировки и фильтров
for rec in recs:
    rec["_progress_num"] = extract_progress_num(rec.get("description"))
    rec["_days_num"] = extract_days_num(rec.get("description"))
    rec["_risk"] = extract_risk_level(rec.get("description")) or rec.get("risk")
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    rec["_priority_order"] = priority_order.get(rec.get("priority"), 3)

# Уникальные значения для фильтров
all_statuses = set(rec.get("status") for rec in recs if rec.get("status"))
all_risks = sorted(set(rec["_risk"] for rec in recs if rec["_risk"]))
risk_labels = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}

# Фильтры и сортировка
col_status, col_risk, col_sort = st.columns([2, 2, 2])

with col_status:
    st.write("**Статус**")
    status_options = {status: st.checkbox(status, key=f"status_{status}") for status in all_statuses}
    selected_statuses = [s for s, checked in status_options.items() if checked]

with col_risk:
    st.write("**Уровень риска**")
    risk_options = {risk: st.checkbox(risk_labels.get(risk, risk), key=f"risk_{risk}") for risk in all_risks}
    selected_risks = [r for r, checked in risk_options.items() if checked]

with col_sort:
    sort_by = st.selectbox(
        "Сортировка",
        options=["Приоритет (сначала высокий)", "Прогресс (сначала низкий)", "Срок до дедлайна (сначала ближайший)"],
        index=0
    )

# Применяем фильтры
filtered_recs = recs
if selected_statuses:
    filtered_recs = [r for r in filtered_recs if r.get("status") in selected_statuses]
if selected_risks:
    filtered_recs = [r for r in filtered_recs if r["_risk"] in selected_risks]

# Сортировка
if sort_by == "Приоритет (сначала высокий)":
    filtered_recs.sort(key=lambda r: r["_priority_order"])
elif sort_by == "Прогресс (сначала низкий)":
    filtered_recs.sort(key=lambda r: r["_progress_num"] if r["_progress_num"] is not None else 101)
elif sort_by == "Срок до дедлайна (сначала ближайший)":
    filtered_recs.sort(key=lambda r: r["_days_num"] if r["_days_num"] is not None else 9999)

if not filtered_recs:
    st.info("Нет рекомендаций, соответствующих выбранным фильтрам.")
    st.stop()

# ---------- Отображение карточек рекомендаций ----------
priority_emojis = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

for rec in filtered_recs:
    emoji = priority_emojis.get(rec.get("priority"), "⚪")
    with st.expander(f"{emoji} {rec.get('title', 'Без названия')[:100]}"):
        progress_str, days_str = extract_progress_deadline(rec.get("description"))
        st.write(f"**Цель:** {rec.get('goal_title', 'Не указана')}")
        if rec.get("action"):
            st.success(f"**Рекомендуемое действие:** {rec['action']}")
        st.write(f"**Статус:** {rec.get('status', 'active')}")
        st.write(f"**Категория:** {rec.get('category', 'Общая')}")
        st.write(f"**Прогресс:** {progress_str}")
        st.write(f"**Дней до дедлайна:** {days_str}")