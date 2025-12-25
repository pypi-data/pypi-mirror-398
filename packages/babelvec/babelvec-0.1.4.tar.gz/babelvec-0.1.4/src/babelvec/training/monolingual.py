"""Monolingual training for BabelVec."""

import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Union

from babelvec.core.model import BabelVec
from babelvec.core.fasttext_wrapper import FastTextWrapper
from babelvec.training.config import TrainingConfig, default_config, get_cpu_count


def train_monolingual(
    lang: str,
    corpus_path: Union[str, Path],
    config: Optional[TrainingConfig] = None,
    output_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> BabelVec:
    """
    Train a monolingual BabelVec model.

    Args:
        lang: Language code (e.g., 'en', 'fr', 'ary')
        corpus_path: Path to training corpus (one sentence per line)
        config: Training configuration. If None, uses defaults.
        output_path: Optional path to save the model
        **kwargs: Override config parameters

    Returns:
        Trained BabelVec model

    Example:
        >>> model = train_monolingual('en', 'corpus.txt', dim=300, epochs=5)
        >>> model.save('en_300d.bin')
    """
    # Get config
    if config is None:
        config = default_config()

    # Apply overrides
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    corpus_path = Path(corpus_path)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    # Train FastText model
    ft_args = config.to_fasttext_args()
    ft = FastTextWrapper.train(corpus_path, **ft_args)

    # Create BabelVec model
    model = BabelVec(
        fasttext_model=ft,
        lang=lang,
        dim=config.dim,
        max_seq_len=config.max_seq_len,
        metadata={
            "training_config": {
                "dim": config.dim,
                "epochs": config.epochs,
                "lr": config.lr,
                "min_count": config.min_count,
                "model_type": config.model_type,
                "thread": config.thread,
            },
            "corpus_path": str(corpus_path),
        },
    )

    # Save if path provided
    if output_path is not None:
        model.save(output_path)

    return model


def _train_single_language(args: tuple) -> tuple:
    """Helper for parallel training."""
    lang, corpus_path, config, output_path = args
    model = train_monolingual(lang, corpus_path, config, output_path)
    return lang, model


def train_multiple_languages(
    languages: Dict[str, Union[str, Path]],
    config: Optional[TrainingConfig] = None,
    output_dir: Optional[Union[str, Path]] = None,
    parallel: bool = True,
    max_workers: int = None,
) -> Dict[str, BabelVec]:
    """
    Train multiple monolingual models, optionally in parallel.
    
    For servers with many cores, this trains languages simultaneously,
    with each language using a portion of available threads.

    Args:
        languages: Dict mapping language code to corpus path
        config: Training configuration
        output_dir: Directory to save models
        parallel: Whether to train languages in parallel
        max_workers: Max parallel training jobs (default: min(len(languages), 2))

    Returns:
        Dict mapping language code to trained model
    
    Example:
        >>> models = train_multiple_languages({
        ...     'en': 'en_corpus.txt',
        ...     'ar': 'ar_corpus.txt',
        ... }, parallel=True)
    """
    if config is None:
        config = default_config()
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    n_languages = len(languages)
    
    if parallel and n_languages > 1:
        # Determine parallelism
        if max_workers is None:
            max_workers = min(n_languages, 2)  # Train at most 2 languages in parallel
        
        # Divide threads among parallel jobs
        total_threads = config.thread
        threads_per_job = max(1, total_threads // max_workers)
        
        # Create per-language configs with reduced thread count
        job_config = TrainingConfig(
            dim=config.dim,
            epochs=config.epochs,
            lr=config.lr,
            min_count=config.min_count,
            word_ngrams=config.word_ngrams,
            minn=config.minn,
            maxn=config.maxn,
            ws=config.ws,
            neg=config.neg,
            model_type=config.model_type,
            loss=config.loss,
            bucket=config.bucket,
            thread=threads_per_job,
            verbose=config.verbose,
            max_seq_len=config.max_seq_len,
        )
        
        print(f"Training {n_languages} languages in parallel ({max_workers} workers, {threads_per_job} threads each)")
        
        # Prepare arguments
        args_list = []
        for lang, corpus_path in languages.items():
            output_path = output_dir / f"{lang}_model.bin" if output_dir else None
            args_list.append((lang, corpus_path, job_config, output_path))
        
        # Train in parallel using threads (FastText releases GIL during training)
        models = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(_train_single_language, args_list)
            for lang, model in results:
                models[lang] = model
        
        return models
    
    else:
        # Sequential training
        models = {}
        for lang, corpus_path in languages.items():
            output_path = output_dir / f"{lang}_model.bin" if output_dir else None
            models[lang] = train_monolingual(lang, corpus_path, config, output_path)
        return models


def train_from_texts(
    lang: str,
    texts: list[str],
    config: Optional[TrainingConfig] = None,
    **kwargs,
) -> BabelVec:
    """
    Train from a list of texts (creates temporary corpus file).

    Args:
        lang: Language code
        texts: List of training sentences
        config: Training configuration
        **kwargs: Override config parameters

    Returns:
        Trained BabelVec model
    """
    import tempfile

    # Write texts to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for text in texts:
            f.write(text.strip() + "\n")
        temp_path = f.name

    try:
        return train_monolingual(lang, temp_path, config, **kwargs)
    finally:
        Path(temp_path).unlink(missing_ok=True)
