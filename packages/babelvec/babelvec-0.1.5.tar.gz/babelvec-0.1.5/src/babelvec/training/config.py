"""Training configuration for BabelVec."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def get_cpu_count() -> int:
    """Get available CPU count, preferring physical cores."""
    try:
        # Try to get physical cores (better for FastText)
        import psutil
        return psutil.cpu_count(logical=False) or os.cpu_count() or 4
    except ImportError:
        return os.cpu_count() or 4


@dataclass
class TrainingConfig:
    """Configuration for BabelVec training."""

    # Model parameters
    dim: int = 300
    min_count: int = 5
    word_ngrams: int = 1
    minn: int = 3
    maxn: int = 6
    bucket: int = 2000000  # Hash buckets for subwords

    # Training parameters
    epochs: int = 5
    lr: float = 0.05
    ws: int = 5  # Window size
    neg: int = 5  # Negative samples
    model_type: str = "skipgram"  # 'skipgram' or 'cbow'
    loss: str = "ns"  # 'ns' (negative sampling), 'hs' (hierarchical softmax), 'softmax'

    # System parameters - auto-detect by default
    thread: int = field(default_factory=get_cpu_count)
    verbose: int = 1

    # Alignment parameters
    alignment_method: str = "ensemble"  # 'procrustes', 'infonce', 'ensemble'
    procrustes_weight: float = 0.8
    infonce_weight: float = 0.2
    infonce_epochs: int = 3
    infonce_batch_size: int = 32
    infonce_temperature: float = 0.07

    # Sentence encoding
    max_seq_len: int = 512

    def to_fasttext_args(self) -> Dict:
        """Convert to FastText training arguments."""
        return {
            "dim": self.dim,
            "epochs": self.epochs,
            "lr": self.lr,
            "min_count": self.min_count,
            "word_ngrams": self.word_ngrams,
            "minn": self.minn,
            "maxn": self.maxn,
            "ws": self.ws,
            "neg": self.neg,
            "model_type": self.model_type,
            "loss": self.loss,
            "bucket": self.bucket,
            "thread": self.thread,
            "verbose": self.verbose,
        }


@dataclass
class AlignmentConfig:
    """Configuration for cross-lingual alignment."""

    method: str = "ensemble"  # 'procrustes', 'infonce', 'ensemble'
    procrustes_weight: float = 0.8
    infonce_weight: float = 0.2
    infonce_epochs: int = 3
    infonce_batch_size: int = 32
    infonce_temperature: float = 0.07
    infonce_lr: float = 0.001

    # Anchor words for Procrustes
    n_anchors: int = 5000

    # Reference language for alignment
    reference_lang: Optional[str] = None


def default_config() -> TrainingConfig:
    """Get default training configuration."""
    return TrainingConfig()


def fast_config() -> TrainingConfig:
    """Get fast training configuration (for testing)."""
    return TrainingConfig(
        dim=100,
        epochs=1,
        min_count=1,
        thread=2,
        verbose=0,
    )


def quality_config() -> TrainingConfig:
    """Get high-quality training configuration."""
    return TrainingConfig(
        dim=300,
        epochs=10,
        min_count=5,
        minn=3,
        maxn=6,
        ws=5,
        neg=10,
    )


def max_performance_config() -> TrainingConfig:
    """Get maximum performance configuration for large servers."""
    cpu_count = get_cpu_count()
    return TrainingConfig(
        dim=300,
        epochs=5,
        min_count=5,
        minn=3,
        maxn=6,
        ws=5,
        neg=10,
        thread=cpu_count,
        bucket=2000000,
        loss="ns",
        verbose=2,
    )
