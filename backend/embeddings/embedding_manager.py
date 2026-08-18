"""
embedding_manager.py
--------------------
This module is responsible for initializing embedding models.
Separating this logic allows easy replacement of embedding models later.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from app.config import MODEL_CACHE_DIR


def load_embedding_model(model_name: str):
    """
    Loads a HuggingFace embedding model.
    The model is cached locally so future runs work offline.
    """
    return HuggingFaceEmbeddings(
        model_name=model_name,
        cache_folder=str(MODEL_CACHE_DIR)
    )
