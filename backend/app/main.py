"""
main.py
-------
FastAPI backend for the RAG pipeline. Deployed on Render.

Endpoints:
    GET  /health                -> liveness probe
    GET  /api/config            -> available embedding models & vector DBs
    GET  /api/stats             -> dataset statistics
    POST /api/upload            -> upload .txt documents
    POST /api/process           -> chunk + embed + build vector store
    GET  /api/keep-alive        -> keep server awake (ping every 30s)
    POST /api/search            -> semantic retrieval
"""

import os
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import (
    DATA_DIR,
    EMBEDDING_MODELS,
    VECTOR_DATABASES,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from app.pipeline import (
    SUPPORTED_EXTENSIONS,
    get_active_config,
    get_dataset_stats,
    process_documents,
    save_active_config,
    search_documents_with_scores,
)

app = FastAPI(title="RAG Semantic Search API", version="1.0.0")

# Allow the Vercel frontend (or any client) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Request / response models
# -----------------------------
class ProcessRequest(BaseModel):
    model_name: str
    db_type: str
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP

    model_config = {"protected_namespaces": ()}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

    model_config = {"protected_namespaces": ()}


def _validate_selections(model_name: str, db_type: str):
    if model_name not in EMBEDDING_MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown embedding model: {model_name}")
    if db_type not in VECTOR_DATABASES:
        raise HTTPException(status_code=400, detail=f"Unknown vector database: {db_type}")


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    logger.info("Config request received")
    return {
        "embedding_models": EMBEDDING_MODELS,
        "vector_databases": VECTOR_DATABASES,
        "default_chunk_size": CHUNK_SIZE,
        "default_chunk_overlap": CHUNK_OVERLAP,
        "active_config": get_active_config(),
    }


@app.get("/api/stats")
def stats():
    return get_dataset_stats()


@app.post("/api/upload")
def upload_files(files: list[UploadFile] = File(...)):
    """
    Saves uploaded .txt / .pdf documents to the data directory.
    """
    DATA_DIR.mkdir(exist_ok=True)
    saved = 0
    rejected = 0

    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            rejected += 1
            continue
        contents = file.file.read()
        with open(DATA_DIR / file.filename, "wb") as f:
            f.write(contents)
        saved += 1

    if saved == 0:
        detail = f"No supported file received. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}."
        if rejected:
            detail += f" Rejected {rejected} unsupported file(s)."
        raise HTTPException(status_code=400, detail=detail)

    return {"saved": saved, "stats": get_dataset_stats()}


@app.post("/api/process")
def process(body: ProcessRequest):
    """
    Chunks uploaded documents, embeds them, and builds the selected vector store.
    """
    _validate_selections(body.model_name, body.db_type)

    try:
        num_chunks = process_documents(
            body.model_name,
            body.db_type,
            chunk_size=body.chunk_size,
            chunk_overlap=body.chunk_overlap,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Remember what built the store so Search can reuse it automatically.
    save_active_config(body.model_name, body.db_type)

    return {
        "status": "success",
        "vector_db": body.db_type,
        "embedding_model": body.model_name,
        "chunks_indexed": num_chunks,
    }


@app.get("/api/keep-alive")
def keep_alive():
    logger.info("Keep-alive ping received - server awake")
    return {"status": "awake"}


@app.post("/api/search")
def search(body: SearchRequest):
    """
    Runs semantic search and returns ordered results with relevance scores.

    The embedding model and vector DB are NOT requested here — they are
    reused from the config that built the store (see save_active_config).
    """
    active = get_active_config()
    if active is None:
        raise HTTPException(
            status_code=400,
            detail="No vector store has been built yet. Process documents first.",
        )

    try:
        results = search_documents_with_scores(
            body.query, active["model_name"], active["db_type"], top_k=body.top_k
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    return {
        "query": body.query,
        "top_k": body.top_k,
        "model_name": active["model_name"],
        "db_type": active["db_type"],
        "results": results,
    }
