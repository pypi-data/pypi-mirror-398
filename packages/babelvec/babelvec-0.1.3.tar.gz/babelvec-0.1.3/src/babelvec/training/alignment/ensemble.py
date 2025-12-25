"""Ensemble alignment combining Procrustes and InfoNCE."""

from typing import Dict, List, Optional, Tuple

import numpy as np

from babelvec.core.model import BabelVec
from babelvec.training.alignment.base import BaseAligner
from babelvec.training.alignment.procrustes import ProcrustesAligner
from babelvec.training.alignment.infonce import InfoNCEAligner


class EnsembleAligner(BaseAligner):
    """
    Ensemble alignment: Procrustes (80%) + Light InfoNCE (20%).

    Combines the strengths of both methods:
    - Procrustes: Fast, captures global structure, proven effective
    - InfoNCE: Fine-grained refinement with contrastive learning

    The ensemble approach provides best of both worlds.
    """

    def __init__(
        self,
        reference_lang: Optional[str] = None,
        procrustes_weight: float = 0.8,
        infonce_weight: float = 0.2,
        infonce_epochs: int = 3,
        infonce_batch_size: int = 32,
        infonce_lr: float = 0.001,
        infonce_temperature: float = 0.07,
    ):
        """
        Initialize ensemble aligner.

        Args:
            reference_lang: Reference language
            procrustes_weight: Weight for Procrustes alignment (default 0.8)
            infonce_weight: Weight for InfoNCE alignment (default 0.2)
            infonce_epochs: Epochs for InfoNCE (keep low - 3 is "light")
            infonce_batch_size: Batch size for InfoNCE
            infonce_lr: Learning rate for InfoNCE
            infonce_temperature: Temperature for InfoNCE softmax
        """
        super().__init__(reference_lang)

        if abs(procrustes_weight + infonce_weight - 1.0) > 1e-6:
            raise ValueError("Weights must sum to 1.0")

        self.procrustes_weight = procrustes_weight
        self.infonce_weight = infonce_weight

        # Initialize component aligners
        self._procrustes = ProcrustesAligner(reference_lang)
        self._infonce = InfoNCEAligner(
            reference_lang,
            epochs=infonce_epochs,
            batch_size=infonce_batch_size,
            lr=infonce_lr,
            temperature=infonce_temperature,
        )

    def compute_projections(
        self,
        models: Dict[str, BabelVec],
        parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    ) -> Dict[str, np.ndarray]:
        """
        Compute ensemble projection matrices.

        Strategy:
        1. Compute Procrustes projections (fast, global)
        2. Compute InfoNCE projections (fine-grained)
        3. Combine with weighted average
        4. Re-orthogonalize to maintain rotation property

        Args:
            models: Dict mapping language code to BabelVec model
            parallel_data: Dict mapping (lang1, lang2) to parallel sentences

        Returns:
            Dict mapping language code to projection matrix
        """
        # Step 1: Procrustes alignment
        projections_procrustes = self._procrustes.compute_projections(
            models, parallel_data
        )

        # Step 2: InfoNCE fine-tuning
        projections_infonce = self._infonce.compute_projections(
            models, parallel_data
        )

        # Step 3: Ensemble combination
        projections_ensemble = {}
        for lang in models:
            combined = (
                self.procrustes_weight * projections_procrustes[lang]
                + self.infonce_weight * projections_infonce[lang]
            )

            # Step 4: Re-orthogonalize to keep as rotation matrix
            projections_ensemble[lang] = self._orthogonalize(combined)

        return projections_ensemble

    def align_pair(
        self,
        source_model: BabelVec,
        target_model: BabelVec,
        parallel_pairs: List[Tuple[str, str]],
    ) -> np.ndarray:
        """
        Compute ensemble alignment for a single language pair.

        Args:
            source_model: Source language model
            target_model: Target language model
            parallel_pairs: List of (source_sent, target_sent) pairs

        Returns:
            Projection matrix for source language
        """
        # Procrustes
        proj_procrustes = self._procrustes.align_pair(
            source_model, target_model, parallel_pairs
        )

        # InfoNCE
        proj_infonce = self._infonce.align_pair(
            source_model, target_model, parallel_pairs
        )

        # Combine
        combined = (
            self.procrustes_weight * proj_procrustes
            + self.infonce_weight * proj_infonce
        )

        return self._orthogonalize(combined)
