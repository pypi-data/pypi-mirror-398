"""Monolingual training for BabelVec."""

from pathlib import Path
from typing import Optional, Union

from babelvec.core.model import BabelVec
from babelvec.core.fasttext_wrapper import FastTextWrapper
from babelvec.training.config import TrainingConfig, default_config


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
            },
            "corpus_path": str(corpus_path),
        },
    )

    # Save if path provided
    if output_path is not None:
        model.save(output_path)

    return model


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
