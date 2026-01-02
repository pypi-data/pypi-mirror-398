"""
Japanese tokenizers for semantic chunking.

Provides multiple tokenizer backends:
- SimpleTokenizer: Regex-based, no dependencies (default)
- MeCabTokenizer: MeCab via fugashi (high accuracy)
- SudachiTokenizer: Sudachi (morphological analysis)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Iterator
import re


class TokenType(Enum):
    """Token classification for semantic chunking decisions."""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    PARTICLE = "particle"
    PUNCTUATION = "punctuation"
    SYMBOL = "symbol"
    OTHER = "other"


@dataclass
class Token:
    """Represents a tokenized unit with metadata."""
    surface: str
    token_type: TokenType
    reading: str | None = None
    base_form: str | None = None
    is_content_word: bool = False

    def __str__(self) -> str:
        return self.surface


class BaseTokenizer(ABC):
    """Abstract base class for Japanese tokenizers."""

    @abstractmethod
    def tokenize(self, text: str) -> list[Token]:
        """Tokenize text into a list of Token objects."""
        pass

    def iter_tokens(self, text: str) -> Iterator[Token]:
        """Iterate over tokens (memory efficient for large texts)."""
        yield from self.tokenize(text)


class SimpleTokenizer(BaseTokenizer):
    """
    Regex-based Japanese tokenizer with no external dependencies.

    Uses character class patterns to identify:
    - Kanji compounds
    - Hiragana sequences (particles, verb endings)
    - Katakana words (loanwords, emphasis)
    - ASCII words
    - Punctuation
    """

    # Japanese punctuation that indicates sentence/clause boundaries
    SENTENCE_ENDINGS = set("。！？!?")
    CLAUSE_BREAKS = set("、，,")
    QUOTE_MARKS = set("「」『』（）()【】")

    # Regex patterns for Japanese text
    PATTERNS = [
        # Kanji + okurigana (e.g., 食べる, 美しい)
        (r"[\u4e00-\u9fff]+[\u3040-\u309f]*", TokenType.NOUN),
        # Pure hiragana (particles, auxiliaries)
        (r"[\u3040-\u309f]+", TokenType.PARTICLE),
        # Katakana (loanwords)
        (r"[\u30a0-\u30ff]+", TokenType.NOUN),
        # ASCII words
        (r"[a-zA-Z][a-zA-Z0-9]*", TokenType.NOUN),
        # Numbers
        (r"[0-9]+(?:\.[0-9]+)?", TokenType.OTHER),
        # Punctuation
        (r"[。、！？!?,，.]+", TokenType.PUNCTUATION),
        # Other symbols
        (r"[^\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fffa-zA-Z0-9。、！？!?,，.]+", TokenType.SYMBOL),
    ]

    # Common particles (助詞) - these are not content words
    PARTICLES = {
        "は", "が", "を", "に", "へ", "で", "と", "も", "や", "の",
        "から", "まで", "より", "ほど", "など", "か", "ね", "よ", "わ",
        "さ", "ぞ", "な", "け", "っけ", "かな", "だけ", "しか", "ばかり",
        "くらい", "ぐらい", "など", "なんか", "って", "とか",
    }

    # Common auxiliary verbs and endings
    AUXILIARIES = {
        "です", "ます", "でした", "ました", "ません", "ない", "なかった",
        "れる", "られる", "せる", "させる", "たい", "たがる",
        "そう", "よう", "らしい", "みたい", "っぽい",
    }

    def __init__(self):
        # Compile patterns for efficiency
        self._compiled = [
            (re.compile(pattern), token_type)
            for pattern, token_type in self.PATTERNS
        ]
        self._combined = re.compile(
            "|".join(f"({p})" for p, _ in self.PATTERNS)
        )

    def tokenize(self, text: str) -> list[Token]:
        """Tokenize Japanese text using regex patterns."""
        tokens = []

        for match in self._combined.finditer(text):
            surface = match.group()

            # Determine token type based on which group matched
            token_type = TokenType.OTHER
            for i, (_, tt) in enumerate(self.PATTERNS):
                if match.group(i + 1):
                    token_type = tt
                    break

            # Check if it's a particle
            if surface in self.PARTICLES:
                token_type = TokenType.PARTICLE

            # Determine if content word
            is_content = token_type in (TokenType.NOUN, TokenType.VERB, TokenType.ADJECTIVE)
            if surface in self.PARTICLES or surface in self.AUXILIARIES:
                is_content = False

            tokens.append(Token(
                surface=surface,
                token_type=token_type,
                is_content_word=is_content,
            ))

        return tokens


class MeCabTokenizer(BaseTokenizer):
    """
    MeCab-based tokenizer using fugashi.

    Requires: pip install bunsetsu[mecab]
    """

    # POS tag mapping to TokenType
    POS_MAP = {
        "名詞": TokenType.NOUN,
        "動詞": TokenType.VERB,
        "形容詞": TokenType.ADJECTIVE,
        "助詞": TokenType.PARTICLE,
        "記号": TokenType.PUNCTUATION,
        "補助記号": TokenType.PUNCTUATION,
    }

    # Content word POS tags
    CONTENT_POS = {"名詞", "動詞", "形容詞", "副詞"}

    def __init__(self):
        try:
            import fugashi
        except ImportError:
            raise ImportError(
                "MeCabTokenizer requires fugashi. "
                "Install with: pip install bunsetsu[mecab]"
            )
        self._tagger = fugashi.Tagger()

    def tokenize(self, text: str) -> list[Token]:
        """Tokenize using MeCab morphological analysis."""
        tokens = []

        for word in self._tagger(text):
            surface = word.surface
            # Get POS information
            pos = word.feature.pos1 if hasattr(word.feature, "pos1") else "その他"
            reading = getattr(word.feature, "kana", None)
            base = getattr(word.feature, "lemma", surface)

            token_type = self.POS_MAP.get(pos, TokenType.OTHER)
            is_content = pos in self.CONTENT_POS

            tokens.append(Token(
                surface=surface,
                token_type=token_type,
                reading=reading,
                base_form=base,
                is_content_word=is_content,
            ))

        return tokens


class SudachiTokenizer(BaseTokenizer):
    """
    Sudachi-based tokenizer.

    Requires: pip install bunsetsu[sudachi]

    Sudachi provides three tokenization modes:
    - A: Short unit (最短)
    - B: Middle unit (中間)
    - C: Long unit (最長) - default for semantic chunking
    """

    POS_MAP = {
        "名詞": TokenType.NOUN,
        "動詞": TokenType.VERB,
        "形容詞": TokenType.ADJECTIVE,
        "助詞": TokenType.PARTICLE,
        "補助記号": TokenType.PUNCTUATION,
    }

    CONTENT_POS = {"名詞", "動詞", "形容詞", "副詞"}

    def __init__(self, mode: str = "C"):
        """
        Initialize Sudachi tokenizer.

        Args:
            mode: Tokenization mode - "A" (short), "B" (middle), "C" (long)
        """
        try:
            from sudachipy import Dictionary, SplitMode
        except ImportError:
            raise ImportError(
                "SudachiTokenizer requires sudachipy. "
                "Install with: pip install bunsetsu[sudachi]"
            )

        self._dict = Dictionary()
        self._tokenizer = self._dict.create()

        mode_map = {"A": SplitMode.A, "B": SplitMode.B, "C": SplitMode.C}
        self._mode = mode_map.get(mode.upper(), SplitMode.C)

    def tokenize(self, text: str) -> list[Token]:
        """Tokenize using Sudachi morphological analysis."""
        tokens = []

        for morpheme in self._tokenizer.tokenize(text, self._mode):
            surface = morpheme.surface()
            pos = morpheme.part_of_speech()[0]
            reading = morpheme.reading_form()
            base = morpheme.dictionary_form()

            token_type = self.POS_MAP.get(pos, TokenType.OTHER)
            is_content = pos in self.CONTENT_POS

            tokens.append(Token(
                surface=surface,
                token_type=token_type,
                reading=reading,
                base_form=base,
                is_content_word=is_content,
            ))

        return tokens


def get_tokenizer(backend: str = "simple") -> BaseTokenizer:
    """
    Get a tokenizer instance by name.

    Args:
        backend: "simple", "mecab", or "sudachi"

    Returns:
        BaseTokenizer instance
    """
    backends = {
        "simple": SimpleTokenizer,
        "mecab": MeCabTokenizer,
        "sudachi": SudachiTokenizer,
    }

    if backend not in backends:
        raise ValueError(f"Unknown backend: {backend}. Choose from {list(backends.keys())}")

    return backends[backend]()
