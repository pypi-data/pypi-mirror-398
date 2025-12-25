"""
Positional encoding implementations for position-aware embeddings.

Supports:
- RoPE (Rotary Position Embedding)
- Sinusoidal (Transformer-style)
- Decay (Exponential position decay)
"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class PositionalEncoding(ABC):
    """Base class for positional encoding strategies."""

    def __init__(self, dim: int, max_seq_len: int = 512):
        """
        Initialize positional encoding.

        Args:
            dim: Embedding dimension
            max_seq_len: Maximum sequence length to support
        """
        self.dim = dim
        self.max_seq_len = max_seq_len

    @abstractmethod
    def encode(self, embeddings: np.ndarray, positions: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply positional encoding to embeddings.

        Args:
            embeddings: Word embeddings of shape (seq_len, dim)
            positions: Optional position indices. If None, uses 0, 1, 2, ...

        Returns:
            Position-encoded embeddings of shape (seq_len, dim)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(dim={self.dim}, max_seq_len={self.max_seq_len})"


class RoPEEncoding(PositionalEncoding):
    """
    Rotary Position Embedding (RoPE).

    Applies rotation to pairs of dimensions based on position,
    preserving relative position information in dot products.

    Reference: Su et al., 2021 - "RoFormer: Enhanced Transformer with Rotary Position Embedding"
    """

    def __init__(self, dim: int, max_seq_len: int = 512, base: float = 10000.0):
        """
        Initialize RoPE encoding.

        Args:
            dim: Embedding dimension (must be even)
            max_seq_len: Maximum sequence length
            base: Base for frequency computation
        """
        super().__init__(dim, max_seq_len)
        if dim % 2 != 0:
            raise ValueError(f"RoPE requires even dimension, got {dim}")
        self.base = base
        self._precompute_freqs()

    def _precompute_freqs(self) -> None:
        """Precompute frequency bands for efficiency."""
        # Compute inverse frequencies for each dimension pair
        half_dim = self.dim // 2
        freqs = 1.0 / (self.base ** (np.arange(0, half_dim) / half_dim))

        # Compute position * frequency for all positions
        positions = np.arange(self.max_seq_len)
        angles = np.outer(positions, freqs)  # (max_seq_len, half_dim)

        # Precompute sin and cos
        self._sin_cache = np.sin(angles)  # (max_seq_len, half_dim)
        self._cos_cache = np.cos(angles)  # (max_seq_len, half_dim)

    def encode(self, embeddings: np.ndarray, positions: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply RoPE to embeddings.

        Args:
            embeddings: Shape (seq_len, dim) or (dim,) for single vector
            positions: Position indices. If None, uses 0, 1, 2, ...

        Returns:
            Rotated embeddings with same shape as input
        """
        single = embeddings.ndim == 1
        if single:
            embeddings = embeddings[np.newaxis, :]

        seq_len = embeddings.shape[0]

        if positions is None:
            positions = np.arange(seq_len)

        # Get precomputed sin/cos for these positions
        sin = self._sin_cache[positions]  # (seq_len, half_dim)
        cos = self._cos_cache[positions]  # (seq_len, half_dim)

        # Split embeddings into pairs
        x1 = embeddings[:, 0::2]  # Even indices
        x2 = embeddings[:, 1::2]  # Odd indices

        # Apply rotation: [x1, x2] -> [x1*cos - x2*sin, x1*sin + x2*cos]
        rotated = np.empty_like(embeddings)
        rotated[:, 0::2] = x1 * cos - x2 * sin
        rotated[:, 1::2] = x1 * sin + x2 * cos

        return rotated[0] if single else rotated


