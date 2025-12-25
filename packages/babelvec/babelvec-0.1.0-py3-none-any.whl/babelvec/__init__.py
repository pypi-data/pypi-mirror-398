"""
BabelVec: Position-aware, cross-lingually aligned word embeddings built on FastText.
"""

from babelvec.version import __version__
from babelvec.core.model import BabelVec
from babelvec.core.positional_encoding import (
    PositionalEncoding,
    RoPEEncoding,
    SinusoidalEncoding,
    DecayEncoding,
)
from babelvec.core.sentence_encoder import SentenceEncoder

__all__ = [
    "__version__",
    "BabelVec",
    "PositionalEncoding",
    "RoPEEncoding",
    "SinusoidalEncoding",
    "DecayEncoding",
    "SentenceEncoder",
]
