"""Semantic search page — vector-based knowledge base search."""
import streamlit as st

from dashboard.api_client import semantic_search

st.header("🔍 Семантический поиск")
st.markdown("Поиск по базе знаний с использованием AI-эмбеддингов. Находит связанные документы по смыслу, а не только по ключевым словам.")

query = st.text_input(
    "Введите запрос",
    placeholder="Например: задержка лицензирования LATAM",
)

col1, col2 = st.columns([1, 3])
with col1:
    limit = st.slider("Количество результатов", 1, 20, 5)

if query:
    with st.spinner("Поиск..."):
        result = semantic_search(query, limit=limit)

    if result and result.get("results"):
        st.success(f"Найдено результатов: {result['count']}")

        for i, doc in enumerate(result["results"], 1):
            similarity = doc.get("similarity", 0)
            color = "#27ae60" if similarity > 0.7 else "#f39c12" if similarity > 0.4 else "#95a5a6"

            with st.expander(f"#{i} {doc['title']} (релевантность: {similarity:.0%})"):
                st.write(f"**Источник:** {doc.get('source_system', 'N/A')}")
                if doc.get("content"):
                    st.write(doc["content"])
    else:
        st.warning("Ничего не найдено. Попробуйте другой запрос.")
