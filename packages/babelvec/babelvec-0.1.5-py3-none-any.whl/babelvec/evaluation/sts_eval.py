"""Sentence similarity evaluation."""

from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import spearmanr, pearsonr

from babelvec.core.model import BabelVec


def sentence_similarity_eval(
    model: BabelVec,
    sentence_pairs: List[Tuple[str, str, float]],
    method: str = "rope",
) -> Dict[str, float]:
    """
    Evaluate sentence similarity correlation with human judgments.

    Args:
        model: BabelVec model
        sentence_pairs: List of (sent1, sent2, human_score) tuples
        method: Sentence encoding method

    Returns:
        Dict with correlation metrics
    """
    model_scores = []
    human_scores = []

    for sent1, sent2, human_score in sentence_pairs:
        vec1 = model.get_sentence_vector(sent1, method=method)
        vec2 = model.get_sentence_vector(sent2, method=method)

        # Skip if either vector is zero
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            continue

        # Cosine similarity
        sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

        model_scores.append(sim)
        human_scores.append(human_score)

    if len(model_scores) < 2:
        return {
            "spearman": 0.0,
            "pearson": 0.0,
            "n_pairs": 0,
        }

    spearman_corr, _ = spearmanr(model_scores, human_scores)
    pearson_corr, _ = pearsonr(model_scores, human_scores)

    return {
        "spearman": float(spearman_corr) if not np.isnan(spearman_corr) else 0.0,
        "pearson": float(pearson_corr) if not np.isnan(pearson_corr) else 0.0,
        "n_pairs": len(model_scores),
        "coverage": len(model_scores) / len(sentence_pairs),
    }


def position_sensitivity_eval(
    model: BabelVec,
    sentence_pairs: List[Tuple[str, str]],
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate position sensitivity by comparing different encoding methods.

    Tests whether position-aware methods distinguish word order
    better than simple averaging.

    Args:
        model: BabelVec model
        sentence_pairs: List of (sent1, sent2) pairs with different word orders
                       but same words (e.g., "dog bites man" vs "man bites dog")

    Returns:
        Dict mapping method to sensitivity metrics
    """
    methods = ["average", "rope", "sinusoidal", "decay"]
    results = {}

    for method in methods:
        similarities = []

        for sent1, sent2 in sentence_pairs:
            vec1 = model.get_sentence_vector(sent1, method=method)
            vec2 = model.get_sentence_vector(sent2, method=method)

            if np.linalg.norm(vec1) > 0 and np.linalg.norm(vec2) > 0:
                sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                similarities.append(sim)

        if similarities:
            results[method] = {
                "mean_similarity": float(np.mean(similarities)),
                "std_similarity": float(np.std(similarities)),
                "min_similarity": float(np.min(similarities)),
                "max_similarity": float(np.max(similarities)),
                # Lower similarity = better position sensitivity
                "position_sensitivity": 1.0 - float(np.mean(similarities)),
            }
        else:
            results[method] = {
                "mean_similarity": 1.0,
                "position_sensitivity": 0.0,
            }

    return results


def compare_encoding_methods(
    model: BabelVec,
    sentence_pairs: List[Tuple[str, str, float]],
) -> Dict[str, Dict[str, float]]:
    """
    Compare all encoding methods on sentence similarity task.

    Args:
        model: BabelVec model
        sentence_pairs: List of (sent1, sent2, human_score) tuples

    Returns:
        Dict mapping method to evaluation metrics
    """
    methods = ["average", "rope", "sinusoidal", "decay"]
    results = {}

    for method in methods:
        results[method] = sentence_similarity_eval(model, sentence_pairs, method)

    return results
