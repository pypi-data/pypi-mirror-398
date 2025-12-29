"""Data loading utilities for BabelVec."""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Union


def load_parallel_data(
    path: Union[str, Path],
    format: str = "auto",
) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """
    Load parallel sentence data from file.

    Supports formats:
    - JSON: {"en-fr": [["hello", "bonjour"], ...]}
    - TSV: lang1<tab>lang2<tab>sent1<tab>sent2

    Args:
        path: Path to parallel data file
        format: File format ('json', 'tsv', 'auto')

    Returns:
        Dict mapping (lang1, lang2) to list of (sent1, sent2) pairs
    """
    path = Path(path)

    if format == "auto":
        if path.suffix == ".json":
            format = "json"
        elif path.suffix in (".tsv", ".txt"):
            format = "tsv"
        else:
            format = "json"

    if format == "json":
        return _load_parallel_json(path)
    elif format == "tsv":
        return _load_parallel_tsv(path)
    else:
        raise ValueError(f"Unknown format: {format}")


def _load_parallel_json(path: Path) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """Load parallel data from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for key, pairs in data.items():
        # Parse key like "en-fr" or "en_fr"
        if "-" in key:
            lang1, lang2 = key.split("-", 1)
        elif "_" in key:
            lang1, lang2 = key.split("_", 1)
        else:
            continue

        result[(lang1, lang2)] = [(p[0], p[1]) for p in pairs]

    return result


def _load_parallel_tsv(path: Path) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """Load parallel data from TSV file."""
    result: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 4:
                lang1, lang2, sent1, sent2 = parts[:4]
                key = (lang1, lang2)
                if key not in result:
                    result[key] = []
                result[key].append((sent1, sent2))

    return result


def load_word_pairs(
    path: Union[str, Path],
    format: str = "auto",
) -> List[Tuple[str, str, float]]:
    """
    Load word similarity pairs from file.

    Supports formats:
    - TSV: word1<tab>word2<tab>score
    - JSON: [{"word1": "...", "word2": "...", "score": ...}, ...]

    Args:
        path: Path to word pairs file
        format: File format ('json', 'tsv', 'auto')

    Returns:
        List of (word1, word2, score) tuples
    """
    path = Path(path)

    if format == "auto":
        if path.suffix == ".json":
            format = "json"
        else:
            format = "tsv"

    if format == "json":
        return _load_word_pairs_json(path)
    elif format == "tsv":
        return _load_word_pairs_tsv(path)
    else:
        raise ValueError(f"Unknown format: {format}")


def _load_word_pairs_json(path: Path) -> List[Tuple[str, str, float]]:
    """Load word pairs from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [(d["word1"], d["word2"], float(d["score"])) for d in data]


def _load_word_pairs_tsv(path: Path) -> List[Tuple[str, str, float]]:
    """Load word pairs from TSV file."""
    result = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 3:
                word1, word2, score = parts[:3]
                result.append((word1, word2, float(score)))

    return result


def load_analogies(
    path: Union[str, Path],
) -> List[Tuple[str, str, str, str]]:
    """
    Load word analogies from file.

    Format: word1 word2 word3 word4 (space-separated)
    Represents: word1:word2 :: word3:word4

    Args:
        path: Path to analogies file

    Returns:
        List of (a, b, c, d) tuples
    """
    path = Path(path)
    result = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(":") or not line:
                continue

            parts = line.split()
            if len(parts) >= 4:
                result.append((parts[0], parts[1], parts[2], parts[3]))

    return result
