"""InfoNCE contrastive alignment for cross-lingual embeddings."""

from typing import Dict, List, Optional, Tuple

import numpy as np

from babelvec.core.model import BabelVec
from babelvec.training.alignment.base import BaseAligner


class InfoNCEAligner(BaseAligner):
    """
    InfoNCE contrastive alignment for cross-lingual embeddings.

    Uses contrastive learning to fine-tune alignment by pulling
    parallel sentences together and pushing non-parallel apart.

    Reference: Oord et al., 2018 - "Representation Learning with Contrastive Predictive Coding"
    """

    def __init__(
        self,
        reference_lang: Optional[str] = None,
        epochs: int = 3,
        batch_size: int = 32,
        lr: float = 0.001,
        temperature: float = 0.07,
    ):
        """
        Initialize InfoNCE aligner.

        Args:
            reference_lang: Reference language
            epochs: Number of training epochs (keep low for "light" alignment)
            batch_size: Batch size for training
            lr: Learning rate
            temperature: Temperature for softmax
        """
        super().__init__(reference_lang)
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.temperature = temperature

    def compute_projections(
        self,
        models: Dict[str, BabelVec],
        parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    ) -> Dict[str, np.ndarray]:
        """
        Compute InfoNCE-optimized projection matrices.

        Args:
            models: Dict mapping language code to BabelVec model
            parallel_data: Dict mapping (lang1, lang2) to parallel sentences

        Returns:
            Dict mapping language code to projection matrix
        """
        languages = list(models.keys())
        ref_lang = self._get_reference_lang(languages)
        dim = models[ref_lang].dim

        # Initialize with identity matrices
        projections = {lang: np.eye(dim) for lang in languages}

        # Train projections for each non-reference language
        for lang in languages:
            if lang == ref_lang:
                continue

            parallel_pairs = self._find_parallel_pairs(lang, ref_lang, parallel_data)
            if not parallel_pairs:
                continue

            # Get embeddings
            src_vecs, tgt_vecs = self._get_parallel_vectors(
                models[lang], models[ref_lang], parallel_pairs
            )

            # Train projection with InfoNCE
            projection = self._train_infonce(src_vecs, tgt_vecs, dim)
            projections[lang] = projection

        return projections

    def _find_parallel_pairs(
        self,
        lang1: str,
        lang2: str,
        parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    ) -> List[Tuple[str, str]]:
        """Find parallel pairs for a language pair."""
        if (lang1, lang2) in parallel_data:
            return parallel_data[(lang1, lang2)]
        elif (lang2, lang1) in parallel_data:
            return [(s2, s1) for s1, s2 in parallel_data[(lang2, lang1)]]
        return []

    def _train_infonce(
        self,
        source: np.ndarray,
        target: np.ndarray,
        dim: int,
    ) -> np.ndarray:
        """
        Train projection matrix using InfoNCE loss.

        Args:
            source: Source embeddings (n_samples, dim)
            target: Target embeddings (n_samples, dim)
            dim: Embedding dimension

        Returns:
            Learned projection matrix
        """
        n_samples = len(source)

        # Initialize projection as identity
        W = np.eye(dim)

        for epoch in range(self.epochs):
            # Shuffle data
            indices = np.random.permutation(n_samples)
            source_shuffled = source[indices]
            target_shuffled = target[indices]

            total_loss = 0.0
            n_batches = 0

            for i in range(0, n_samples, self.batch_size):
                batch_src = source_shuffled[i : i + self.batch_size]
                batch_tgt = target_shuffled[i : i + self.batch_size]

                if len(batch_src) < 2:
                    continue

                # Forward pass: project source
                projected = batch_src @ W

                # Normalize
                projected = projected / (np.linalg.norm(projected, axis=1, keepdims=True) + 1e-8)
                batch_tgt_norm = batch_tgt / (np.linalg.norm(batch_tgt, axis=1, keepdims=True) + 1e-8)

                # Compute similarity matrix
                sim_matrix = (projected @ batch_tgt_norm.T) / self.temperature

                # InfoNCE loss: -log(exp(sim_ii) / sum_j(exp(sim_ij)))
                # Positive pairs are on diagonal
                batch_size_actual = len(batch_src)
                labels = np.arange(batch_size_actual)

                # Softmax and cross-entropy
                exp_sim = np.exp(sim_matrix - sim_matrix.max(axis=1, keepdims=True))
                softmax = exp_sim / exp_sim.sum(axis=1, keepdims=True)

                loss = -np.log(softmax[np.arange(batch_size_actual), labels] + 1e-8).mean()
                total_loss += loss

                # Gradient computation (simplified)
                # d_loss/d_W = d_loss/d_projected * d_projected/d_W
                grad_softmax = softmax.copy()
                grad_softmax[np.arange(batch_size_actual), labels] -= 1
                grad_softmax /= batch_size_actual

                # Gradient w.r.t. projected (before normalization)
                grad_projected = (grad_softmax @ batch_tgt_norm) / self.temperature

                # Gradient w.r.t. W
                grad_W = batch_src.T @ grad_projected

                # Update W
                W -= self.lr * grad_W

                # Re-orthogonalize to keep as rotation
                U, _, Vt = np.linalg.svd(W)
                W = U @ Vt

                n_batches += 1

        return W

    def align_pair(
        self,
        source_model: BabelVec,
        target_model: BabelVec,
        parallel_pairs: List[Tuple[str, str]],
    ) -> np.ndarray:
        """
        Compute InfoNCE alignment for a single language pair.

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
        return self._train_infonce(src_vecs, tgt_vecs, source_model.dim)
