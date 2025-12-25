"""Base class for alignment methods."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import numpy as np

from babelvec.core.model import BabelVec


class BaseAligner(ABC):
    """Base class for cross-lingual alignment methods."""

    def __init__(self, reference_lang: Optional[str] = None):
        """
        Initialize aligner.

        Args:
            reference_lang: Reference language for alignment.
                           If None, uses English ('en') or first language.
        """
        self.reference_lang = reference_lang

    @abstractmethod
    def compute_projections(
        self,
        models: Dict[str, BabelVec],
        parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    ) -> Dict[str, np.ndarray]:
        """
        Compute projection matrices for each language.

        Args:
            models: Dict mapping language code to BabelVec model
            parallel_data: Dict mapping (lang1, lang2) to list of parallel sentences

        Returns:
            Dict mapping language code to projection matrix
        """
        pass

    def align(
        self,
        models: Dict[str, BabelVec],
        parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    ) -> Dict[str, BabelVec]:
        """
        Align models and return new aligned models.

        Args:
            models: Dict mapping language code to BabelVec model
            parallel_data: Parallel sentence pairs

        Returns:
            Dict mapping language code to aligned BabelVec model
        """
        projections = self.compute_projections(models, parallel_data)

        aligned_models = {}
        for lang, model in models.items():
            # Create a copy with projection applied
            aligned = BabelVec(
                fasttext_model=model._ft,
                lang=lang,
                dim=model.dim,
                max_seq_len=model.max_seq_len,
                metadata={**model.metadata, "aligned": True, "aligner": self.__class__.__name__},
            )
            aligned.set_projection(projections[lang])
            aligned_models[lang] = aligned

        return aligned_models

    def _get_reference_lang(self, languages: List[str]) -> str:
        """Determine reference language."""
        if self.reference_lang and self.reference_lang in languages:
            return self.reference_lang
        if "en" in languages:
            return "en"
        return languages[0]

    def _get_parallel_vectors(
        self,
        model1: BabelVec,
        model2: BabelVec,
        parallel_pairs: List[Tuple[str, str]],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get embedding matrices for parallel sentences.

        Args:
            model1: First language model
            model2: Second language model
            parallel_pairs: List of (sent1, sent2) pairs

        Returns:
            Tuple of (embeddings1, embeddings2) arrays
        """
        vecs1 = []
        vecs2 = []

        for sent1, sent2 in parallel_pairs:
            # Use simple average for alignment (position-agnostic)
            v1 = model1.get_sentence_vector(sent1, method="average")
            v2 = model2.get_sentence_vector(sent2, method="average")

            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                vecs1.append(v1)
                vecs2.append(v2)

        return np.array(vecs1), np.array(vecs2)

    def _orthogonalize(self, matrix: np.ndarray) -> np.ndarray:
        """
        Orthogonalize a matrix using SVD.

        Args:
            matrix: Input matrix

        Returns:
            Orthogonal matrix (rotation)
        """
        U, _, Vt = np.linalg.svd(matrix)
        return U @ Vt
