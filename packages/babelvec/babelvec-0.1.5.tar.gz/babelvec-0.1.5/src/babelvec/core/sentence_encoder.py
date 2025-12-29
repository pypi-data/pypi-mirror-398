"""
Position-aware sentence encoder.

Combines word embeddings with positional encoding for order-sensitive
sentence representations.
"""

from typing import Callable, List, Optional, Union

import numpy as np

from babelvec.core.positional_encoding import (
    PositionalEncoding,
    RoPEEncoding,
    SinusoidalEncoding,
    DecayEncoding,
    get_positional_encoding,
)


class SentenceEncoder:
    """
    Position-aware sentence encoder.

    Encodes sentences by combining word embeddings with positional information,
    making the resulting sentence vectors sensitive to word order.
    """

    def __init__(
        self,
        dim: int,
        method: str = "rope",
        max_seq_len: int = 512,
        normalize: bool = True,
        **kwargs,
    ):
        """
        Initialize sentence encoder.

        Args:
            dim: Embedding dimension
            method: Positional encoding method ('rope', 'sinusoidal', 'decay', 'average')
            max_seq_len: Maximum sequence length
            normalize: Whether to L2-normalize output vectors
            **kwargs: Additional arguments for positional encoding
        """
        self.dim = dim
        self.method = method
        self.max_seq_len = max_seq_len
        self.normalize = normalize

        self._pos_encoder = get_positional_encoding(method, dim, max_seq_len, **kwargs)

    def encode(
        self,
        word_vectors: np.ndarray,
        pooling: str = "mean",
    ) -> np.ndarray:
        """
        Encode word vectors into a sentence vector.

        Args:
            word_vectors: Word embeddings of shape (seq_len, dim)
            pooling: Pooling strategy ('mean', 'max', 'first', 'last')

        Returns:
            Sentence vector of shape (dim,)
        """
        if word_vectors.ndim == 1:
            word_vectors = word_vectors[np.newaxis, :]

        if len(word_vectors) == 0:
            return np.zeros(self.dim)

        # Apply positional encoding if not using simple average
        if self._pos_encoder is not None:
            encoded = self._pos_encoder.encode(word_vectors)
        else:
            encoded = word_vectors

        # Pool to single vector
        if pooling == "mean":
            sentence_vec = np.mean(encoded, axis=0)
        elif pooling == "max":
            sentence_vec = np.max(encoded, axis=0)
        elif pooling == "first":
            sentence_vec = encoded[0]
        elif pooling == "last":
            sentence_vec = encoded[-1]
        elif pooling == "sum":
            sentence_vec = np.sum(encoded, axis=0)
        else:
            raise ValueError(f"Unknown pooling method: {pooling}")

        # Normalize if requested
        if self.normalize:
            norm = np.linalg.norm(sentence_vec)
            if norm > 0:
                sentence_vec = sentence_vec / norm

        return sentence_vec

    def encode_batch(
        self,
        batch_word_vectors: List[np.ndarray],
        pooling: str = "mean",
    ) -> np.ndarray:
        """
        Encode a batch of sentences.

        Args:
            batch_word_vectors: List of word embedding arrays
            pooling: Pooling strategy

        Returns:
            Sentence vectors of shape (batch_size, dim)
        """
        return np.array([self.encode(wv, pooling) for wv in batch_word_vectors])

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
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

    def __repr__(self) -> str:
        return (
            f"SentenceEncoder(dim={self.dim}, method='{self.method}', "
            f"normalize={self.normalize})"
        )


class MultiMethodEncoder:
    """
    Encoder that supports multiple positional encoding methods.

    Useful for comparing different encoding strategies on the same input.
    """

    def __init__(self, dim: int, max_seq_len: int = 512, normalize: bool = True):
        """
        Initialize multi-method encoder.

        Args:
            dim: Embedding dimension
            max_seq_len: Maximum sequence length
            normalize: Whether to normalize outputs
        """
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.normalize = normalize

        # Create encoders for each method
        self._encoders = {
            "average": SentenceEncoder(dim, "average", max_seq_len, normalize),
            "rope": SentenceEncoder(dim, "rope", max_seq_len, normalize),
            "sinusoidal": SentenceEncoder(dim, "sinusoidal", max_seq_len, normalize),
            "decay": SentenceEncoder(dim, "decay", max_seq_len, normalize),
        }

    def encode(
        self,
        word_vectors: np.ndarray,
        method: str = "rope",
        pooling: str = "mean",
    ) -> np.ndarray:
        """
        Encode using specified method.

        Args:
            word_vectors: Word embeddings
            method: Encoding method
            pooling: Pooling strategy

        Returns:
            Sentence vector
        """
        if method not in self._encoders:
            raise ValueError(f"Unknown method: {method}. Available: {list(self._encoders.keys())}")
        return self._encoders[method].encode(word_vectors, pooling)

    def encode_all_methods(
        self,
        word_vectors: np.ndarray,
        pooling: str = "mean",
    ) -> dict[str, np.ndarray]:
        """
        Encode using all available methods.

        Args:
            word_vectors: Word embeddings
            pooling: Pooling strategy

        Returns:
            Dict mapping method name to sentence vector
        """
        return {
            method: encoder.encode(word_vectors, pooling)
            for method, encoder in self._encoders.items()
        }

    def compare_methods(
        self,
        word_vectors1: np.ndarray,
        word_vectors2: np.ndarray,
        pooling: str = "mean",
    ) -> dict[str, float]:
        """
        Compare similarity scores across all methods.

        Args:
            word_vectors1: First sentence word embeddings
            word_vectors2: Second sentence word embeddings
            pooling: Pooling strategy

        Returns:
            Dict mapping method name to similarity score
        """
        results = {}
        for method, encoder in self._encoders.items():
            vec1 = encoder.encode(word_vectors1, pooling)
            vec2 = encoder.encode(word_vectors2, pooling)
            results[method] = encoder.similarity(vec1, vec2)
        return results

    @property
    def methods(self) -> List[str]:
        """Get available encoding methods."""
        return list(self._encoders.keys())

    def __repr__(self) -> str:
        return f"MultiMethodEncoder(dim={self.dim}, methods={self.methods})"
