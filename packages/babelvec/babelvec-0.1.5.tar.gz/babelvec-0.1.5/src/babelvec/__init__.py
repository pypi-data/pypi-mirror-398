"""
BabelVec: Position-aware, cross-lingually aligned word embeddings built on FastText.
"""

from importlib.metadata import version

__version__ = version("babelvec")

from babelvec.core.model import BabelVec
from babelvec.core.positional_encoding import (
    PositionalEncoding,
    RoPEEncoding,
    SinusoidalEncoding,
    DecayEncoding,
)
from babelvec.core.sentence_encoder import SentenceEncoder
from babelvec.families import (
    get_family_key,
    get_family_languages,
    assign_families,
    get_training_groups,
    HARDCODED_FAMILIES,
    WIKIPEDIA_LANGUAGES,
)

__all__ = [
    "__version__",
    "BabelVec",
    "PositionalEncoding",
    "RoPEEncoding",
    "SinusoidalEncoding",
    "DecayEncoding",
    "SentenceEncoder",
    # Family assignment
    "get_family_key",
    "get_family_languages",
    "assign_families",
    "get_training_groups",
    "HARDCODED_FAMILIES",
    "WIKIPEDIA_LANGUAGES",
]
