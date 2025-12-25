"""Alignment visualization utilities."""

from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    HAS_VIZ = True
except ImportError:
    HAS_VIZ = False

from babelvec.core.model import BabelVec


def _check_viz_deps():
    if not HAS_VIZ:
        raise ImportError(
            "Visualization requires additional dependencies. "
            "Install with: pip install babelvec[viz]"
        )


def plot_alignment_quality(
    retrieval_results: Dict[str, Dict[str, float]],
    metric: str = "recall@1",
    figsize: Tuple[int, int] = (12, 8),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> "plt.Figure":
    """
    Plot alignment quality heatmap.

    Args:
        retrieval_results: Results from retrieval_accuracy()
        metric: Metric to plot
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    _check_viz_deps()

    # Extract language pairs and scores
    pairs = list(retrieval_results.keys())
    scores = [retrieval_results[p].get(metric, 0) for p in pairs]

    # Create bar plot
    fig, ax = plt.subplots(figsize=figsize)

    colors = plt.cm.RdYlGn([s for s in scores])
    bars = ax.bar(range(len(pairs)), scores, color=colors)

    ax.set_xticks(range(len(pairs)))
    ax.set_xticklabels(pairs, rotation=45, ha="right")
    ax.set_ylabel(metric)
    ax.set_title(title or f"Cross-Lingual Alignment Quality ({metric})")
    ax.set_ylim(0, 1)

    # Add value labels
    for bar, score in zip(bars, scores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{score:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_parallel_similarity_distribution(
    model_src: BabelVec,
    model_tgt: BabelVec,
    parallel_sentences: List[Tuple[str, str]],
    method: str = "average",
    figsize: Tuple[int, int] = (10, 6),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> "plt.Figure":
    """
    Plot distribution of parallel sentence similarities.

    Args:
        model_src: Source language model
        model_tgt: Target language model
        parallel_sentences: List of parallel sentence pairs
        method: Sentence encoding method
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    _check_viz_deps()

    similarities = []
    for src_sent, tgt_sent in parallel_sentences:
        src_vec = model_src.get_sentence_vector(src_sent, method=method)
        tgt_vec = model_tgt.get_sentence_vector(tgt_sent, method=method)

        if np.linalg.norm(src_vec) > 0 and np.linalg.norm(tgt_vec) > 0:
            sim = np.dot(src_vec, tgt_vec) / (
                np.linalg.norm(src_vec) * np.linalg.norm(tgt_vec)
            )
            similarities.append(sim)

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(similarities, bins=30, edgecolor="black", alpha=0.7)
    ax.axvline(np.mean(similarities), color="red", linestyle="--", label=f"Mean: {np.mean(similarities):.3f}")
    ax.axvline(np.median(similarities), color="green", linestyle="--", label=f"Median: {np.median(similarities):.3f}")

    ax.set_xlabel("Cosine Similarity")
    ax.set_ylabel("Count")
    ax.set_title(title or f"Parallel Sentence Similarity Distribution ({model_src.lang}-{model_tgt.lang})")
    ax.legend()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig
