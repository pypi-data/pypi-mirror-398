# BabelVec

**Position-aware, cross-lingually aligned word embeddings built on FastText.**

[![PyPI version](https://badge.fury.io/py/babelvec.svg)](https://badge.fury.io/py/babelvec)
[![License](https://img.shields.io/badge/licence-MIT-green)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Position-Aware Embeddings**: Word order matters! Uses RoPE, sinusoidal, or decay positional encoding
- **Cross-Lingual Alignment**: Ensemble alignment (Procrustes + InfoNCE) for multilingual compatibility
- **FastText Foundation**: Handles OOV words through subword information
- **Multiple Training Modes**: Monolingual, multilingual, or post-hoc alignment

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

# Position-aware sentence embedding (order matters)
vec1 = model.get_sentence_vector("The dog bites the man", method='rope')
vec2 = model.get_sentence_vector("The man bites the dog", method='rope')
# vec1 != vec2 because word order is different!

# Standard averaging (order-agnostic)
vec_avg = model.get_sentence_vector("The dog bites the man", method='average')
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

model = train_multilingual(
    languages=['en', 'fr', 'de'],
    corpus_paths={'en': 'en.txt', 'fr': 'fr.txt', 'de': 'de.txt'},
    dim=300,
    alignment='ensemble'
)
```

### Post-hoc Alignment

```python
from babelvec.training import align_models

aligned = align_models(
    models={'en': model_en, 'fr': model_fr},
    method='ensemble',
    parallel_data=parallel_sentences
)
```

## Positional Encoding Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `average` | Simple averaging (no position) | Bag-of-words tasks |
| `rope` | Rotary Position Embedding | Best for semantic similarity |
| `sinusoidal` | Transformer-style positional | General purpose |
| `decay` | Exponential position decay | Emphasis on early words |

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