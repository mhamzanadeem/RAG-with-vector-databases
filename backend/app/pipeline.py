"""
pipeline.py
-----------
Core backend logic:
- Loading documents
- Chunking text
- Creating vector stores
- Performing similarity search
- Reporting dataset statistics

Consumed by the FastAPI layer (app/main.py) and the local Streamlit GUI (gui.py).
"""

import json
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import (
    ACTIVE_CONFIG_FILE,
    DATA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODELS,
    VECTOR_DATABASES,
)
from embeddings.embedding_manager import load_embedding_model
from Vector_Store import create_vector_store, load_vector_store


def save_active_config(model_name: str, db_type: str):
    """
    Persists which embedding model + vector DB built the current store,
    so search can reuse it automatically instead of asking again.
    """
    ACTIVE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTIVE_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"model_name": model_name, "db_type": db_type}, f)


def get_active_config():
    """
    Returns the stored {model_name, db_type} used to build the current
    vector store, or None if nothing has been processed yet.
    """
    if not ACTIVE_CONFIG_FILE.exists():
        return None

    with open(ACTIVE_CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("model_name") not in EMBEDDING_MODELS:
        return None
    if data.get("db_type") not in VECTOR_DATABASES:
        return None
    return data


SUPPORTED_EXTENSIONS = (".txt", ".pdf")


def load_documents():
    """
    Loads all supported documents (.txt, .pdf) from the data directory.
    """
    documents = []

    for file in os.listdir(DATA_DIR):
        ext = os.path.splitext(file)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        file_path = os.path.join(DATA_DIR, file)
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
            else:
                loader = TextLoader(file_path, encoding="utf-8")
            documents.extend(loader.load())
        except Exception as e:
            print(f"Error loading {file}: {e}")

    return documents


def split_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Splits documents into smaller chunks for better embeddings.
    Chunk size / overlap are configurable so different chunking
    strategies can be compared (see README § 2).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(documents)


def process_documents(model_name, db_type, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Full pipeline:
    - Load documents
    - Split into chunks
    - Create embeddings
    - Store in vector DB
    """
    docs = load_documents()
    if not docs:
        raise ValueError("No documents found. Upload at least one .txt or .pdf file first.")

    chunks = split_documents(docs, chunk_size, chunk_overlap)
    embeddings = load_embedding_model(model_name)

    create_vector_store(db_type, chunks, embeddings)
    return len(chunks)


def search_documents(query, model_name, db_type, top_k=5):
    """
    Performs similarity search on stored vectors and returns
    the raw LangChain Document objects (used by the local GUI).
    """
    embeddings = load_embedding_model(model_name)
    db = load_vector_store(db_type, embeddings)
    return db.similarity_search(query, k=top_k)


def search_documents_with_scores(query, model_name, db_type, top_k=5):
    """
    Performs similarity search and returns JSON-friendly results.

    Returns a list of dicts:
        {content, source, score, relevance}

    `relevance` is normalised to (0, 1] where higher = more similar.
    - Chroma returns cosine similarity directly (higher is better).
    - FAISS returns L2 distance by default (lower is better), so it is
      converted with relevance = 1 / (1 + distance).
    """
    embeddings = load_embedding_model(model_name)
    db = load_vector_store(db_type, embeddings)

    results = []

    if db_type == "FAISS":
        for doc, score in db.similarity_search_with_score(query, k=top_k):
            score = float(score)
            results.append({
                "content": doc.page_content,
                "source": os.path.basename(doc.metadata.get("source", "")),
                "score": round(score, 4),
                "relevance": round(1.0 / (1.0 + score), 4),
            })
    else:  # Chroma
        for doc, score in db.similarity_search_with_relevance_scores(query, k=top_k):
            score = float(score)
            results.append({
                "content": doc.page_content,
                "source": os.path.basename(doc.metadata.get("source", "")),
                "score": round(score, 4),
                "relevance": round(score, 4),
            })

    return results


def get_dataset_stats():
    """
    Returns basic statistics about the uploaded document set (txt + pdf).
    """
    files = [
        f for f in os.listdir(DATA_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
    ]
    total_bytes = sum(os.path.getsize(os.path.join(DATA_DIR, f)) for f in files)

    return {
        "document_count": len(files),
        "files": sorted(files),
        "total_size_bytes": total_bytes,
    }
