"""
FastText wrapper for BabelVec.

Provides a clean interface to FastText models with additional functionality.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

try:
    import fasttext
except ImportError:
    fasttext = None


class FastTextWrapper:
    """
    Wrapper around FastText models with enhanced functionality.

    Handles model loading, saving, and provides consistent interface
    for word vector operations.
    """

    def __init__(self, model: Optional["fasttext.FastText._FastText"] = None):
        """
        Initialize wrapper with optional pre-loaded model.

        Args:
            model: Pre-loaded FastText model
        """
        if fasttext is None:
            raise ImportError(
                "fasttext is required for BabelVec. Install with: pip install fasttext"
            )
        self._model = model
        self._projection_matrix: Optional[np.ndarray] = None

    @property
    def dim(self) -> int:
        """Get embedding dimension."""
        if self._model is None:
            raise ValueError("No model loaded")
        return self._model.get_dimension()

    @property
    def words(self) -> List[str]:
        """Get vocabulary words."""
        if self._model is None:
            raise ValueError("No model loaded")
        return self._model.get_words()

    @property
    def vocab_size(self) -> int:
        """Get vocabulary size."""
        return len(self.words)

    def get_word_vector(self, word: str) -> np.ndarray:
        """
        Get vector for a word.

        Args:
            word: Word to get vector for

        Returns:
            Word vector of shape (dim,)
        """
        if self._model is None:
            raise ValueError("No model loaded")

        vec = self._model.get_word_vector(word)

        # Apply projection if set (for alignment)
        if self._projection_matrix is not None:
            vec = vec @ self._projection_matrix

        return vec

    def get_word_vectors(self, words: List[str]) -> np.ndarray:
        """
        Get vectors for multiple words.

        Args:
            words: List of words

        Returns:
            Array of shape (n_words, dim)
        """
        return np.array([self.get_word_vector(w) for w in words])

    def get_sentence_vector(self, sentence: str) -> np.ndarray:
        """
        Get FastText's native sentence vector (simple average).

        Args:
            sentence: Input sentence

        Returns:
            Sentence vector of shape (dim,)
        """
        if self._model is None:
            raise ValueError("No model loaded")

        vec = self._model.get_sentence_vector(sentence)

        if self._projection_matrix is not None:
            vec = vec @ self._projection_matrix

        return vec

    def get_nearest_neighbors(
        self, word: str, k: int = 10
    ) -> List[tuple[float, str]]:
        """
        Get k nearest neighbors for a word.

        Args:
            word: Query word
            k: Number of neighbors

        Returns:
            List of (similarity, word) tuples
        """
        if self._model is None:
            raise ValueError("No model loaded")
        return self._model.get_nearest_neighbors(word, k)

    def set_projection(self, matrix: np.ndarray) -> None:
        """
        Set projection matrix for alignment.

        Args:
            matrix: Projection matrix of shape (dim, dim)
        """
        if matrix.shape != (self.dim, self.dim):
            raise ValueError(f"Projection matrix must be ({self.dim}, {self.dim})")
        self._projection_matrix = matrix.copy()

    def clear_projection(self) -> None:
        """Remove projection matrix."""
        self._projection_matrix = None

    @classmethod
    def load(cls, path: Union[str, Path]) -> "FastTextWrapper":
        """
        Load FastText model from file.

        Args:
            path: Path to .bin model file

        Returns:
            FastTextWrapper instance
        """
        if fasttext is None:
            raise ImportError("fasttext is required")

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        model = fasttext.load_model(str(path))
        return cls(model)

    def save(self, path: Union[str, Path]) -> None:
        """
        Save model to file.

        Args:
            path: Output path (.bin)
        """
        if self._model is None:
            raise ValueError("No model to save")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._model.save_model(str(path))

    @classmethod
    def train(
        cls,
        corpus_path: Union[str, Path],
        dim: int = 300,
        epochs: int = 5,
        lr: float = 0.05,
        min_count: int = 5,
        word_ngrams: int = 1,
        minn: int = 3,
        maxn: int = 6,
        ws: int = 5,
        neg: int = 5,
        model_type: str = "skipgram",
        loss: str = "ns",
        bucket: int = 2000000,
        thread: int = None,
        verbose: int = 1,
    ) -> "FastTextWrapper":
        """
        Train a new FastText model.

        Args:
            corpus_path: Path to training corpus (one sentence per line)
            dim: Embedding dimension
            epochs: Number of training epochs
            lr: Learning rate
            min_count: Minimum word frequency
            word_ngrams: Max word n-gram length
            minn: Min character n-gram length
            maxn: Max character n-gram length
            ws: Context window size
            neg: Number of negative samples
            model_type: 'skipgram' or 'cbow'
            loss: Loss function ('ns', 'hs', 'softmax')
            bucket: Number of hash buckets for subwords
            thread: Number of threads (None = auto-detect)
            verbose: Verbosity level

        Returns:
            Trained FastTextWrapper
        """
        if fasttext is None:
            raise ImportError("fasttext is required")

        corpus_path = Path(corpus_path)
        if not corpus_path.exists():
            raise FileNotFoundError(f"Corpus not found: {corpus_path}")

        # Auto-detect thread count if not specified
        if thread is None:
            thread = os.cpu_count() or 4
        
        if verbose >= 1:
            print(f"Training FastText with {thread} threads...")

        model = fasttext.train_unsupervised(
            str(corpus_path),
            model=model_type,
            dim=dim,
            epoch=epochs,
            lr=lr,
            minCount=min_count,
            wordNgrams=word_ngrams,
            minn=minn,
            maxn=maxn,
            ws=ws,
            neg=neg,
            loss=loss,
            bucket=bucket,
            thread=thread,
            verbose=verbose,
        )

        return cls(model)

    def export_vectors(self, path: Union[str, Path], binary: bool = False) -> None:
        """
        Export word vectors to .vec format.

        Args:
            path: Output path
            binary: If True, save in binary format
        """
        if self._model is None:
            raise ValueError("No model loaded")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        words = self.words
        dim = self.dim

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{len(words)} {dim}\n")
            for word in words:
                vec = self.get_word_vector(word)
                vec_str = " ".join(f"{v:.6f}" for v in vec)
                f.write(f"{word} {vec_str}\n")

    def get_embedding_matrix(self, words: Optional[List[str]] = None) -> np.ndarray:
        """
        Get embedding matrix for vocabulary or specified words.

        Args:
            words: Optional list of words. If None, uses full vocabulary.

        Returns:
            Embedding matrix of shape (n_words, dim)
        """
        if words is None:
            words = self.words
        return self.get_word_vectors(words)

    def __contains__(self, word: str) -> bool:
        """Check if word is in vocabulary."""
        return word in self.words

    def __len__(self) -> int:
        """Get vocabulary size."""
        return self.vocab_size

    def __repr__(self) -> str:
        if self._model is None:
            return "FastTextWrapper(no model loaded)"
        return f"FastTextWrapper(vocab_size={self.vocab_size}, dim={self.dim})"