class SinusoidalEncoding(PositionalEncoding):
    """
    Sinusoidal positional encoding (Transformer-style).

    Adds position-dependent sinusoidal signals to embeddings.

    Reference: Vaswani et al., 2017 - "Attention Is All You Need"
    """

    def __init__(self, dim: int, max_seq_len: int = 512, base: float = 10000.0):
        """
        Initialize sinusoidal encoding.

        Args:
            dim: Embedding dimension
            max_seq_len: Maximum sequence length
            base: Base for frequency computation
        """
        super().__init__(dim, max_seq_len)
        self.base = base
        self._precompute_encodings()

    def _precompute_encodings(self) -> None:
        """Precompute positional encodings for all positions."""
        positions = np.arange(self.max_seq_len)[:, np.newaxis]  # (max_seq_len, 1)
        dims = np.arange(self.dim)[np.newaxis, :]  # (1, dim)

        # Compute angles
        angles = positions / (self.base ** (2 * (dims // 2) / self.dim))

        # Apply sin to even indices, cos to odd indices
        self._encodings = np.zeros((self.max_seq_len, self.dim))
        self._encodings[:, 0::2] = np.sin(angles[:, 0::2])
        self._encodings[:, 1::2] = np.cos(angles[:, 1::2])

    def encode(self, embeddings: np.ndarray, positions: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Add sinusoidal positional encoding to embeddings.

        Args:
            embeddings: Shape (seq_len, dim) or (dim,) for single vector
            positions: Position indices. If None, uses 0, 1, 2, ...

        Returns:
            Embeddings with positional encoding added
        """
        single = embeddings.ndim == 1
        if single:
            embeddings = embeddings[np.newaxis, :]

        seq_len = embeddings.shape[0]

        if positions is None:
            positions = np.arange(seq_len)

        # Add positional encodings
        result = embeddings + self._encodings[positions]

        return result[0] if single else result


class DecayEncoding(PositionalEncoding):
    """
    Exponential decay positional encoding.

    Weights embeddings by exponentially decaying position weights,
    giving more importance to earlier positions.
    """

    def __init__(self, dim: int, max_seq_len: int = 512, decay_rate: float = 0.1):
        """
        Initialize decay encoding.

        Args:
            dim: Embedding dimension
            max_seq_len: Maximum sequence length
            decay_rate: Decay rate (higher = faster decay)
        """
        super().__init__(dim, max_seq_len)
        self.decay_rate = decay_rate
        self._precompute_weights()

    def _precompute_weights(self) -> None:
        """Precompute decay weights for all positions."""
        positions = np.arange(self.max_seq_len)
        self._weights = np.exp(-self.decay_rate * positions)

    def encode(self, embeddings: np.ndarray, positions: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply decay weighting to embeddings.

        Args:
            embeddings: Shape (seq_len, dim) or (dim,) for single vector
            positions: Position indices. If None, uses 0, 1, 2, ...

        Returns:
            Decay-weighted embeddings
        """
        single = embeddings.ndim == 1
        if single:
            embeddings = embeddings[np.newaxis, :]

        seq_len = embeddings.shape[0]

        if positions is None:
            positions = np.arange(seq_len)

        # Apply decay weights
        weights = self._weights[positions][:, np.newaxis]  # (seq_len, 1)
        result = embeddings * weights

        return result[0] if single else result


def get_positional_encoding(
    method: str, dim: int, max_seq_len: int = 512, **kwargs
) -> Optional[PositionalEncoding]:
    """
    Factory function to get positional encoding by name.

    Args:
        method: One of 'rope', 'sinusoidal', 'decay', 'average', 'none'
        dim: Embedding dimension
        max_seq_len: Maximum sequence length
        **kwargs: Additional arguments for specific encodings

    Returns:
        PositionalEncoding instance or None for 'average'/'none'
    """
    method = method.lower()

    if method in ("average", "none", "mean"):
        return None
    elif method == "rope":
        return RoPEEncoding(dim, max_seq_len, base=kwargs.get("base", 10000.0))
    elif method == "sinusoidal":
        return SinusoidalEncoding(dim, max_seq_len, base=kwargs.get("base", 10000.0))
    elif method == "decay":
        return DecayEncoding(dim, max_seq_len, decay_rate=kwargs.get("decay_rate", 0.1))
    else:
        raise ValueError(f"Unknown positional encoding method: {method}")
