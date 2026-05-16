"""Dashboard Overview — main page for CEO."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from dashboard.api_client import (
    get_dashboard_summary,
    get_notifications,
    get_risks,
    trigger_analysis,
)

col_action, _ = st.columns([1, 3])
with col_action:
    if st.button("Запустить анализ", type="primary"):
        with st.spinner("Анализ целей..."):
            result = trigger_analysis()
            if "error" not in result:
                st.success(f"Проанализировано целей: {result.get('goals_analyzed', 0)}")
            else:
                st.error("Ошибка анализа")

summary = get_dashboard_summary()

if not summary or not summary.get("total_goals"):
    st.info(
        "Данные отсутствуют. Запустите seed-скрипт для заполнения базы и нажмите «Запустить анализ»."
    )
    st.code("docker compose exec api python -m seed.seed_data", language="bash")
    st.stop()

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Всего целей", summary.get("total_goals", 0))
with col2:
    st.metric(
        "В норме", summary.get("goals_on_track", 0), delta="✓", delta_color="normal"
    )
with col3:
    st.metric(
        "Под угрозой", summary.get("goals_at_risk", 0), delta="!", delta_color="inverse"
    )
with col4:
    st.metric(
        "Критические",
        summary.get("goals_critical", 0),
        delta="!!!",
        delta_color="inverse",
    )

st.markdown("---")
col5, col6 = st.columns(2)

with col5:
    st.subheader("Здоровье целей")

    on_track = summary.get("goals_on_track", 0)
    at_risk = summary.get("goals_at_risk", 0)
    critical = summary.get("goals_critical", 0)

    # Собираем только ненулевые значения
    labels = []
    values = []
    colors = []
    for label, value, color in zip(
        ["В норме", "Под угрозой", "Критические"],
        [on_track, at_risk, critical],
        ["#27ae60", "#f39c12", "#e74c3c"],
    ):
        if value > 0:
            labels.append(label)
            values.append(value)
            colors.append(color)

    if values:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    marker_colors=colors,
                    hole=0.5,
                    textinfo="percent",
                    textposition="auto",
                    textfont_size=14,
                )
            ]
        )
        fig.update_layout(
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Нет данных для отображения")

with col6:
    st.subheader("Общая статистика")

    stats_col1, stats_col2 = st.columns(2)
    with stats_col1:
        st.metric("Проектов", summary.get("total_projects", 0))
        st.metric("Задач всего", summary.get("total_tasks", 0))
    with stats_col2:
        st.metric("Задач заблокировано", summary.get("blocked_tasks", 0))
        avg_risk = summary.get("avg_risk_score", 0)
        st.metric("Средний риск", f"{avg_risk:.0%}")

st.markdown("---")
st.subheader("Распределение по уровням риска")

risks = get_risks()
if risks:
    risk_df = pd.DataFrame(risks)
    level_colors = {
        "critical": "#e74c3c",
        "high": "#e67e22",
        "medium": "#f39c12",
        "low": "#27ae60",
    }
    level_labels = {
        "critical": "Критический",
        "high": "Высокий",
        "medium": "Средний",
        "low": "Низкий",
    }

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        level_counts = risk_df["risk_level"].value_counts()
        risk_levels_fig = px.pie(
            names=[level_labels.get(level, level) for level in level_counts.index],
            values=level_counts.values,
            color_discrete_sequence=[
                level_colors.get(level, "#95a5a6") for level in level_counts.index
            ],
        )
        risk_levels_fig.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(risk_levels_fig, use_container_width=True)

    with chart_col2:
        st.caption("Факторы риска")
        if "blocked_tasks_count" in risk_df.columns:
            factor_data = {
                "Фактор": [
                    "Заблокированные задачи",
                    "Задержки документов",
                    "Отставание от плана",
                ],
                "Среднее значение": [
                    risk_df["blocked_tasks_count"].mean(),
                    risk_df["document_delays"].mean(),
                    risk_df["overdue_tasks_ratio"].mean() * 100,
                ],
            }
            risk_factors_fig = px.bar(
                pd.DataFrame(factor_data),
                x="Фактор",
                y="Среднее значение",
                color_discrete_sequence=["#667eea"],
            )
            risk_factors_fig.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(risk_factors_fig, use_container_width=True)
else:
    st.info("Данные о рисках отсутствуют. Запустите анализ.")

st.markdown("---")
st.subheader("Топ рисков")

top_risks = summary.get("top_risks", [])
if top_risks:
    rows_html = ""
    for risk in top_risks:
        level_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
            risk["risk_level"], "⚪"
        )
        risk_score = f"{risk['risk_score']:.0%}"
        blocked = int(risk["blocked_tasks_count"])
        description = (risk.get("ai_summary") or "")[:120]

        rows_html += f"""
        <tr>
            <td style="text-align: center;">{level_emoji}</td>
            <td>{risk['goal_title']}</td>
            <td style="text-align: center;">{risk_score}</td>
            <td style="text-align: center;">{blocked}</td>
            <td style="word-wrap: break-word; white-space: normal;">{description}</td>
        </tr>
        """

    table_html = f"""
    <style>
        .risk-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: 'Source Sans Pro', sans-serif;
        }}
        .risk-table th, .risk-table td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
            vertical-align: middle;  /* центрирование по вертикали */
        }}
        .risk-table th {{
            background-color: #f0f2f6;
            font-weight: 600;
        }}
        .risk-table {{
            table-layout: auto;
        }}
        /* Для тёмной темы */
        @media (prefers-color-scheme: dark) {{
            .risk-table th {{ background-color: #1e293b; color: #f8fafc; border-color: #334155; }}
            .risk-table td {{ border-color: #334155; }}
        }}
    </style>
    <table class="risk-table">
        <thead>
            <tr><th>Уровень</th><th>Цель</th><th>Риск</th><th>Блокеры</th><th>Описание</th></tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """

    try:
        st.html(table_html)  # для Streamlit >= 1.36
    except AttributeError:
        from streamlit.components.v1 import html

        html(table_html, height=400, scrolling=True)
else:
    st.info("Риски не обнаружены")
