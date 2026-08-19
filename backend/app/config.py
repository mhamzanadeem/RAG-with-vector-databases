"""
config.py
----------
This file contains all configuration variables used across the backend.
Keeping settings here makes the system modular and easy to modify.
Paths are computed relative to the backend root so the service works
both locally and when deployed on Render.
"""

from pathlib import Path

# -----------------------------
# Paths (relative to backend/)
# -----------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
VECTOR_STORE_DIR = BACKEND_DIR / "stores"
MODEL_CACHE_DIR = BACKEND_DIR / "model_cache"
ACTIVE_CONFIG_FILE = VECTOR_STORE_DIR / "active_config.json"

# -----------------------------
# Embedding Models (local Hugging Face)
# -----------------------------
EMBEDDING_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "BAAI/bge-small-en-v1.5"
]

# -----------------------------
# Vector Database options
# -----------------------------
VECTOR_DATABASES = ["FAISS", "Chroma"]

# -----------------------------
# Text chunking configuration
# -----------------------------
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
