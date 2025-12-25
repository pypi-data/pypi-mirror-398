"""Intrinsic evaluation metrics for word embeddings."""

from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import spearmanr

from babelvec.core.model import BabelVec


def word_similarity_eval(
    model: BabelVec,
    word_pairs: List[Tuple[str, str, float]],
) -> Dict[str, float]:
    """
    Evaluate word similarity correlation.

    Args:
        model: BabelVec model
        word_pairs: List of (word1, word2, human_score) tuples

    Returns:
        Dict with 'spearman', 'coverage', 'n_pairs' metrics
    """
    model_scores = []
    human_scores = []
    oov_count = 0

    for word1, word2, human_score in word_pairs:
        try:
            vec1 = model.get_word_vector(word1)
            vec2 = model.get_word_vector(word2)

            # Cosine similarity
            sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8)

            model_scores.append(sim)
            human_scores.append(human_score)
        except Exception:
            oov_count += 1

    if len(model_scores) < 2:
        return {
            "spearman": 0.0,
            "coverage": 0.0,
            "n_pairs": 0,
        }

    correlation, _ = spearmanr(model_scores, human_scores)

    return {
        "spearman": float(correlation) if not np.isnan(correlation) else 0.0,
        "coverage": len(model_scores) / len(word_pairs),
        "n_pairs": len(model_scores),
        "oov_pairs": oov_count,
    }


def analogy_eval(
    model: BabelVec,
    analogies: List[Tuple[str, str, str, str]],
    topn: int = 10,
) -> Dict[str, float]:
    """
    Evaluate word analogy task (a:b :: c:?).

    Args:
        model: BabelVec model
        analogies: List of (a, b, c, d) tuples where a:b :: c:d
        topn: Number of candidates to consider

    Returns:
        Dict with accuracy metrics
    """
    correct = 0
    total = 0
    oov_count = 0

    for a, b, c, d in analogies:
        try:
            # Get vectors
            vec_a = model.get_word_vector(a)
            vec_b = model.get_word_vector(b)
            vec_c = model.get_word_vector(c)

            # Compute target vector: b - a + c
            target = vec_b - vec_a + vec_c
            target = target / (np.linalg.norm(target) + 1e-8)

            # Find nearest neighbors
            neighbors = model.most_similar(c, topn=topn + 3)

            # Filter out input words
            exclude = {a.lower(), b.lower(), c.lower()}
            candidates = [w for w, _ in neighbors if w.lower() not in exclude][:topn]

            if d.lower() in [w.lower() for w in candidates]:
                correct += 1
            total += 1

        except Exception:
            oov_count += 1

    accuracy = correct / total if total > 0 else 0.0

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "oov": oov_count,
    }


def oov_coverage(
    model: BabelVec,
    words: List[str],
) -> Dict[str, float]:
    """
    Evaluate OOV (out-of-vocabulary) coverage.

    Args:
        model: BabelVec model
        words: List of words to check

    Returns:
        Dict with coverage metrics
    """
    in_vocab = 0
    oov = 0

    vocab_set = set(model.words)

    for word in words:
        if word in vocab_set:
            in_vocab += 1
        else:
            oov += 1

    total = len(words)
    coverage = in_vocab / total if total > 0 else 0.0

    return {
        "coverage": coverage,
        "in_vocab": in_vocab,
        "oov": oov,
        "total": total,
        "oov_rate": oov / total if total > 0 else 0.0,
    }


def embedding_quality_metrics(
    model: BabelVec,
    sample_words: Optional[List[str]] = None,
    n_samples: int = 1000,
) -> Dict[str, float]:
    """
    Compute embedding quality metrics.

    Args:
        model: BabelVec model
        sample_words: Words to sample. If None, samples from vocabulary.
        n_samples: Number of words to sample

    Returns:
        Dict with quality metrics
    """
    if sample_words is None:
        vocab = model.words
        if len(vocab) > n_samples:
            indices = np.random.choice(len(vocab), n_samples, replace=False)
            sample_words = [vocab[i] for i in indices]
        else:
            sample_words = vocab

    # Get embeddings
    embeddings = model.get_word_vectors(sample_words)

    # Compute metrics
    norms = np.linalg.norm(embeddings, axis=1)

    # Average pairwise similarity (sample)
    n_pairs = min(1000, len(embeddings) * (len(embeddings) - 1) // 2)
    if n_pairs > 0 and len(embeddings) > 1:
        idx1 = np.random.randint(0, len(embeddings), n_pairs)
        idx2 = np.random.randint(0, len(embeddings), n_pairs)
        # Ensure different indices
        mask = idx1 != idx2
        idx1, idx2 = idx1[mask], idx2[mask]

        if len(idx1) > 0:
            sims = np.sum(embeddings[idx1] * embeddings[idx2], axis=1) / (
                norms[idx1] * norms[idx2] + 1e-8
            )
            avg_sim = float(np.mean(sims))
        else:
            avg_sim = 0.0
    else:
        avg_sim = 0.0

    return {
        "mean_norm": float(np.mean(norms)),
        "std_norm": float(np.std(norms)),
        "min_norm": float(np.min(norms)),
        "max_norm": float(np.max(norms)),
        "avg_pairwise_similarity": avg_sim,
        "n_samples": len(sample_words),
    }
