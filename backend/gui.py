"""
gui.py
------
Local Streamlit GUI for the RAG pipeline (optional, runs on your machine).
The deployed web UI lives in `frontend/` (Vercel) and talks to the
FastAPI backend (Render) via the /api endpoints.

Run locally:  streamlit run backend/gui.py
"""

import os
import streamlit as st
from app.config import DATA_DIR, EMBEDDING_MODELS, VECTOR_DATABASES
from app.pipeline import process_documents, search_documents

st.set_page_config(page_title="Document Search System")
st.title("Document Search & Evaluation System")

# -----------------------------
# Sidebar Configuration
# -----------------------------
model = st.sidebar.selectbox("Embedding Model", EMBEDDING_MODELS)
db_type = st.sidebar.selectbox("Vector Database", VECTOR_DATABASES)
top_k = st.sidebar.slider("Top-K Results", 1, 10, 5)

# -----------------------------
# File Upload
# -----------------------------
st.subheader("Upload Documents")

uploaded_files = st.file_uploader(
    "Upload TXT / PDF files",
    type=["txt", "pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    os.makedirs(DATA_DIR, exist_ok=True)

    for file in uploaded_files:
        with open(os.path.join(DATA_DIR, file.name), "wb") as f:
            f.write(file.getbuffer())

    st.success("Files uploaded successfully.")

# -----------------------------
# Processing Button
# -----------------------------
if st.button("Process Documents"):
    with st.spinner("Processing..."):
        process_documents(model, db_type)
    st.success("Vector store created!")

# -----------------------------
# Search Section
# -----------------------------
st.subheader("Search")
query = st.text_input("Enter your query")

if st.button("Search") and query:
    with st.spinner("Searching..."):
        results = search_documents(query, model, db_type, top_k)

    if not results:
        st.info("No relevant documents found.")
    else:
        st.success(f"Found {len(results)} relevant chunk(s)")

        # Stream documents one by one
        for i, doc in enumerate(results, 1):
            with st.container():
                st.markdown(f"**Result {i}**")
                source = doc.metadata.get("source", "")
                if source:
                    st.caption(f"Source: {source}")

                # Stream the content word-by-word
                words = doc.page_content.split()
                text_placeholder = st.empty()
                current_text = ""

                for word in words:
                    current_text += word + " "
                    text_placeholder.markdown(current_text)
                    # Small delay gives nice typing animation
                    import time
                    time.sleep(0.015)   # ← adjust speed (0.01–0.03 feels natural)

                # Final clean version (prevents extra space issues)
                text_placeholder.markdown(doc.page_content)
