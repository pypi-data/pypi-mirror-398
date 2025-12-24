"""
MemvidRetriever - Semantic search and retrieval from QR videos

Provides:
- Fast semantic search using FAISS
- QR code decoding from video frames
- Context window retrieval
- Batch operations with caching
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from functools import lru_cache

from .index import IndexManager


class MemvidRetriever:
    """
    Retrieve text from QR videos using semantic search.

    Example:
        retriever = MemvidRetriever("output.mp4", "index")
        results = retriever.search("your query here", top_k=5)
        for text, score, metadata in results:
            print(f"Score: {score:.3f} - {text[:100]}...")
    """

    def __init__(
        self,
        video_path: Union[str, Path],
        index_path: Union[str, Path],
        cache_size: int = 100,
    ):
        """
        Initialize MemvidRetriever.

        Args:
            video_path: Path to QR video file
            index_path: Path to index (without extension)
            cache_size: Number of frames to cache
        """
        self.video_path = Path(video_path)
        self.index_path = Path(index_path)
        self.cache_size = cache_size

        # Load Rust decoder
        try:
            import memvid_rs
            # Try loading with frames index first
            frames_index = str(self.index_path) + "_frames.json"
            if Path(frames_index).exists():
                self._decoder = memvid_rs.MemvidDecoder(
                    str(self.video_path),
                    frames_index,
                )
            else:
                # Fallback to basic index
                self._decoder = memvid_rs.MemvidDecoder(
                    str(self.video_path),
                    str(self.index_path) + ".json",
                )
        except ImportError:
            raise ImportError(
                "memvid_rs native module not found. "
                "Build with: maturin develop --release"
            )

        # Load semantic index
        self.index_manager = IndexManager()
        self.index_manager.load(str(self.index_path))

        # Setup frame cache
        self._setup_cache()

    def _setup_cache(self):
        """Setup LRU cache for frame decoding."""
        @lru_cache(maxsize=self.cache_size)
        def cached_decode(frame_num: int) -> Optional[str]:
            return self._decoder.get_chunk_text(frame_num)

        self._cached_decode = cached_decode

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for relevant chunks.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (text, similarity_score, metadata) tuples
        """
        # Semantic search in FAISS index
        search_results = self.index_manager.search(query, top_k=top_k)

        results = []
        for chunk_id, distance, metadata in search_results:
            # Get text from index (faster than decoding video)
            text = self.index_manager.get_chunk(chunk_id)
            if text:
                # Convert L2 distance to similarity score (0-1)
                similarity = 1.0 / (1.0 + distance)
                results.append((text, similarity, metadata))

        return results

    def search_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_before: int = 1,
        context_after: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Search with surrounding context.

        Args:
            query: Search query
            top_k: Number of results
            context_before: Number of chunks before match to include
            context_after: Number of chunks after match to include

        Returns:
            List of result dicts with context
        """
        search_results = self.index_manager.search(query, top_k=top_k)

        results = []
        total_chunks = len(self.index_manager)

        for chunk_id, distance, metadata in search_results:
            # Get context window
            start_id = max(0, chunk_id - context_before)
            end_id = min(total_chunks, chunk_id + context_after + 1)

            context_chunks = []
            for i in range(start_id, end_id):
                text = self.index_manager.get_chunk(i)
                if text:
                    context_chunks.append({
                        "id": i,
                        "text": text,
                        "is_match": i == chunk_id,
                    })

            similarity = 1.0 / (1.0 + distance)
            results.append({
                "chunk_id": chunk_id,
                "text": self.index_manager.get_chunk(chunk_id),
                "similarity": similarity,
                "metadata": metadata,
                "context": context_chunks,
            })

        return results

    def get_chunk(self, chunk_id: int) -> Optional[str]:
        """
        Get chunk by ID.

        First tries the index, falls back to video decoding.

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk text or None
        """
        # Try index first (faster)
        text = self.index_manager.get_chunk(chunk_id)
        if text:
            return text

        # Fallback to video decoding
        return self._cached_decode(chunk_id)

    def get_chunks(self, chunk_ids: List[int]) -> Dict[int, str]:
        """
        Get multiple chunks by ID.

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            Dict mapping chunk_id to text
        """
        result = {}
        missing_ids = []

        # Try index first
        for chunk_id in chunk_ids:
            text = self.index_manager.get_chunk(chunk_id)
            if text:
                result[chunk_id] = text
            else:
                missing_ids.append(chunk_id)

        # Decode missing from video
        if missing_ids:
            decoded = self._decoder.get_chunks_text(missing_ids)
            result.update(decoded)

        return result

    def get_all_text(self) -> str:
        """
        Get all chunks as concatenated text.

        Returns:
            Full text content
        """
        chunks = []
        for i in range(len(self.index_manager)):
            text = self.index_manager.get_chunk(i)
            if text:
                chunks.append(text)
        return "\n".join(chunks)

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        video_info = self._decoder.get_video_info()
        return {
            "video_path": str(self.video_path),
            "total_chunks": len(self.index_manager),
            "total_frames": video_info.get("total_frames", 0),
            "model_name": self.index_manager.model_name,
            "cache_size": self.cache_size,
        }

    def clear_cache(self):
        """Clear the frame cache."""
        self._cached_decode.cache_clear()
        self._setup_cache()
