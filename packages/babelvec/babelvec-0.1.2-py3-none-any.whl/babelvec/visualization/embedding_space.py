"""Embedding space visualization."""

from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import matplotlib.pyplot as plt
    from sklearn.manifold import TSNE

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


def plot_embeddings_tsne(
    model: BabelVec,
    words: Optional[List[str]] = None,
    n_words: int = 100,
    perplexity: int = 30,
    figsize: Tuple[int, int] = (10, 10),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> "plt.Figure":
    """
    Plot word embeddings using t-SNE.

    Args:
        model: BabelVec model
        words: Specific words to plot. If None, samples from vocabulary.
        n_words: Number of words to sample if words is None
        perplexity: t-SNE perplexity parameter
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    _check_viz_deps()

    if words is None:
        vocab = model.words
        if len(vocab) > n_words:
            indices = np.random.choice(len(vocab), n_words, replace=False)
            words = [vocab[i] for i in indices]
        else:
            words = vocab

    # Get embeddings
    embeddings = model.get_word_vectors(words)

    # Apply t-SNE
    tsne = TSNE(n_components=2, perplexity=min(perplexity, len(words) - 1), random_state=42)
    coords = tsne.fit_transform(embeddings)

    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(coords[:, 0], coords[:, 1], alpha=0.6)

    # Add labels
    for i, word in enumerate(words):
        ax.annotate(word, (coords[i, 0], coords[i, 1]), fontsize=8, alpha=0.7)

    ax.set_title(title or f"t-SNE Embedding Space ({model.lang})")
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_embeddings_umap(
    model: BabelVec,
    words: Optional[List[str]] = None,
    n_words: int = 100,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    figsize: Tuple[int, int] = (10, 10),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> "plt.Figure":
    """
    Plot word embeddings using UMAP.

    Args:
        model: BabelVec model
        words: Specific words to plot
        n_words: Number of words to sample
        n_neighbors: UMAP n_neighbors parameter
        min_dist: UMAP min_dist parameter
        figsize: Figure size
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure
    """
    _check_viz_deps()

    try:
        import umap
    except ImportError:
        raise ImportError("UMAP requires umap-learn. Install with: pip install umap-learn")

    if words is None:
        vocab = model.words
        if len(vocab) > n_words:
            indices = np.random.choice(len(vocab), n_words, replace=False)
            words = [vocab[i] for i in indices]
        else:
            words = vocab

    # Get embeddings
    embeddings = model.get_word_vectors(words)

    # Apply UMAP
    reducer = umap.UMAP(n_neighbors=n_neighbors, min_dist=min_dist, random_state=42)
    coords = reducer.fit_transform(embeddings)

    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(coords[:, 0], coords[:, 1], alpha=0.6)

    for i, word in enumerate(words):
        ax.annotate(word, (coords[i, 0], coords[i, 1]), fontsize=8, alpha=0.7)

    ax.set_title(title or f"UMAP Embedding Space ({model.lang})")
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig
