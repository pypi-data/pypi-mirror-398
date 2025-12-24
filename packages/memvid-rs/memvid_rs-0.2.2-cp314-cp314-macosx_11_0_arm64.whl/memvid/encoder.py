"""
MemvidEncoder - High-level encoder with semantic search support

Wraps the Rust MemvidEncoder and adds:
- Automatic embedding generation
- FAISS index creation
- PDF and text file support
"""

from pathlib import Path
from typing import List, Optional, Union

from .index import IndexManager


class MemvidEncoder:
    """
    Encode text into QR video with semantic search capabilities.

    Example:
        encoder = MemvidEncoder()
        encoder.add_text("Your long text here...", chunk_size=512)
        encoder.build_video("output.mp4", "index")
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large-instruct",
        index_type: str = "Flat",
    ):
        """
        Initialize MemvidEncoder.

        Args:
            model_name: SentenceTransformer model name for embeddings
            index_type: FAISS index type ("Flat" or "IVF")
        """
        try:
            import memvid_rs
            self._rust_encoder = memvid_rs.MemvidEncoder()
        except ImportError:
            raise ImportError(
                "memvid_rs native module not found. "
                "Build with: maturin develop --release"
            )

        self.index_manager = IndexManager(
            model_name=model_name,
            index_type=index_type,
        )
        self.chunks: List[str] = []

    def add_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> int:
        """
        Add text and chunk it automatically.

        Args:
            text: Text content to add
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks

        Returns:
            Number of chunks added
        """
        # Use Rust encoder for chunking
        self._rust_encoder.add_text(text, chunk_size, overlap)

        # Get chunks from Rust encoder
        new_chunks = self._rust_encoder.get_chunks()
        num_new = len(new_chunks) - len(self.chunks)

        if num_new > 0:
            added_chunks = new_chunks[len(self.chunks):]
            self.chunks = new_chunks

        return num_new

    def add_chunks(self, chunks: List[str]) -> int:
        """
        Add pre-chunked text.

        Args:
            chunks: List of text chunks

        Returns:
            Number of chunks added
        """
        for chunk in chunks:
            # Add each chunk as a small text
            self._rust_encoder.add_text(chunk, len(chunk) + 1, 0)

        self.chunks = self._rust_encoder.get_chunks()
        return len(chunks)

    def add_pdf(self, pdf_path: Union[str, Path]) -> int:
        """
        Add text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of chunks added
        """
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF support. "
                "Install with: pip install PyPDF2"
            )

        pdf_path = Path(pdf_path)
        text = ""

        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"

        return self.add_text(text)

    def build_video(
        self,
        video_path: Union[str, Path],
        index_path: Union[str, Path],
        show_progress: bool = True,
    ) -> None:
        """
        Build video and create search index.

        This method:
        1. Generates embeddings for all chunks
        2. Creates FAISS index
        3. Builds QR video with Rust encoder
        4. Saves index files

        Args:
            video_path: Output video file path
            index_path: Output index base path (without extension)
            show_progress: Show progress bar
        """
        video_path = Path(video_path)
        index_path = Path(index_path)

        if not self.chunks:
            raise ValueError("No chunks to encode. Add text first.")

        # Generate embeddings and add to index
        frame_numbers = list(range(len(self.chunks)))
        self.index_manager.add_chunks(
            self.chunks,
            frame_numbers=frame_numbers,
            show_progress=show_progress,
        )

        # Build video with Rust encoder
        # Note: Rust encoder also creates a basic index.json
        rust_index_path = str(index_path) + "_frames.json"
        self._rust_encoder.build(str(video_path), rust_index_path)

        # Save semantic search index
        self.index_manager.save(str(index_path))

    def get_stats(self) -> dict:
        """Get encoder statistics."""
        return {
            "total_chunks": len(self.chunks),
            "model_name": self.index_manager.model_name,
            "index_type": self.index_manager.index_type,
        }
