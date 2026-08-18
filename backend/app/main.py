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
    POST /api/search            -> semantic retrieval
"""

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import DATA_DIR, EMBEDDING_MODELS, VECTOR_DATABASES, CHUNK_SIZE, CHUNK_OVERLAP
from app.pipeline import (
    get_dataset_stats,
    process_documents,
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
    model_name: str
    db_type: str
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
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    return {
        "embedding_models": EMBEDDING_MODELS,
        "vector_databases": VECTOR_DATABASES,
        "default_chunk_size": CHUNK_SIZE,
        "default_chunk_overlap": CHUNK_OVERLAP,
    }


@app.get("/api/stats")
def stats():
    return get_dataset_stats()


@app.post("/api/upload")
def upload_files(files: list[UploadFile] = File(...)):
    """
    Saves uploaded .txt files to the data directory.
    """
    DATA_DIR.mkdir(exist_ok=True)
    saved = 0

    for file in files:
        if not file.filename.endswith(".txt"):
            continue
        contents = file.file.read()
        with open(DATA_DIR / file.filename, "wb") as f:
            f.write(contents)
        saved += 1

    if saved == 0:
        raise HTTPException(status_code=400, detail="No .txt files received.")

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

    return {
        "status": "success",
        "vector_db": body.db_type,
        "embedding_model": body.model_name,
        "chunks_indexed": num_chunks,
    }


@app.post("/api/search")
def search(body: SearchRequest):
    """
    Runs semantic search and returns ordered results with relevance scores.
    """
    _validate_selections(body.model_name, body.db_type)

    try:
        results = search_documents_with_scores(
            body.query, body.model_name, body.db_type, top_k=body.top_k
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    return {"query": body.query, "top_k": body.top_k, "results": results}
