"""
Main BabelVec model class.

Combines FastText embeddings with position-aware sentence encoding
and cross-lingual alignment capabilities.
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from babelvec.core.fasttext_wrapper import FastTextWrapper
from babelvec.core.sentence_encoder import SentenceEncoder, MultiMethodEncoder


class BabelVec:
    """
    BabelVec: Position-aware, cross-lingually aligned word embeddings.

    Combines FastText word embeddings with positional encoding for
    order-sensitive sentence representations, and supports cross-lingual
    alignment through projection matrices.

    Example:
        >>> model = BabelVec.load('model.bin')
        >>> vec = model.get_word_vector('hello')
        >>> sent_vec = model.get_sentence_vector('Hello world', method='rope')
    """

    def __init__(
        self,
        fasttext_model: Optional[FastTextWrapper] = None,
        lang: str = "unknown",
        dim: int = 300,
        max_seq_len: int = 512,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize BabelVec model.

        Args:
            fasttext_model: Underlying FastText model
            lang: Language code
            dim: Embedding dimension
            max_seq_len: Maximum sequence length for positional encoding
            metadata: Optional metadata dictionary
        """
        self._ft = fasttext_model
        self.lang = lang
        self._dim = dim
        self.max_seq_len = max_seq_len
        self.metadata = metadata or {}

        # Initialize sentence encoder
        self._encoder = MultiMethodEncoder(dim, max_seq_len, normalize=True)

        # Projection matrix for alignment (None if not aligned)
        self._projection: Optional[np.ndarray] = None

    @property
    def dim(self) -> int:
        """Get embedding dimension."""
        if self._ft is not None:
            return self._ft.dim
        return self._dim

    @property
    def vocab_size(self) -> int:
        """Get vocabulary size."""
        if self._ft is None:
            return 0
        return self._ft.vocab_size

    @property
    def words(self) -> List[str]:
        """Get vocabulary words."""
        if self._ft is None:
            return []
        return self._ft.words

    @property
    def is_aligned(self) -> bool:
        """Check if model has alignment projection."""
        return self._projection is not None

    def get_word_vector(self, word: str) -> np.ndarray:
        """
        Get vector for a word.

        Args:
            word: Word to get vector for

        Returns:
            Word vector of shape (dim,)
        """
        if self._ft is None:
            raise ValueError("No model loaded")
        return self._ft.get_word_vector(word)

    def get_word_vectors(self, words: List[str]) -> np.ndarray:
        """
        Get vectors for multiple words.

        Args:
            words: List of words

        Returns:
            Array of shape (n_words, dim)
        """
        if self._ft is None:
            raise ValueError("No model loaded")
        return self._ft.get_word_vectors(words)

    def tokenize(self, text: str) -> List[str]:
        """
        Simple whitespace tokenization.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        return text.strip().split()

    def get_sentence_vector(
        self,
        sentence: str,
        method: str = "rope",
        pooling: str = "mean",
    ) -> np.ndarray:
        """
        Get position-aware sentence vector.

        Args:
            sentence: Input sentence
            method: Positional encoding method ('rope', 'sinusoidal', 'decay', 'average')
            pooling: Pooling strategy ('mean', 'max', 'first', 'last')

        Returns:
            Sentence vector of shape (dim,)
        """
        if self._ft is None:
            raise ValueError("No model loaded")

        # Tokenize
        tokens = self.tokenize(sentence)
        if not tokens:
            return np.zeros(self.dim)

        # Get word vectors
        word_vectors = self.get_word_vectors(tokens)

        # Encode with positional information
        return self._encoder.encode(word_vectors, method=method, pooling=pooling)

    def get_sentence_vectors(
        self,
        sentences: List[str],
        method: str = "rope",
        pooling: str = "mean",
    ) -> np.ndarray:
        """
        Get sentence vectors for multiple sentences.

        Args:
            sentences: List of sentences
            method: Positional encoding method
            pooling: Pooling strategy

        Returns:
            Array of shape (n_sentences, dim)
        """
        return np.array([
            self.get_sentence_vector(s, method, pooling) for s in sentences
        ])

    def similarity(self, text1: str, text2: str, method: str = "rope") -> float:
        """
        Compute similarity between two texts.

        Args:
            text1: First text
            text2: Second text
            method: Positional encoding method

        Returns:
            Cosine similarity score
        """
        vec1 = self.get_sentence_vector(text1, method)
        vec2 = self.get_sentence_vector(text2, method)
        return self.cosine_similarity(vec1, vec2)

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def most_similar(
        self,
        word: str,
        topn: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Find most similar words.

        Args:
            word: Query word
            topn: Number of results

        Returns:
            List of (word, similarity) tuples
        """
        if self._ft is None:
            raise ValueError("No model loaded")

        neighbors = self._ft.get_nearest_neighbors(word, topn)
        return [(w, s) for s, w in neighbors]

    def set_projection(self, matrix: np.ndarray) -> None:
        """
        Set alignment projection matrix.

        Args:
            matrix: Projection matrix of shape (dim, dim)
        """
        if matrix.shape != (self.dim, self.dim):
            raise ValueError(f"Projection must be ({self.dim}, {self.dim})")
        self._projection = matrix.copy()
        if self._ft is not None:
            self._ft.set_projection(matrix)

    def clear_projection(self) -> None:
        """Remove alignment projection."""
        self._projection = None
        if self._ft is not None:
            self._ft.clear_projection()

    @classmethod
    def load(cls, path: Union[str, Path]) -> "BabelVec":
        """
        Load BabelVec model from file.

        Supports:
        - .bin: FastText binary format
        - .babelvec: Full BabelVec format with metadata

        Args:
            path: Path to model file

        Returns:
            Loaded BabelVec model
        """
        path = Path(path)

        if path.suffix == ".babelvec":
            return cls._load_babelvec(path)
        elif path.suffix == ".bin":
            return cls._load_fasttext(path)
        else:
            # Try FastText format
            return cls._load_fasttext(path)

    @classmethod
    def _load_fasttext(cls, path: Path) -> "BabelVec":
        """Load from FastText .bin file."""
        ft = FastTextWrapper.load(path)

        # Try to infer language from filename
        lang = path.stem.split("_")[0] if "_" in path.stem else "unknown"

        return cls(
            fasttext_model=ft,
            lang=lang,
            dim=ft.dim,
        )

    @classmethod
    def _load_babelvec(cls, path: Path) -> "BabelVec":
        """Load from .babelvec format."""
        with open(path, "rb") as f:
            data = pickle.load(f)

        # Load FastText model if path provided
        ft = None
        if "fasttext_path" in data and data["fasttext_path"]:
            ft_path = path.parent / data["fasttext_path"]
            if ft_path.exists():
                ft = FastTextWrapper.load(ft_path)

        model = cls(
            fasttext_model=ft,
            lang=data.get("lang", "unknown"),
            dim=data.get("dim", 300),
            max_seq_len=data.get("max_seq_len", 512),
            metadata=data.get("metadata", {}),
        )

        # Load projection if present
        if "projection" in data and data["projection"] is not None:
            model.set_projection(data["projection"])

        return model

    def save(self, path: Union[str, Path], save_fasttext: bool = True) -> None:
        """
        Save BabelVec model.

        Args:
            path: Output path (.bin or .babelvec)
            save_fasttext: Whether to save underlying FastText model
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix == ".bin":
            # Save just FastText model
            if self._ft is not None:
                self._ft.save(path)
        else:
            # Save full BabelVec format
            self._save_babelvec(path, save_fasttext)

    def _save_babelvec(self, path: Path, save_fasttext: bool) -> None:
        """Save in .babelvec format."""
        ft_path = None
        if save_fasttext and self._ft is not None:
            ft_path = path.stem + ".bin"
            self._ft.save(path.parent / ft_path)

        data = {
            "lang": self.lang,
            "dim": self.dim,
            "max_seq_len": self.max_seq_len,
            "metadata": self.metadata,
            "projection": self._projection,
            "fasttext_path": ft_path,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

    def export_vectors(self, path: Union[str, Path]) -> None:
        """
        Export word vectors to .vec format.

        Args:
            path: Output path
        """
        if self._ft is None:
            raise ValueError("No model loaded")
        self._ft.export_vectors(path)

    def __contains__(self, word: str) -> bool:
        """Check if word is in vocabulary."""
        if self._ft is None:
            return False
        return word in self._ft

    def __len__(self) -> int:
        """Get vocabulary size."""
        return self.vocab_size

    def __repr__(self) -> str:
        aligned_str = ", aligned" if self.is_aligned else ""
        return f"BabelVec(lang='{self.lang}', dim={self.dim}, vocab={self.vocab_size}{aligned_str})"
