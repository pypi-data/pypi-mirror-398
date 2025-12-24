"""
memvid_rs - High-performance video memory with semantic search

This package provides:
- MemvidEncoder: Encode text chunks into QR video with embeddings
- MemvidRetriever: Semantic search and retrieval from QR videos
- MemvidDecoder: Low-level QR video decoder (Rust)
- IndexManager: Embedding generation and FAISS vector search
"""

# Import Rust native module
from memvid_rs._memvid_rs import MemvidEncoder as _RustEncoder
from memvid_rs._memvid_rs import MemvidDecoder

# Import Python wrappers
from .encoder import MemvidEncoder
from .retriever import MemvidRetriever
from .index import IndexManager

__version__ = "0.3.0"
__all__ = [
    "MemvidEncoder",
    "MemvidRetriever",
    "MemvidDecoder",
    "IndexManager",
    "_RustEncoder",
]
