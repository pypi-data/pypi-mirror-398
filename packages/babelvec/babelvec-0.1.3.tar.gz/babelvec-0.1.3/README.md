# BabelVec

**Position-aware, cross-lingually aligned word embeddings built on FastText.**

[![PyPI version](https://badge.fury.io/py/babelvec.svg)](https://badge.fury.io/py/babelvec)
[![License](https://img.shields.io/badge/licence-MIT-green)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Cross-Lingual Alignment**: Procrustes alignment for multilingual compatibility
- **Position-Aware Embeddings**: Optional positional encoding (RoPE, sinusoidal, decay)
- **FastText Foundation**: Handles OOV words through subword information

## Installation

```bash
pip install babelvec
```

For visualization support:
```bash
pip install babelvec[viz]
```

## Quick Start

```python
from babelvec import BabelVec

# Load a model
model = BabelVec.load('path/to/model.bin')

# Get word vector
vec = model.get_word_vector("hello")

# Position-aware sentence embedding
vec1 = model.get_sentence_vector("The dog bites the man", method='rope')
vec2 = model.get_sentence_vector("The man bites the dog", method='rope')
# vec1 != vec2 because word order is encoded

# Simple averaging (no position encoding)
vec = model.get_sentence_vector("Hello world", method='average')
```

## Training

### Monolingual Training

```python
from babelvec.training import train_monolingual

model = train_monolingual(
    lang='en',
    corpus_path='corpus.txt',
    dim=300,
    epochs=5
)
model.save('en_300d.bin')
```

### Multilingual Training with Alignment

```python
from babelvec.training import train_multilingual

models = train_multilingual(
    languages=['en', 'ar'],
    corpus_paths={'en': 'en.txt', 'ar': 'ar.txt'},
    parallel_data={('en', 'ar'): parallel_pairs},
    alignment='procrustes'
)
```

### Post-hoc Alignment

```python
from babelvec.training import align_models

aligned = align_models(
    models={'en': model_en, 'ar': model_ar},
    parallel_data={('en', 'ar'): parallel_pairs},
    method='procrustes'
)
```

## Model Save/Load (v0.1.3+)

Models save projection matrices alongside the FastText binary:

```python
# Save model
model.save('model.bin')
# Creates: model.bin, model.projection.npy (if aligned), model.meta.json

# Load model - projection is automatically restored
model = BabelVec.load('model.bin')
print(model.is_aligned)  # True if projection was loaded
```

## Encoding Methods

| Method | Description |
|--------|-------------|
| `rope` | Rotary Position Embedding |
| `decay` | Exponential position decay |
| `sinusoidal` | Transformer-style positional encoding |
| `average` | Simple averaging (no position encoding) |

## Evaluation

```python
from babelvec.evaluation import cross_lingual_retrieval

metrics = cross_lingual_retrieval(
    model_src=model_en,
    model_tgt=model_ar,
    parallel_sentences=test_pairs,
    method='rope'
)
print(f"Recall@1: {metrics['recall@1']:.3f}")
```

## Examples

See the `examples/` directory:

- `01_basic_usage.py` - Getting started

## Citation

```bibtex
@software{babelvec2025,
  title = {BabelVec: Position-Aware Cross-Lingual Word Embeddings},
  author = {Kamali, Omar},
  year = {2025},
  url = {https://github.com/omarkamali/babelvec}
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

Copyright © 2025 [Omar Kamali](https://omarkamali.com)