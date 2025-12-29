"""Training utilities for BabelVec models."""

from babelvec.training.monolingual import train_monolingual, train_multiple_languages
from babelvec.training.multilingual import train_multilingual, align_models
from babelvec.training.config import (
    TrainingConfig, 
    AlignmentConfig,
    get_cpu_count,
    default_config,
    fast_config,
    quality_config,
    max_performance_config,
)

__all__ = [
    "train_monolingual",
    "train_multiple_languages",
    "train_multilingual",
    "align_models",
    "TrainingConfig",
    "AlignmentConfig",
    "get_cpu_count",
    "default_config",
    "fast_config",
    "quality_config",
    "max_performance_config",
]
