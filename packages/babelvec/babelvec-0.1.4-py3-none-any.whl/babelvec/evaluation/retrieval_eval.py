"""Cross-lingual retrieval evaluation."""

from typing import Dict, List, Optional, Tuple

import numpy as np

from babelvec.core.model import BabelVec


def cross_lingual_retrieval(
    model_src: BabelVec,
    model_tgt: BabelVec,
    parallel_sentences: List[Tuple[str, str]],
    method: str = "average",
    k_values: List[int] = [1, 5, 10],
) -> Dict[str, float]:
    """
    Evaluate cross-lingual retrieval accuracy.

    For each source sentence, find the nearest target sentence
    and check if it's the correct parallel pair.

    Args:
        model_src: Source language model
        model_tgt: Target language model
        parallel_sentences: List of (src_sent, tgt_sent) parallel pairs
        method: Sentence encoding method
        k_values: Values of k for recall@k

    Returns:
        Dict with retrieval metrics
    """
    # Encode all sentences
    src_vecs = []
    tgt_vecs = []

    for src_sent, tgt_sent in parallel_sentences:
        src_vec = model_src.get_sentence_vector(src_sent, method=method)
        tgt_vec = model_tgt.get_sentence_vector(tgt_sent, method=method)

        if np.linalg.norm(src_vec) > 0 and np.linalg.norm(tgt_vec) > 0:
            src_vecs.append(src_vec)
            tgt_vecs.append(tgt_vec)

    if len(src_vecs) < 2:
        return {f"recall@{k}": 0.0 for k in k_values}

    src_matrix = np.array(src_vecs)
    tgt_matrix = np.array(tgt_vecs)

    # Normalize
    src_matrix = src_matrix / (np.linalg.norm(src_matrix, axis=1, keepdims=True) + 1e-8)
    tgt_matrix = tgt_matrix / (np.linalg.norm(tgt_matrix, axis=1, keepdims=True) + 1e-8)

    # Compute similarity matrix
    sim_matrix = src_matrix @ tgt_matrix.T

    # Compute recall@k
    n = len(src_vecs)
    results = {}

    for k in k_values:
        # Get top-k indices for each source
        top_k_indices = np.argsort(-sim_matrix, axis=1)[:, :k]

        # Check if correct target is in top-k
        correct = sum(i in top_k_indices[i] for i in range(n))
        results[f"recall@{k}"] = correct / n

    # Mean reciprocal rank
    ranks = np.argsort(np.argsort(-sim_matrix, axis=1), axis=1)
    correct_ranks = ranks[np.arange(n), np.arange(n)] + 1  # 1-indexed
    mrr = float(np.mean(1.0 / correct_ranks))
    results["mrr"] = mrr

    # Average parallel similarity
    parallel_sims = sim_matrix[np.arange(n), np.arange(n)]
    results["avg_parallel_similarity"] = float(np.mean(parallel_sims))

    results["n_pairs"] = n

    return results


def retrieval_accuracy(
    models: Dict[str, BabelVec],
    parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    method: str = "average",
) -> Dict[str, Dict[str, float]]:
    """
    Compute retrieval accuracy for all language pairs.

    Args:
        models: Dict mapping language code to BabelVec model
        parallel_data: Dict mapping (lang1, lang2) to parallel sentences
        method: Sentence encoding method

    Returns:
        Dict mapping language pair to retrieval metrics
    """
    results = {}

    for (lang1, lang2), sentences in parallel_data.items():
        if lang1 not in models or lang2 not in models:
            continue

        # Forward direction: lang1 -> lang2
        fwd_results = cross_lingual_retrieval(
            models[lang1], models[lang2], sentences, method
        )
        results[f"{lang1}->{lang2}"] = fwd_results

        # Backward direction: lang2 -> lang1
        reversed_sentences = [(s2, s1) for s1, s2 in sentences]
        bwd_results = cross_lingual_retrieval(
            models[lang2], models[lang1], reversed_sentences, method
        )
        results[f"{lang2}->{lang1}"] = bwd_results

    return results


def alignment_quality_score(
    model_src: BabelVec,
    model_tgt: BabelVec,
    parallel_sentences: List[Tuple[str, str]],
    method: str = "average",
) -> float:
    """
    Compute overall alignment quality score.

    Combines retrieval accuracy and parallel similarity into
    a single score between 0 and 1.

    Args:
        model_src: Source language model
        model_tgt: Target language model
        parallel_sentences: Parallel sentence pairs
        method: Sentence encoding method

    Returns:
        Alignment quality score (0-1)
    """
    metrics = cross_lingual_retrieval(
        model_src, model_tgt, parallel_sentences, method
    )

    # Weighted combination
    recall_1 = metrics.get("recall@1", 0.0)
    recall_5 = metrics.get("recall@5", 0.0)
    mrr = metrics.get("mrr", 0.0)
    parallel_sim = metrics.get("avg_parallel_similarity", 0.0)

    # Normalize parallel_sim to 0-1 range (assuming it's typically 0.5-1.0)
    parallel_sim_norm = max(0, min(1, (parallel_sim - 0.5) * 2))

    # Weighted average
    score = 0.3 * recall_1 + 0.2 * recall_5 + 0.2 * mrr + 0.3 * parallel_sim_norm

    return float(score)
