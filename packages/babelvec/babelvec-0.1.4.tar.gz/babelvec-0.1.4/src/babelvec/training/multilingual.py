"""Multilingual training for BabelVec."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from babelvec.core.model import BabelVec
from babelvec.training.monolingual import train_monolingual
from babelvec.training.config import TrainingConfig, default_config
from babelvec.training.alignment import (
    ProcrustesAligner,
    InfoNCEAligner,
    EnsembleAligner,
)


def train_multilingual(
    languages: List[str],
    corpus_paths: Dict[str, Union[str, Path]],
    parallel_data: Optional[Dict[Tuple[str, str], List[Tuple[str, str]]]] = None,
    config: Optional[TrainingConfig] = None,
    alignment: str = "ensemble",
    reference_lang: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    **kwargs,
) -> Dict[str, BabelVec]:
    """
    Train multilingual BabelVec models with cross-lingual alignment.

    Args:
        languages: List of language codes
        corpus_paths: Dict mapping language code to corpus path
        parallel_data: Dict mapping (lang1, lang2) to list of parallel sentences.
                      If None, models are trained but not aligned.
        config: Training configuration
        alignment: Alignment method ('procrustes', 'infonce', 'ensemble', 'none')
        reference_lang: Reference language for alignment
        output_dir: Optional directory to save models
        **kwargs: Override config parameters

    Returns:
        Dict mapping language code to trained (and optionally aligned) BabelVec model

    Example:
        >>> models = train_multilingual(
        ...     languages=['en', 'fr', 'de'],
        ...     corpus_paths={'en': 'en.txt', 'fr': 'fr.txt', 'de': 'de.txt'},
        ...     parallel_data={('en', 'fr'): [('hello', 'bonjour'), ...]},
        ...     alignment='ensemble'
        ... )
    """
    if config is None:
        config = default_config()

    # Apply overrides
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Validate inputs
    for lang in languages:
        if lang not in corpus_paths:
            raise ValueError(f"Missing corpus path for language: {lang}")

    # Step 1: Train monolingual models
    models = {}
    for lang in languages:
        corpus_path = corpus_paths[lang]
        model = train_monolingual(lang, corpus_path, config)
        models[lang] = model

    # Step 2: Align if parallel data provided and alignment requested
    if parallel_data and alignment != "none":
        models = align_models(
            models,
            parallel_data,
            method=alignment,
            reference_lang=reference_lang,
            config=config,
        )

    # Step 3: Save if output directory provided
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for lang, model in models.items():
            suffix = "_aligned" if model.is_aligned else ""
            model.save(output_dir / f"{lang}_{config.dim}d{suffix}.bin")

    return models


def align_models(
    models: Dict[str, BabelVec],
    parallel_data: Dict[Tuple[str, str], List[Tuple[str, str]]],
    method: str = "ensemble",
    reference_lang: Optional[str] = None,
    config: Optional[TrainingConfig] = None,
) -> Dict[str, BabelVec]:
    """
    Align pre-trained models using parallel data.

    Args:
        models: Dict mapping language code to BabelVec model
        parallel_data: Dict mapping (lang1, lang2) to parallel sentences
        method: Alignment method ('procrustes', 'infonce', 'ensemble')
        reference_lang: Reference language for alignment
        config: Configuration for alignment parameters

    Returns:
        Dict mapping language code to aligned BabelVec model
    """
    if config is None:
        config = default_config()

    # Select aligner
    if method == "procrustes":
        aligner = ProcrustesAligner(reference_lang)
    elif method == "infonce":
        aligner = InfoNCEAligner(
            reference_lang,
            epochs=config.infonce_epochs,
            batch_size=config.infonce_batch_size,
            lr=0.001,
            temperature=config.infonce_temperature,
        )
    elif method == "ensemble":
        aligner = EnsembleAligner(
            reference_lang,
            procrustes_weight=config.procrustes_weight,
            infonce_weight=config.infonce_weight,
            infonce_epochs=config.infonce_epochs,
            infonce_batch_size=config.infonce_batch_size,
            infonce_temperature=config.infonce_temperature,
        )
    else:
        raise ValueError(f"Unknown alignment method: {method}")

    return aligner.align(models, parallel_data)
