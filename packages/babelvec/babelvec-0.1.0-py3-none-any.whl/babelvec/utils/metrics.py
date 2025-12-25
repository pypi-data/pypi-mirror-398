"""Metric utilities for BabelVec."""

import numpy as np
from typing import Union


def cosine_similarity(
    vec1: np.ndarray,
    vec2: np.ndarray,
) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (-1 to 1)
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def euclidean_distance(
    vec1: np.ndarray,
    vec2: np.ndarray,
) -> float:
    """
    Compute Euclidean distance between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Euclidean distance
    """
    return float(np.linalg.norm(vec1 - vec2))


def pairwise_cosine_similarity(
    matrix1: np.ndarray,
    matrix2: np.ndarray,
) -> np.ndarray:
    """
    Compute pairwise cosine similarity between two matrices.

    Args:
        matrix1: First matrix (n, dim)
        matrix2: Second matrix (m, dim)

    Returns:
        Similarity matrix (n, m)
    """
    # Normalize
    norms1 = np.linalg.norm(matrix1, axis=1, keepdims=True)
    norms2 = np.linalg.norm(matrix2, axis=1, keepdims=True)

    matrix1_norm = matrix1 / (norms1 + 1e-8)
    matrix2_norm = matrix2 / (norms2 + 1e-8)

    return matrix1_norm @ matrix2_norm.T


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """
    L2-normalize vectors.

    Args:
        vectors: Input vectors (n, dim) or (dim,)

    Returns:
        Normalized vectors
    """
    if vectors.ndim == 1:
        norm = np.linalg.norm(vectors)
        return vectors / norm if norm > 0 else vectors

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-8)
