"""
Integrations with popular RAG frameworks.

Provides drop-in replacements for:
- LangChain text splitters
- LlamaIndex node parsers
"""

from typing import Any

from .chunker import SemanticChunker, RecursiveChunker, FixedSizeChunker, Chunk
from .tokenizer import get_tokenizer


# ============================================================================
# LangChain Integration
# ============================================================================

class LangChainTextSplitter:
    """
    LangChain-compatible text splitter interface.

    Drop-in replacement for LangChain's TextSplitter classes.

    Example:
        >>> from bunsetsu.integrations import LangChainTextSplitter
        >>> splitter = LangChainTextSplitter(strategy="semantic")
        >>> docs = splitter.split_text("日本語のテキスト...")
        >>> # Or with LangChain Documents
        >>> from langchain.schema import Document
        >>> doc = Document(page_content="テキスト", metadata={"source": "file.txt"})
        >>> split_docs = splitter.split_documents([doc])
    """

    def __init__(
        self,
        strategy: str = "semantic",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        tokenizer: str = "simple",
        **kwargs,
    ):
        """
        Initialize LangChain-compatible splitter.

        Args:
            strategy: "fixed", "semantic", or "recursive"
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            tokenizer: "simple", "mecab", or "sudachi"
            **kwargs: Additional chunker arguments
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tokenizer
        self.kwargs = kwargs

        # Initialize chunker
        if strategy == "fixed":
            self._chunker = FixedSizeChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        elif strategy == "semantic":
            self._chunker = SemanticChunker(
                tokenizer=get_tokenizer(tokenizer),
                max_chunk_size=chunk_size,
                **kwargs,
            )
        elif strategy == "recursive":
            self._chunker = RecursiveChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def split_text(self, text: str) -> list[str]:
        """
        Split text into chunks (LangChain interface).

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = self._chunker.chunk(text)
        return [chunk.text for chunk in chunks]

    def split_documents(self, documents: list[Any]) -> list[Any]:
        """
        Split LangChain Documents.

        Args:
            documents: List of LangChain Document objects

        Returns:
            List of split Document objects
        """
        try:
            from langchain.schema import Document
        except ImportError:
            raise ImportError(
                "split_documents requires langchain. "
                "Install with: pip install langchain"
            )

        split_docs = []
        for doc in documents:
            chunks = self._chunker.chunk(doc.page_content)
            for i, chunk in enumerate(chunks):
                metadata = doc.metadata.copy()
                metadata["chunk_index"] = i
                metadata["start_char"] = chunk.start_char
                metadata["end_char"] = chunk.end_char
                split_docs.append(Document(
                    page_content=chunk.text,
                    metadata=metadata,
                ))

        return split_docs


# ============================================================================
# LlamaIndex Integration
# ============================================================================

class LlamaIndexNodeParser:
    """
    LlamaIndex-compatible node parser.

    Drop-in replacement for LlamaIndex's NodeParser classes.

    Example:
        >>> from bunsetsu.integrations import LlamaIndexNodeParser
        >>> parser = LlamaIndexNodeParser(strategy="semantic")
        >>> nodes = parser.get_nodes_from_documents(documents)
    """

    def __init__(
        self,
        strategy: str = "semantic",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        tokenizer: str = "simple",
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        **kwargs,
    ):
        """
        Initialize LlamaIndex-compatible parser.

        Args:
            strategy: "fixed", "semantic", or "recursive"
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            tokenizer: "simple", "mecab", or "sudachi"
            include_metadata: Include metadata in nodes
            include_prev_next_rel: Include prev/next relationships
            **kwargs: Additional chunker arguments
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tokenizer
        self.include_metadata = include_metadata
        self.include_prev_next_rel = include_prev_next_rel
        self.kwargs = kwargs

        # Initialize chunker
        if strategy == "fixed":
            self._chunker = FixedSizeChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        elif strategy == "semantic":
            self._chunker = SemanticChunker(
                tokenizer=get_tokenizer(tokenizer),
                max_chunk_size=chunk_size,
                **kwargs,
            )
        elif strategy == "recursive":
            self._chunker = RecursiveChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def get_nodes_from_documents(self, documents: list[Any]) -> list[Any]:
        """
        Parse documents into nodes.

        Args:
            documents: List of LlamaIndex Document objects

        Returns:
            List of TextNode objects
        """
        try:
            from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
        except ImportError:
            try:
                from llama_index.schema import TextNode, NodeRelationship, RelatedNodeInfo
            except ImportError:
                raise ImportError(
                    "get_nodes_from_documents requires llama-index. "
                    "Install with: pip install llama-index"
                )

        all_nodes = []

        for doc in documents:
            chunks = self._chunker.chunk(doc.text)
            nodes = []

            for i, chunk in enumerate(chunks):
                metadata = {}
                if self.include_metadata:
                    metadata = doc.metadata.copy() if hasattr(doc, "metadata") else {}
                    metadata["chunk_index"] = i
                    metadata["start_char"] = chunk.start_char
                    metadata["end_char"] = chunk.end_char

                node = TextNode(
                    text=chunk.text,
                    metadata=metadata,
                )
                nodes.append(node)

            # Add prev/next relationships
            if self.include_prev_next_rel and len(nodes) > 1:
                for i, node in enumerate(nodes):
                    if i > 0:
                        node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(
                            node_id=nodes[i - 1].node_id,
                        )
                    if i < len(nodes) - 1:
                        node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(
                            node_id=nodes[i + 1].node_id,
                        )

            all_nodes.extend(nodes)

        return all_nodes


# Convenience aliases
JapaneseTextSplitter = LangChainTextSplitter
JapaneseNodeParser = LlamaIndexNodeParser
