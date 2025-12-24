"""
IndexManager - Embedding generation and FAISS vector search

Handles:
- Text chunk embedding with SentenceTransformer
- FAISS index creation and management
- Semantic similarity search
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional


class IndexManager:
    """Manages text embeddings and FAISS vector index for semantic search."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_type: str = "Flat",
        nlist: int = 100,
    ):
        """
        Initialize IndexManager.

        Args:
            model_name: SentenceTransformer model name
            index_type: FAISS index type ("Flat" or "IVF")
            nlist: Number of clusters for IVF index
        """
        self.model_name = model_name
        self.index_type = index_type
        self.nlist = nlist

        self._model = None
        self._index = None
        self._faiss = None

        self.chunks: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.dimension: int = 0

    def _load_model(self):
        """Lazy load the SentenceTransformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def _load_faiss(self):
        """Lazy load FAISS."""
        if self._faiss is None:
            try:
                import faiss
                self._faiss = faiss
            except ImportError:
                raise ImportError(
                    "faiss-cpu is required. "
                    "Install with: pip install faiss-cpu"
                )
        return self._faiss

    def add_chunks(
        self,
        chunks: List[str],
        frame_numbers: Optional[List[int]] = None,
        show_progress: bool = True,
    ) -> None:
        """
        Add text chunks and generate embeddings.

        Args:
            chunks: List of text chunks to add
            frame_numbers: Corresponding frame numbers (default: sequential)
            show_progress: Show progress bar
        """
        if not chunks:
            return

        if frame_numbers is None:
            start_idx = len(self.chunks)
            frame_numbers = list(range(start_idx, start_idx + len(chunks)))

        model = self._load_model()
        faiss = self._load_faiss()

        # Generate embeddings
        new_embeddings = model.encode(
            chunks,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
        )
        new_embeddings = np.array(new_embeddings).astype("float32")

        # Store dimension
        if self.dimension == 0:
            self.dimension = new_embeddings.shape[1]

        # Add to chunks and metadata
        for i, (chunk, frame_num) in enumerate(zip(chunks, frame_numbers)):
            chunk_id = len(self.chunks)
            self.chunks.append(chunk)
            self.metadata.append({
                "id": chunk_id,
                "frame": frame_num,
                "text_length": len(chunk),
            })

        # Update embeddings array
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        # Rebuild index
        self._build_index()

    def _build_index(self) -> None:
        """Build or rebuild FAISS index."""
        if self.embeddings is None or len(self.embeddings) == 0:
            return

        faiss = self._load_faiss()

        if self.index_type == "IVF" and len(self.embeddings) >= self.nlist:
            # Use IVF index for large datasets
            quantizer = faiss.IndexFlatL2(self.dimension)
            self._index = faiss.IndexIVFFlat(
                quantizer, self.dimension, self.nlist
            )
            self._index.train(self.embeddings)
            self._index.add(self.embeddings)
        else:
            # Use flat index for small datasets or fallback
            self._index = faiss.IndexFlatL2(self.dimension)
            self._index.add(self.embeddings)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        Search for similar chunks.

        Args:
            query: Query text
            top_k: Number of results to return

        Returns:
            List of (chunk_id, distance, metadata) tuples
        """
        if self._index is None or len(self.chunks) == 0:
            return []

        model = self._load_model()

        # Generate query embedding
        query_embedding = model.encode(
            [query],
            normalize_embeddings=True,
        )
        query_embedding = np.array(query_embedding).astype("float32")

        # Search
        top_k = min(top_k, len(self.chunks))
        distances, indices = self._index.search(query_embedding, top_k)

        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0 and idx < len(self.metadata):
                results.append((int(idx), float(dist), self.metadata[idx]))

        return results

    def get_chunk(self, chunk_id: int) -> Optional[str]:
        """Get chunk text by ID."""
        if 0 <= chunk_id < len(self.chunks):
            return self.chunks[chunk_id]
        return None

    def save(self, path: str) -> None:
        """
        Save index to files.

        Creates:
        - {path}.faiss: FAISS index
        - {path}.json: Metadata and chunks
        """
        if self._index is None:
            raise ValueError("No index to save")

        faiss = self._load_faiss()
        base_path = Path(path)

        # Save FAISS index
        faiss.write_index(self._index, str(base_path.with_suffix(".faiss")))

        # Save metadata
        meta = {
            "version": "1.0",
            "model_name": self.model_name,
            "index_type": self.index_type,
            "dimension": self.dimension,
            "total_chunks": len(self.chunks),
            "chunks": self.chunks,
            "metadata": self.metadata,
        }
        with open(base_path.with_suffix(".json"), "w") as f:
            json.dump(meta, f, indent=2)

    def load(self, path: str) -> None:
        """
        Load index from files.

        Args:
            path: Base path (without extension)
        """
        faiss = self._load_faiss()
        base_path = Path(path)

        # Load FAISS index
        faiss_path = base_path.with_suffix(".faiss")
        if faiss_path.exists():
            self._index = faiss.read_index(str(faiss_path))
        else:
            raise FileNotFoundError(f"FAISS index not found: {faiss_path}")

        # Load metadata
        json_path = base_path.with_suffix(".json")
        if json_path.exists():
            with open(json_path, "r") as f:
                meta = json.load(f)

            self.model_name = meta.get("model_name", self.model_name)
            self.index_type = meta.get("index_type", self.index_type)
            self.dimension = meta.get("dimension", 0)
            self.chunks = meta.get("chunks", [])
            self.metadata = meta.get("metadata", [])
        else:
            raise FileNotFoundError(f"Metadata not found: {json_path}")

    def __len__(self) -> int:
        return len(self.chunks)
