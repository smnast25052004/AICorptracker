"""
AI CorpTracker — CEO Dashboard

Strategic goal monitoring dashboard with real-time risk visualization.
"""

import streamlit as st

# Настройка страницы (должна быть первой командой Streamlit)
# st.set_page_config(page_title="AI CorpTracker", page_icon="🎯", layout="wide")

st.set_page_config(
    page_title="AI CorpTracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
     /* Название приложения вверху боковой панели — поднято повыше */
    [data-testid="stSidebarNav"]::before {
        content: "AI CorpTracker";
        display: block;
        text-align: center;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: -0.5rem;        /* поднимаем вверх */
        padding: 0.5rem 0.5rem 0.5rem 0.5rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    /* Дополнительно убираем верхний отступ у самого контейнера навигации */
    [data-testid="stSidebarNav"] {
        padding-top: 0 !important;
    }

    /* Скрыть пункт меню "Рекомендации" */
    div[data-testid="stSidebarNav"] li:has(a[href*="recommendations"]) {
        display: none;
    }

    /* Остальные стили (можно оставить как у вас) */
    .main-header { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; margin-bottom: 2rem; }
    [data-theme="light"] .main-header, [theme="light"] .main-header { color: #1a1a2e; }
    [data-theme="light"] .sub-header, [theme="light"] .sub-header { color: #555; }
    [data-theme="dark"] .main-header, [theme="dark"] .main-header { color: #f8fafc; }
    [data-theme="dark"] .sub-header, [theme="dark"] .sub-header { color: #94a3b8; }

    [data-testid="stMetricValue"] { font-weight: 600; }
    div[data-testid="metric-container"] {
        padding: 1rem 1.25rem !important;
        border-radius: 10px !important;
    }
    [data-theme="light"] div[data-testid="metric-container"],
    [theme="light"] div[data-testid="metric-container"] {
        background-color: #f0f2f6 !important;
        border: 1px solid #e2e8f0 !important;
    }
    [data-theme="dark"] div[data-testid="metric-container"],
    [theme="dark"] div[data-testid="metric-container"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }

    .risk-critical { color: #e74c3c; font-weight: 700; }
    .risk-high { color: #e67e22; font-weight: 700; }
    .risk-medium { color: #f39c12; font-weight: 600; }
    .risk-low { color: #27ae60; font-weight: 600; }
    [data-theme="dark"] .risk-critical, [theme="dark"] .risk-critical { color: #f87171; }
    [data-theme="dark"] .risk-high, [theme="dark"] .risk-high { color: #fb923c; }
    [data-theme="dark"] .risk-medium, [theme="dark"] .risk-medium { color: #fbbf24; }
    [data-theme="dark"] .risk-low, [theme="dark"] .risk-low { color: #4ade80; }

    footer { visibility: hidden; }
    a[href*="streamlit.io"] { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }
</style>
""",
    unsafe_allow_html=True,
)

overview_page = st.Page("pages/overview.py", title="Обзор", default=True)
goals_page = st.Page("pages/goals.py", title="Цели")
risks_page = st.Page("pages/risks.py", title="Риски")
recommendations_page = st.Page(
    "pages/recommendations.py", title="Рекомендации"
)  # оставляем
search_page = st.Page("pages/search.py", title="Поиск")
admin_page = st.Page("pages/admin.py", title="Управление")

# Добавляем рекомендации в навигацию, но они будут скрыты CSS
pg = st.navigation(
    {
        "Мониторинг": [
            overview_page,
            goals_page,
            risks_page,
            recommendations_page,
            search_page,
        ],
        "Администрирование": [admin_page],
    }
)

pg.run()
