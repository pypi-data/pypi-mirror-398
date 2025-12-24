"""
memvid - High-performance video memory with semantic search

This package provides:
- MemvidEncoder: Encode text chunks into QR video with embeddings
- MemvidRetriever: Semantic search and retrieval from QR videos
- IndexManager: Embedding generation and FAISS vector search
"""

from .encoder import MemvidEncoder
from .retriever import MemvidRetriever
from .index import IndexManager

__version__ = "0.1.1"
__all__ = ["MemvidEncoder", "MemvidRetriever", "IndexManager"]
