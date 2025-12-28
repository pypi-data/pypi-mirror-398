"""
SanTOK Embedding Generation System

This module provides embedding generation from SanTOK tokens,
enabling inference-ready vector representations.
"""

from .embedding_generator import SanTOKEmbeddingGenerator
from .vector_store import SanTOKVectorStore, ChromaVectorStore, FAISSVectorStore

# Try importing WeaviateVectorStore (optional dependency)
try:
    from .weaviate_vector_store import WeaviateVectorStore
    WEAVIATE_AVAILABLE = True
except ImportError:
    WeaviateVectorStore = None
    WEAVIATE_AVAILABLE = False

from .inference_pipeline import SanTOKInferencePipeline

__all__ = [
    "SanTOKEmbeddingGenerator",
    "SanTOKVectorStore",
    "ChromaVectorStore",
    "FAISSVectorStore",
    "SanTOKInferencePipeline",
]

# Conditionally add WeaviateVectorStore to __all__ if available
if WEAVIATE_AVAILABLE:
    __all__.append("WeaviateVectorStore")