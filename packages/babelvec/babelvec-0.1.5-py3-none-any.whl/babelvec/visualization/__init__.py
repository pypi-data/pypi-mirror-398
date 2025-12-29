"""Visualization utilities for BabelVec (requires viz extras)."""

try:
    from babelvec.visualization.embedding_space import (
        plot_embeddings_tsne,
        plot_embeddings_umap,
    )
    from babelvec.visualization.alignment_viz import plot_alignment_quality

    __all__ = [
        "plot_embeddings_tsne",
        "plot_embeddings_umap",
        "plot_alignment_quality",
    ]
except ImportError:
    # Visualization dependencies not installed
    __all__ = []
