"""Goals page — detailed view of strategic goals."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from dashboard.api_client import get_goals, get_goal_detail

st.header("Стратегические цели")

goals = get_goals()

if not goals:
    st.info("Цели не загружены. Запустите seed-скрипт.")
    st.stop()

status_colors = {"on_track": "#27ae60", "at_risk": "#f39c12", "critical": "#e74c3c", "completed": "#3498db"}
status_labels = {"on_track": "В норме", "at_risk": "Под угрозой", "critical": "Критический", "completed": "Завершён"}
status_emojis = {"on_track": "🟢", "at_risk": "🟡", "critical": "🔴", "completed": "🔵"}

fig = go.Figure()
for goal in goals:
    color = status_colors.get(goal["status"], "#95a5a6")
    fig.add_trace(go.Bar(
        x=[goal["risk_score"] * 100],
        y=[goal["title"][:40]],
        orientation="h",
        marker_color=color,
        text=[f"{goal['risk_score']:.0%}"],
        textposition="auto",
        name=status_labels.get(goal["status"], goal["status"]),
        showlegend=False,
    ))

fig.update_layout(
    title="Уровень риска по целям",
    xaxis_title="Риск (%)",
    height=max(300, len(goals) * 60),
    margin=dict(l=200),
    yaxis=dict(
        autorange="reversed",
        tickfont=dict(size=14, family="Arial"),  # размер шрифта меток
        title_font=dict(size=14)                 # если есть заголовок оси
    ),
    xaxis=dict(
        title_font=dict(size=16),
        tickfont=dict(size=14)
    ),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}

search_col, sort_col = st.columns([2, 1])
with search_col:
    search_query = st.text_input("Поиск по названию цели", placeholder="Введите часть названия...")
with sort_col:
    sort_option = st.selectbox(
        "Сортировка",
        ["Без сортировки", "По сроку (ближайшие сначала)", "По приоритету", "По риску (сначала высокий)"],
    )

filtered_goals = goals
if search_query:
    query = search_query.strip().lower()
    filtered_goals = [g for g in filtered_goals if query in (g.get("title") or "").lower()]

if sort_option == "По сроку (ближайшие сначала)":
    def _target_date_sort_key(goal: dict) -> tuple:
        target_date = pd.to_datetime(goal.get("target_date"), errors="coerce")
        return pd.isna(target_date), target_date
    
    filtered_goals = sorted(
        filtered_goals,
        key=_target_date_sort_key,
    )
elif sort_option == "По приоритету":
    filtered_goals = sorted(
        filtered_goals,
        key=lambda goal: priority_order.get((goal.get("priority") or "").lower(), 99),
    )
elif sort_option == "По риску (сначала высокий)":
    filtered_goals = sorted(
        filtered_goals,
        key=lambda goal: goal.get("risk_score", 0),
        reverse=True,
    )

st.markdown(
    """
    <style>
        /* Увеличиваем текст в шапке блока рекомендации */
        [data-testid="stExpander"] summary p {
            font-size: 16px !important;
        }
        .rec-meta {
            text-align: right;
            color: #9ca3af;
            font-size: 0.8rem;
            line-height: 1.35;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if not filtered_goals:
    st.info("По текущим фильтрам цели не найдены.")
    st.stop()

for goal in filtered_goals:
    emoji = status_emojis.get(goal["status"], "⚪")
    with st.expander(f"{emoji} {goal['title']} — Риск: {goal['risk_score']:.0%}"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Прогресс", f"{goal['progress']:.0f}%")
        with col2:
            st.metric("Проектов", goal.get("projects_count", 0))
        with col3:
            st.metric("Задач", goal.get("tasks_count", 0))
        with col4:
            st.metric("Приоритет", goal.get("priority", "").upper())

        if goal.get("description"):
            st.write(goal["description"])

        detail = get_goal_detail(str(goal["id"]))
        if detail and detail.get("projects"):
            st.write("**Проекты:**")
            for p in detail["projects"]:
                st.write(f"  - {p['title']} ({status_labels.get(p['status'], p['status'])})")

        if detail and detail.get("tasks"):
            st.write(f"**Задачи ({len(detail['tasks'])}):**")
            task_df = pd.DataFrame([
                {
                    "Задача": t["title"][:60],
                    "Статус": t["status"],
                    "Приоритет": t["priority"],
                    "Сводка": t.get("summary") or "Нет данных",
                }
                for t in detail["tasks"][:10]
            ])
            st.dataframe(task_df, use_container_width=True, hide_index=True)