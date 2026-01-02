"""
Bunsetsu - Japanese semantic text chunking for RAG applications.

A lightweight, Japanese-optimized text chunking library designed for
Retrieval-Augmented Generation (RAG) systems.

Features:
- Multiple chunking strategies (fixed, semantic, recursive)
- Japanese morphological analysis support (MeCab, Sudachi)
- Zero dependencies by default (optional tokenizer backends)
- LangChain/LlamaIndex compatible interfaces

Quick Start:
    >>> from bunsetsu import chunk_text
    >>> chunks = chunk_text("日本語のテキストを分割します。")
    >>> for chunk in chunks:
    ...     print(chunk.text)

With specific strategy:
    >>> from bunsetsu import SemanticChunker
    >>> chunker = SemanticChunker(max_chunk_size=500)
    >>> chunks = chunker.chunk(long_text)

With MeCab tokenizer (higher accuracy):
    >>> from bunsetsu import SemanticChunker, MeCabTokenizer
    >>> chunker = SemanticChunker(tokenizer=MeCabTokenizer())
    >>> chunks = chunker.chunk(text)
"""

__version__ = "0.1.0"
__author__ = "YUA LAB"

from .tokenizer import (
    Token,
    TokenType,
    BaseTokenizer,
    SimpleTokenizer,
    MeCabTokenizer,
    SudachiTokenizer,
    get_tokenizer,
)

from .chunker import (
    Chunk,
    BaseChunker,
    FixedSizeChunker,
    SemanticChunker,
    RecursiveChunker,
    chunk_text,
)

__all__ = [
    # Version
    "__version__",
    # Tokenizer
    "Token",
    "TokenType",
    "BaseTokenizer",
    "SimpleTokenizer",
    "MeCabTokenizer",
    "SudachiTokenizer",
    "get_tokenizer",
    # Chunker
    "Chunk",
    "BaseChunker",
    "FixedSizeChunker",
    "SemanticChunker",
    "RecursiveChunker",
    "chunk_text",
]
