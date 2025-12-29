"""Command-line interface for BabelVec."""

import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="babelvec",
        description="BabelVec: Position-aware cross-lingual word embeddings",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train a BabelVec model")
    train_parser.add_argument("--lang", required=True, help="Language code")
    train_parser.add_argument("--corpus", required=True, help="Path to corpus file")
    train_parser.add_argument("--output", "-o", required=True, help="Output model path")
    train_parser.add_argument("--dim", type=int, default=300, help="Embedding dimension")
    train_parser.add_argument("--epochs", type=int, default=5, help="Training epochs")
    train_parser.add_argument("--min-count", type=int, default=5, help="Minimum word count")
    train_parser.add_argument("--threads", type=int, default=4, help="Number of threads")

    # Align command
    align_parser = subparsers.add_parser("align", help="Align models cross-lingually")
    align_parser.add_argument("--models", nargs="+", required=True, help="Model paths (lang:path)")
    align_parser.add_argument("--parallel", required=True, help="Parallel data file")
    align_parser.add_argument("--method", default="ensemble", choices=["procrustes", "infonce", "ensemble"])
    align_parser.add_argument("--output-dir", "-o", required=True, help="Output directory")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a model")
    eval_parser.add_argument("--model", required=True, help="Model path")
    eval_parser.add_argument("--word-sim", help="Word similarity dataset")
    eval_parser.add_argument("--analogies", help="Analogies dataset")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show model information")
    info_parser.add_argument("model", help="Model path")

    args = parser.parse_args()

    if args.version:
        from babelvec.version import __version__
        print(f"babelvec {__version__}")
        return 0

    if args.command == "train":
        return cmd_train(args)
    elif args.command == "align":
        return cmd_align(args)
    elif args.command == "evaluate":
        return cmd_evaluate(args)
    elif args.command == "info":
        return cmd_info(args)
    else:
        parser.print_help()
        return 0


def cmd_train(args):
    """Train command handler."""
    from babelvec.training import train_monolingual
    from babelvec.training.config import TrainingConfig

    config = TrainingConfig(
        dim=args.dim,
        epochs=args.epochs,
        min_count=args.min_count,
        thread=args.threads,
    )

    print(f"Training {args.lang} model...")
    print(f"  Corpus: {args.corpus}")
    print(f"  Dimension: {args.dim}")
    print(f"  Epochs: {args.epochs}")

    model = train_monolingual(
        lang=args.lang,
        corpus_path=args.corpus,
        config=config,
        output_path=args.output,
    )

    print(f"Model saved to: {args.output}")
    print(f"  Vocabulary size: {model.vocab_size}")
    return 0


def cmd_align(args):
    """Align command handler."""
    from babelvec import BabelVec
    from babelvec.training import align_models
    from babelvec.utils.data_loader import load_parallel_data

    # Parse model paths
    models = {}
    for spec in args.models:
        lang, path = spec.split(":", 1)
        models[lang] = BabelVec.load(path)
        print(f"Loaded {lang} model from {path}")

    # Load parallel data
    parallel_data = load_parallel_data(args.parallel)
    print(f"Loaded parallel data: {sum(len(v) for v in parallel_data.values())} pairs")

    # Align
    print(f"Aligning with method: {args.method}")
    aligned = align_models(models, parallel_data, method=args.method)

    # Save
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for lang, model in aligned.items():
        output_path = output_dir / f"{lang}_aligned.bin"
        model.save(output_path)
        print(f"Saved aligned {lang} model to {output_path}")

    return 0


def cmd_evaluate(args):
    """Evaluate command handler."""
    from babelvec import BabelVec
    from babelvec.evaluation import word_similarity_eval, analogy_eval
    from babelvec.utils.data_loader import load_word_pairs, load_analogies

    model = BabelVec.load(args.model)
    print(f"Loaded model: {model}")

    if args.word_sim:
        pairs = load_word_pairs(args.word_sim)
        results = word_similarity_eval(model, pairs)
        print(f"\nWord Similarity:")
        print(f"  Spearman: {results['spearman']:.4f}")
        print(f"  Coverage: {results['coverage']:.2%}")

    if args.analogies:
        analogies = load_analogies(args.analogies)
        results = analogy_eval(model, analogies)
        print(f"\nAnalogies:")
        print(f"  Accuracy: {results['accuracy']:.2%}")
        print(f"  Correct: {results['correct']}/{results['total']}")

    return 0


def cmd_info(args):
    """Info command handler."""
    from babelvec import BabelVec

    model = BabelVec.load(args.model)

    print(f"Model: {args.model}")
    print(f"  Language: {model.lang}")
    print(f"  Dimension: {model.dim}")
    print(f"  Vocabulary: {model.vocab_size:,} words")
    print(f"  Aligned: {model.is_aligned}")

    if model.metadata:
        print(f"  Metadata:")
        for key, value in model.metadata.items():
            print(f"    {key}: {value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
