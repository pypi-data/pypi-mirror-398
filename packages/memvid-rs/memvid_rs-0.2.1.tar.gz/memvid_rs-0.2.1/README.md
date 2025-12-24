# memvid-rs (Python Bindings)

[![🇰🇷 한국어 (Korean)](https://img.shields.io/badge/lang-Korean-blue.svg)](README_ko.md)
[![PyPI version](https://badge.fury.io/py/memvid-rs.svg)](https://badge.fury.io/py/memvid-rs)

**Memvid-rs** combines the performance of Rust with the ease of use of Python. It encodes text data into QR codes and then into video frames, with **semantic search** capabilities powered by FAISS and SentenceTransformers.

This project exposes the core logic written in Rust (`MemvidEncoder`, `MemvidDecoder`) as a Python module via PyO3, with a high-level Python wrapper for semantic search.

> **Attribution**: This project is a port reimplemented in Rust based on the ideas and design of [Olow304/memvid](https://github.com/Olow304/memvid). We deeply appreciate the innovative approach of the original project.

## 🚀 Key Features

-   **High Performance**: Leverages Rust's parallel processing and efficient memory management for fast text-to-video conversion.
-   **Semantic Search**: FAISS vector index with SentenceTransformer embeddings for <100ms search across millions of chunks.
-   **Pythonic**: Easy to install via `pip` and use naturally as a Python object.
-   **Strong Compression**: Significantly reduces storage space via Text -> QR -> Video (H.264/H.265) conversion.

## 📦 Installation

### From PyPI (Recommended)

```bash
# Basic installation (Rust encoder/decoder only)
pip install memvid-rs

# Full installation with semantic search
pip install memvid-rs[full]
```

### From Source (Development)

Requires Rust and Python development environments.

```bash
# 1. Install Rust & FFmpeg
brew install rust ffmpeg

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Maturin and dependencies
pip install maturin sentence-transformers faiss-cpu

# 4. Build and install
maturin develop --release
```

## 💻 Usage

### Basic Usage (Rust Encoder Only)

```python
import memvid_rs

# Initialize Encoder
encoder = memvid_rs.MemvidEncoder()

# Add Text (chunk_size=200, overlap=20)
text_data = "Memvid-rs is fast and efficient. " * 100
encoder.add_text(text_data, chunk_size=200, overlap=20)

# Build Video
encoder.build("output.mp4", "index.json")
print("Video created: output.mp4")
```

### Full Usage with Semantic Search

```python
from memvid import MemvidEncoder, MemvidRetriever

# === ENCODING ===
encoder = MemvidEncoder()

# Add text chunks
texts = [
    "Python is a high-level programming language.",
    "Machine learning uses algorithms to learn from data.",
    "Rust is focused on safety and performance.",
]
for text in texts:
    encoder.add_text(text, chunk_size=512)

# Build video + FAISS index
encoder.build_video("memory.mp4", "index")
# Creates: memory.mp4, index.faiss, index.json

# === RETRIEVAL ===
retriever = MemvidRetriever("memory.mp4", "index")

# Semantic search
results = retriever.search("programming language", top_k=3)
for text, score, metadata in results:
    print(f"[{score:.3f}] {text}")

# Search with context
results = retriever.search_with_context(
    "artificial intelligence",
    top_k=2,
    context_before=1,
    context_after=1
)
```

## 🔧 API Reference

### `memvid.MemvidEncoder`

High-level encoder with semantic search support.

```python
encoder = MemvidEncoder(
    model_name="all-MiniLM-L6-v2",  # SentenceTransformer model
    index_type="Flat"               # FAISS index type: "Flat" or "IVF"
)

encoder.add_text(text, chunk_size=512, overlap=50)
encoder.add_pdf("document.pdf")  # Requires PyPDF2
encoder.build_video("output.mp4", "index")
```

### `memvid.MemvidRetriever`

Semantic search and retrieval from QR videos.

```python
retriever = MemvidRetriever(
    video_path="memory.mp4",
    index_path="index",
    cache_size=100  # Frame cache size
)

# Search methods
results = retriever.search(query, top_k=5)
results = retriever.search_with_context(query, top_k=5, context_before=1, context_after=1)
text = retriever.get_chunk(chunk_id)
all_text = retriever.get_all_text()
stats = retriever.get_stats()
```

### `memvid_rs` (Low-level Rust API)

```python
import memvid_rs

# Encoder
encoder = memvid_rs.MemvidEncoder()
encoder.add_text(text, chunk_size, overlap)
encoder.build(video_path, index_path)
chunks = encoder.get_chunks()

# Decoder
decoder = memvid_rs.MemvidDecoder(video_path, index_path)
text = decoder.get_chunk_text(chunk_id)
texts = decoder.get_chunks_text([0, 1, 2])
all_chunks = decoder.get_all_chunks()
info = decoder.get_video_info()
```

## ⚠️ Requirements

-   **System**: macOS (Tested), Linux, Windows
-   **Runtime**: `ffmpeg` (Required for video encoding)
    -   macOS: `brew install ffmpeg`
-   **Python**: >= 3.8
-   **Optional**: `sentence-transformers`, `faiss-cpu` for semantic search

## 📄 License

MIT License


