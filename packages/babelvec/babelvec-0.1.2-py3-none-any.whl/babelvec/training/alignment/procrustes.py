"""Procrustes alignment for cross-lingual embeddings."""

from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.linalg import orthogonal_procrustes

from babelvec.core.model import BabelVec
from babelvec.training.alignment.base import BaseAligner


class ProcrustesAligner(BaseAligner):
    """
    Procrustes alignment for cross-lingual embeddings.

    Finds the optimal orthogonal transformation to align embedding spaces
    using parallel data (e.g., word translations or parallel sentences).

    Reference: Schönemann, 1966 - "A generalized solution of the orthogonal Procrustes problem"
    """

    def __init__(
        self,
        reference_lang: Optional[str] = None,
        normalize: bool = True,
        center: bool = True,
    ):
        """
        Initialize Procrustes aligner.

        Args:
            reference_lang: Reference language (target space)
            normalize: Whether to L2-normalize vectors before alignment
            center: Whether to center vectors before alignment
        """
        super().__init__(reference_lang)
        self.normalize = normalize
        self.center = center

    def compute_projections(
        self,
        models: Dict[str, BabelVec],
        parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    ) -> Dict[str, np.ndarray]:
        """
        Compute Procrustes projection matrices.

        Args:
            models: Dict mapping language code to BabelVec model
            parallel_data: Dict mapping (lang1, lang2) to parallel sentences

        Returns:
            Dict mapping language code to projection matrix
        """
        languages = list(models.keys())
        ref_lang = self._get_reference_lang(languages)
        dim = models[ref_lang].dim

        # Reference language gets identity projection
        projections = {ref_lang: np.eye(dim)}

        # Align each other language to reference
        for lang in languages:
            if lang == ref_lang:
                continue

            # Find parallel data involving this language pair
            parallel_pairs = self._find_parallel_pairs(
                lang, ref_lang, parallel_data
            )

            if not parallel_pairs:
                # No parallel data - use identity
                projections[lang] = np.eye(dim)
                continue

            # Get embedding matrices
            src_vecs, tgt_vecs = self._get_parallel_vectors(
                models[lang], models[ref_lang], parallel_pairs
            )

            # Compute Procrustes alignment
            projection = self._compute_procrustes(src_vecs, tgt_vecs)
            projections[lang] = projection

        return projections

    def _find_parallel_pairs(
        self,
        lang1: str,
        lang2: str,
        parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    ) -> List[Tuple[str, str]]:
        """Find parallel pairs for a language pair."""
        # Try both orderings
        if (lang1, lang2) in parallel_data:
            return parallel_data[(lang1, lang2)]
        elif (lang2, lang1) in parallel_data:
            # Swap order
            return [(s2, s1) for s1, s2 in parallel_data[(lang2, lang1)]]
        return []

    def _compute_procrustes(
        self,
        source: np.ndarray,
        target: np.ndarray,
    ) -> np.ndarray:
        """
        Compute Procrustes transformation from source to target.

        Args:
            source: Source embeddings (n_samples, dim)
            target: Target embeddings (n_samples, dim)

        Returns:
            Orthogonal projection matrix (dim, dim)
        """
        # Optionally center
        if self.center:
            source = source - source.mean(axis=0)
            target = target - target.mean(axis=0)

        # Optionally normalize
        if self.normalize:
            source_norms = np.linalg.norm(source, axis=1, keepdims=True)
            target_norms = np.linalg.norm(target, axis=1, keepdims=True)
            source = source / np.maximum(source_norms, 1e-8)
            target = target / np.maximum(target_norms, 1e-8)

        # Compute optimal orthogonal transformation
        # Solves: min ||source @ R - target||_F subject to R^T R = I
        R, _ = orthogonal_procrustes(source, target)

        return R

    def align_pair(
        self,
        source_model: BabelVec,
        target_model: BabelVec,
        parallel_pairs: List[Tuple[str, str]],
    ) -> np.ndarray:
        """
        Compute alignment for a single language pair.

        Args:
            source_model: Source language model
            target_model: Target language model
            parallel_pairs: List of (source_sent, target_sent) pairs

        Returns:
            Projection matrix for source language
        """
        src_vecs, tgt_vecs = self._get_parallel_vectors(
            source_model, target_model, parallel_pairs
        )
        return self._compute_procrustes(src_vecs, tgt_vecs)
