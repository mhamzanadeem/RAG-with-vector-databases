"""
vector_store_manager.py
-----------------------
This module handles vector database creation and loading.
It supports multiple vector stores using a unified interface.
"""

import os
from langchain_community.vectorstores import FAISS, Chroma
from app.config import VECTOR_STORE_DIR


def create_vector_store(db_type, documents, embeddings):
    """
    Creates and saves a vector store based on selected DB type.
    """
    if db_type == "FAISS":
        db = FAISS.from_documents(documents, embeddings)
        db.save_local(os.path.join(VECTOR_STORE_DIR, "faiss_index"))

    elif db_type == "Chroma":
        db = Chroma.from_documents(
            documents,
            embeddings,
            persist_directory=os.path.join(VECTOR_STORE_DIR, "chroma_db")
        )
        db.persist()

    return db


def load_vector_store(db_type, embeddings):
    """
    Loads an existing vector store from disk.
    """
    if db_type == "FAISS":
        return FAISS.load_local(
            os.path.join(VECTOR_STORE_DIR, "faiss_index"),
            embeddings,
            allow_dangerous_deserialization=True
        )

    elif db_type == "Chroma":
        return Chroma(
            persist_directory=os.path.join(VECTOR_STORE_DIR, "chroma_db"),
            embedding_function=embeddings
        )