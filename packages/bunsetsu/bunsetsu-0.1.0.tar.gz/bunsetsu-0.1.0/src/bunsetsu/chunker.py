"""
Japanese semantic text chunking for RAG applications.

Provides multiple chunking strategies optimized for Japanese:
- FixedSizeChunker: Character-based with sentence boundary awareness
- SemanticChunker: Content-aware chunking using token analysis
- RecursiveChunker: Hierarchical splitting by document structure
"""

from dataclasses import dataclass, field
from typing import Callable, Iterator
import re

from .tokenizer import BaseTokenizer, SimpleTokenizer, Token, TokenType


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    start_char: int
    end_char: int
    token_count: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.text)

    def __str__(self) -> str:
        return self.text


class BaseChunker:
    """Abstract base class for text chunkers."""

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into chunks."""
        raise NotImplementedError

    def iter_chunks(self, text: str) -> Iterator[Chunk]:
        """Iterate over chunks (memory efficient)."""
        yield from self.chunk(text)


class FixedSizeChunker(BaseChunker):
    """
    Fixed-size chunker with Japanese sentence boundary awareness.

    Unlike naive character splitting, this chunker:
    - Respects sentence boundaries (。！？)
    - Avoids breaking in the middle of words
    - Handles Japanese punctuation correctly
    """

    # Japanese sentence endings
    SENTENCE_END = re.compile(r"[。！？!?]+")
    # Clause boundaries
    CLAUSE_END = re.compile(r"[、，,]+")

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        respect_sentences: bool = True,
    ):
        """
        Initialize fixed-size chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between consecutive chunks
            respect_sentences: If True, try to break at sentence boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_sentences = respect_sentences

    def _find_break_point(self, text: str, target: int) -> int:
        """Find the best break point near the target position."""
        if not self.respect_sentences:
            return target

        # Search window: look back up to 20% of chunk size
        window_start = max(0, target - self.chunk_size // 5)
        window = text[window_start:target]

        # First, try to find sentence ending
        for match in reversed(list(self.SENTENCE_END.finditer(window))):
            return window_start + match.end()

        # Fall back to clause boundary
        for match in reversed(list(self.CLAUSE_END.finditer(window))):
            return window_start + match.end()

        # No good break point found, use target
        return target

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into fixed-size chunks with overlap."""
        if not text:
            return []

        chunks = []
        text_len = len(text)
        start = 0

        while start < text_len:
            # Calculate end position
            end = min(start + self.chunk_size, text_len)

            # Find optimal break point if not at end
            if end < text_len:
                end = self._find_break_point(text, end)

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    start_char=start,
                    end_char=end,
                ))

            # Move start position with overlap
            if end >= text_len:
                break
            start = end - self.chunk_overlap
            if start <= chunks[-1].start_char if chunks else 0:
                start = end  # Avoid infinite loop

        return chunks


class SemanticChunker(BaseChunker):
    """
    Semantic chunker optimized for Japanese text.

    Uses morphological analysis to identify:
    - Topic boundaries (は, が particles after nouns)
    - Paragraph structure
    - Content density variations

    This produces more coherent chunks for RAG retrieval.
    """

    # Strong boundary markers
    PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
    HEADING_PATTERN = re.compile(r"^[#＃]+\s*|^[■□●○◆◇▪▫]+")

    def __init__(
        self,
        tokenizer: BaseTokenizer | None = None,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000,
        similarity_threshold: float = 0.5,
    ):
        """
        Initialize semantic chunker.

        Args:
            tokenizer: Tokenizer instance (defaults to SimpleTokenizer)
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            similarity_threshold: Threshold for semantic similarity (0-1)
        """
        self.tokenizer = tokenizer or SimpleTokenizer()
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.similarity_threshold = similarity_threshold

    def _split_paragraphs(self, text: str) -> list[tuple[str, int]]:
        """Split text into paragraphs with their start positions."""
        paragraphs = []
        pos = 0

        for part in self.PARAGRAPH_BREAK.split(text):
            if part.strip():
                paragraphs.append((part.strip(), pos))
            pos += len(part) + 2  # Account for \n\n

        return paragraphs

    def _calculate_content_density(self, tokens: list[Token]) -> float:
        """Calculate ratio of content words to total tokens."""
        if not tokens:
            return 0.0
        content_count = sum(1 for t in tokens if t.is_content_word)
        return content_count / len(tokens)

    def _find_topic_boundaries(self, tokens: list[Token]) -> list[int]:
        """
        Find potential topic boundaries in tokenized text.

        Japanese topic markers (は, が after nouns) often indicate
        new topics or subtopics.
        """
        boundaries = []

        for i, token in enumerate(tokens):
            # Look for topic markers
            if token.surface in ("は", "が") and i > 0:
                prev = tokens[i - 1]
                if prev.token_type == TokenType.NOUN:
                    boundaries.append(i + 1)

            # Sentence endings are always boundaries
            if token.token_type == TokenType.PUNCTUATION and "。" in token.surface:
                boundaries.append(i + 1)

        return boundaries

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into semantic chunks."""
        if not text:
            return []

        chunks = []

        # First, split by paragraphs
        paragraphs = self._split_paragraphs(text)

        for para_text, para_start in paragraphs:
            # If paragraph is small enough, keep as single chunk
            if len(para_text) <= self.max_chunk_size:
                if len(para_text) >= self.min_chunk_size:
                    tokens = self.tokenizer.tokenize(para_text)
                    chunks.append(Chunk(
                        text=para_text,
                        start_char=para_start,
                        end_char=para_start + len(para_text),
                        token_count=len(tokens),
                    ))
                continue

            # For larger paragraphs, use semantic splitting
            tokens = self.tokenizer.tokenize(para_text)
            boundaries = self._find_topic_boundaries(tokens)

            # Convert token boundaries to character positions
            char_positions = []
            pos = 0
            for token in tokens:
                idx = para_text.find(token.surface, pos)
                if idx >= 0:
                    char_positions.append(idx)
                    pos = idx + len(token.surface)
                else:
                    char_positions.append(pos)

            # Build chunks from boundaries
            chunk_start = 0
            current_size = 0

            for boundary_idx in boundaries:
                if boundary_idx >= len(char_positions):
                    continue

                boundary_pos = char_positions[boundary_idx] if boundary_idx < len(char_positions) else len(para_text)
                segment_size = boundary_pos - chunk_start

                # Check if we should create a chunk
                if current_size + segment_size > self.max_chunk_size and current_size >= self.min_chunk_size:
                    # Create chunk up to current position
                    chunk_text = para_text[chunk_start:chunk_start + current_size].strip()
                    if chunk_text:
                        chunks.append(Chunk(
                            text=chunk_text,
                            start_char=para_start + chunk_start,
                            end_char=para_start + chunk_start + current_size,
                        ))
                    chunk_start = chunk_start + current_size
                    current_size = segment_size
                else:
                    current_size = boundary_pos - chunk_start

            # Don't forget the last chunk
            if current_size > 0:
                chunk_text = para_text[chunk_start:].strip()
                if chunk_text and len(chunk_text) >= self.min_chunk_size // 2:
                    chunks.append(Chunk(
                        text=chunk_text,
                        start_char=para_start + chunk_start,
                        end_char=para_start + len(para_text),
                    ))

        # Merge small trailing chunks
        return self._merge_small_chunks(chunks)

    def _merge_small_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Merge chunks that are too small."""
        if len(chunks) <= 1:
            return chunks

        merged = []
        current = chunks[0]

        for next_chunk in chunks[1:]:
            combined_size = current.char_count + next_chunk.char_count

            if current.char_count < self.min_chunk_size and combined_size <= self.max_chunk_size:
                # Merge with next
                current = Chunk(
                    text=current.text + "\n" + next_chunk.text,
                    start_char=current.start_char,
                    end_char=next_chunk.end_char,
                )
            else:
                merged.append(current)
                current = next_chunk

        merged.append(current)
        return merged


class RecursiveChunker(BaseChunker):
    """
    Recursive chunker that splits by document hierarchy.

    Splitting order:
    1. Headings / section breaks
    2. Paragraphs (double newline)
    3. Sentences (。！？)
    4. Clauses (、)
    5. Characters (last resort)
    """

    # Separators in order of precedence
    SEPARATORS = [
        (re.compile(r"\n(?=[#＃■□●○◆◇▪▫]|\d+\.)"), "heading"),      # Before headings
        (re.compile(r"\n\s*\n"), "paragraph"),                          # Paragraphs
        (re.compile(r"(?<=[。！？!?])\s*"), "sentence"),                # Sentences
        (re.compile(r"(?<=[、，,])\s*"), "clause"),                     # Clauses
    ]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[tuple[re.Pattern, str]] | None = None,
    ):
        """
        Initialize recursive chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            separators: Custom separator patterns (optional)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.SEPARATORS

    def _split_text(
        self,
        text: str,
        separator_idx: int = 0,
    ) -> list[str]:
        """Recursively split text using separator hierarchy."""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        if separator_idx >= len(self.separators):
            # Last resort: character split
            return self._character_split(text)

        pattern, _ = self.separators[separator_idx]
        parts = pattern.split(text)

        # Filter empty parts
        parts = [p for p in parts if p.strip()]

        if len(parts) <= 1:
            # Separator didn't help, try next level
            return self._split_text(text, separator_idx + 1)

        # Recursively process parts that are still too large
        result = []
        for part in parts:
            if len(part) > self.chunk_size:
                result.extend(self._split_text(part, separator_idx + 1))
            else:
                result.append(part)

        return result

    def _character_split(self, text: str) -> list[str]:
        """Split by characters as last resort."""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def chunk(self, text: str) -> list[Chunk]:
        """Split text recursively by document structure."""
        if not text:
            return []

        parts = self._split_text(text.strip())

        # Merge small consecutive parts
        merged = []
        current = ""
        current_start = 0

        for part in parts:
            if len(current) + len(part) <= self.chunk_size:
                if current:
                    current += "\n" + part
                else:
                    current = part
            else:
                if current:
                    merged.append((current, current_start))
                current = part
                current_start = text.find(part)

        if current:
            merged.append((current, current_start))

        # Create Chunk objects with overlap
        chunks = []
        for i, (chunk_text, start) in enumerate(merged):
            # Add overlap from previous chunk
            if i > 0 and self.chunk_overlap > 0:
                prev_text = merged[i - 1][0]
                overlap = prev_text[-self.chunk_overlap:]
                chunk_text = overlap + chunk_text

            chunks.append(Chunk(
                text=chunk_text.strip(),
                start_char=max(0, start - self.chunk_overlap) if i > 0 else start,
                end_char=start + len(chunk_text),
            ))

        return chunks


# Convenience function
def chunk_text(
    text: str,
    strategy: str = "semantic",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    tokenizer_backend: str = "simple",
    **kwargs,
) -> list[Chunk]:
    """
    Convenience function to chunk Japanese text.

    Args:
        text: Text to chunk
        strategy: "fixed", "semantic", or "recursive"
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        tokenizer_backend: "simple", "mecab", or "sudachi"
        **kwargs: Additional arguments for the chunker

    Returns:
        List of Chunk objects

    Example:
        >>> chunks = chunk_text("日本語のテキストです。", strategy="semantic")
        >>> for chunk in chunks:
        ...     print(chunk.text)
    """
    from .tokenizer import get_tokenizer

    chunkers = {
        "fixed": lambda: FixedSizeChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        ),
        "semantic": lambda: SemanticChunker(
            tokenizer=get_tokenizer(tokenizer_backend),
            max_chunk_size=chunk_size,
            **kwargs,
        ),
        "recursive": lambda: RecursiveChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        ),
    }

    if strategy not in chunkers:
        raise ValueError(f"Unknown strategy: {strategy}. Choose from {list(chunkers.keys())}")

    return chunkers[strategy]().chunk(text)
