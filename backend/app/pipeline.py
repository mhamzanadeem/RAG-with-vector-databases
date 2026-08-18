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

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from embeddings.embedding_manager import load_embedding_model
from Vector_Store import create_vector_store, load_vector_store


def load_documents():
    """
    Loads all .txt documents from the data directory.
    """
    documents = []

    for file in os.listdir(DATA_DIR):
        if file.endswith(".txt"):
            file_path = os.path.join(DATA_DIR, file)
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {file}: {e}")

    return documents


def split_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Splits documents into smaller chunks for better embeddings.
    Chunk size / overlap are configurable so different chunking
    strategies can be compared (see docs/chunking-strategies.md).
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
        raise ValueError("No documents found. Upload at least one .txt file first.")

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
    Returns basic statistics about the uploaded document set.
    """
    txt_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]
    total_bytes = sum(os.path.getsize(os.path.join(DATA_DIR, f)) for f in txt_files)

    return {
        "document_count": len(txt_files),
        "files": sorted(txt_files),
        "total_size_bytes": total_bytes,
    }
