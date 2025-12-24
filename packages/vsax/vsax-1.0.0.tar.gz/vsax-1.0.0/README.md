# VSAX: Vector Symbolic Algebra for JAX

[![PyPI version](https://img.shields.io/pypi/v/vsax.svg)](https://pypi.org/project/vsax/)
[![Python Version](https://img.shields.io/pypi/pyversions/vsax.svg)](https://pypi.org/project/vsax/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-github%20pages-blue)](https://vasanthsarathy.github.io/vsax/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

VSAX is a GPU-accelerated, JAX-native Python library for Vector Symbolic Architectures (VSAs). It provides composable symbolic representations using hypervectors, algebraic operations for binding and bundling, and encoding strategies for symbolic and structured data.

## Features

- 🚀 **Three VSA Models**: FHRR, MAP, and Binary implementations ✅
- 🏭 **Factory Functions**: One-line model creation with sensible defaults ✅
- 💾 **VSAMemory**: Dictionary-style symbol management ✅
- 📊 **5 Core Encoders**: Scalar, Sequence, Set, Dict, and Graph encoders ✅
- 🎨 **Custom Encoders**: Easy-to-extend AbstractEncoder base class ✅
- 🔍 **Similarity Metrics**: Cosine, dot, and Hamming similarity ✅
- ⚡ **Batch Operations**: GPU-accelerated vmap operations for parallel processing ✅
- 💾 **I/O & Persistence**: Save/load basis vectors to JSON ✅
- 🎮 **GPU Utilities**: Device management, benchmarking, CPU/GPU comparison ✅ **NEW in v0.7.2**
- 🚀 **GPU-Accelerated**: Built on JAX for automatic GPU acceleration (5-30x speedup)
- 🧩 **Modular Architecture**: Clean separation between representations and operations
- 🧬 **Complete Representations**: Complex, Real, and Binary hypervectors ✅
- ⚙️ **Full Operation Sets**: FFT-based FHRR, MAP, and XOR/majority Binary ops ✅
- 🎲 **Random Sampling**: Sampling utilities for all representation types ✅
- 📚 **Comprehensive Documentation**: Full API docs and examples ✅
- 📓 **Interactive Tutorials**: Jupyter notebooks with real datasets (MNIST, knowledge graphs) ✅ **NEW in v0.7.1**
- ✅ **96% Test Coverage**: 377 tests ensuring reliability

## Installation

### From PyPI (Recommended)

```bash
pip install vsax
```

Or with uv:

```bash
uv pip install vsax
```

### From Source

#### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. Install it first:

```bash
# Install uv (Unix/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install uv (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install VSAX:

```bash
git clone https://github.com/vasanthsarathy/vsax.git
cd vsax

# Create virtual environment and install package
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

#### Using pip

```bash
git clone https://github.com/vasanthsarathy/vsax.git
cd vsax
pip install -e .
```

### Development Installation

#### Using uv (Recommended)

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev,docs]"
```

#### Using pip

```bash
pip install -e ".[dev,docs]"
```

## Quick Start

**New in v0.6.0:** Save and load basis vectors!

### Simple Example

```python
from vsax import create_fhrr_model, VSAMemory, DictEncoder, save_basis, load_basis
from vsax.similarity import cosine_similarity
from vsax.utils import vmap_bind

# Create model with factory function (one line!)
model = create_fhrr_model(dim=512)

# Create memory for symbol management
memory = VSAMemory(model)

# Add symbols - automatically samples and stores hypervectors
memory.add_many(["subject", "action", "dog", "run", "cat", "jump"])

# Dictionary-style access
dog = memory["dog"]

# Encode structured data with DictEncoder
encoder = DictEncoder(model, memory)
sentence = encoder.encode({"subject": "dog", "action": "run"})

# Bind concepts (circular convolution)
dog_is_animal = model.opset.bind(dog.vec, memory["animal"].vec)

# Bundle concepts (sum and normalize)
pets = model.opset.bundle(memory["dog"].vec, memory["cat"].vec)

# NEW: Similarity search
similarity = cosine_similarity(memory["dog"], memory["cat"])
print(f"Dog-Cat similarity: {similarity:.3f}")

# NEW: Batch operations (GPU-accelerated)
import jax.numpy as jnp
nouns = jnp.stack([memory["dog"].vec, memory["cat"].vec])
verbs = jnp.stack([memory["run"].vec, memory["jump"].vec])
actions = vmap_bind(model.opset, nouns, verbs)  # Parallel binding!

# NEW: Save and load basis vectors
save_basis(memory, "my_basis.json")  # Persist to JSON
memory_new = VSAMemory(model)
load_basis(memory_new, "my_basis.json")  # Load from JSON
```

### All Three Models

VSAX supports three VSA models, all with the same simple API:

```python
from vsax import create_fhrr_model, create_map_model, create_binary_model, VSAMemory

# FHRR: Complex hypervectors, exact unbinding
fhrr = create_fhrr_model(dim=512)

# MAP: Real hypervectors, approximate unbinding
map_model = create_map_model(dim=512)

# Binary: Discrete hypervectors, exact unbinding
binary = create_binary_model(dim=10000, bipolar=True)

# Same interface for all models!
for model in [fhrr, map_model, binary]:
    memory = VSAMemory(model)
    memory.add("concept")
    vec = memory["concept"]
```

### Advanced: Manual Model Creation

You can still create models manually if you need custom configuration:

```python
from vsax import VSAModel, ComplexHypervector, FHRROperations, sample_complex_random

model = VSAModel(
    dim=512,
    rep_cls=ComplexHypervector,
    opset=FHRROperations(),
    sampler=sample_complex_random
)
```

See [docs/design-spec.md](docs/design-spec.md) for complete technical specification.

## Development Status

Currently in **Iteration 6: I/O & Persistence** ✅

### Completed

**Iteration 1** (v0.1.0): Foundation & Infrastructure ✅
- ✅ Core abstract classes (AbstractHypervector, AbstractOpSet)
- ✅ VSAModel dataclass
- ✅ Package structure
- ✅ Testing infrastructure (pytest, coverage)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Documentation site (MkDocs)
- ✅ Development tooling (ruff, mypy)

**Iteration 2** (v0.2.0): All 3 Representations + All 3 OpSets ✅
- ✅ ComplexHypervector, RealHypervector, BinaryHypervector
- ✅ FHRROperations, MAPOperations, BinaryOperations
- ✅ Sampling utilities (sample_random, sample_complex_random, sample_binary_random)
- ✅ 175 comprehensive tests with 96% coverage
- ✅ Full integration tests for all model combinations

**Iteration 3** (v0.3.0): VSAMemory + Factory Functions ✅
- ✅ VSAMemory class - dictionary-style symbol management
- ✅ Factory functions (create_fhrr_model, create_map_model, create_binary_model)
- ✅ Utility functions (coerce_to_array, validation helpers)
- ✅ 230 tests with 89% coverage
- ✅ Comprehensive documentation guides

**Iteration 4** (v0.4.0): Encoders + Examples ✅ **FIRST USABLE RELEASE!**
- ✅ ScalarEncoder - Numeric values with power encoding
- ✅ SequenceEncoder - Ordered sequences (lists, tuples)
- ✅ SetEncoder - Unordered collections (sets)
- ✅ DictEncoder - Key-value pairs (dictionaries)
- ✅ GraphEncoder - Graph structures (edge lists)
- ✅ AbstractEncoder - Base class for custom encoders
- ✅ Complete integration examples for all 3 models
- ✅ Custom encoder examples (DateEncoder, ColorEncoder)
- ✅ 280+ tests with 92%+ coverage

**Iteration 5** (v0.5.0): Similarity Metrics & Utilities ✅
- ✅ Cosine, dot, and Hamming similarity functions
- ✅ Batch operations with JAX vmap (vmap_bind, vmap_bundle, vmap_similarity)
- ✅ Visualization utilities (pretty_repr, format_similarity_results)
- ✅ GPU-accelerated similarity search
- ✅ Comprehensive examples (similarity_search.py, batch_operations.py)
- ✅ 319 tests with 95%+ coverage

**Iteration 6** (v0.6.0): I/O & Persistence ✅
- ✅ save_basis() and load_basis() functions
- ✅ JSON serialization for all 3 models
- ✅ Round-trip vector preservation
- ✅ Dimension and type validation
- ✅ Comprehensive tests (339 tests, 96% coverage)
- ✅ Complete examples and documentation

### Coming Next

**Iteration 7** (v1.0.0): Full Documentation & Production Release
- Complete API documentation
- Tutorial notebooks
- Production-ready v1.0.0 release

See [todo.md](todo.md) for the complete development roadmap.

## Documentation

- [Full Documentation](https://vasanthsarathy.github.io/vsax/)
- [Getting Started](docs/getting-started.md)
- [Modeling Guide](docs/modeling-guide.md) - **7-step workflow** for building VSA applications
- [Tutorials](docs/tutorials/index.md)
  - [MNIST Classification](docs/tutorials/01_mnist_classification.md) - Image classification with VSA
  - [Knowledge Graph Reasoning](docs/tutorials/02_knowledge_graph.md) - Multi-hop reasoning with relational facts
  - [Kanerva's "Dollar of Mexico"](docs/tutorials/03_kanerva_analogies.md) - Analogical reasoning and mapping
  - [Word Analogies & Random Indexing](docs/tutorials/04_word_analogies.md) - Word embeddings and semantic similarity
  - [Understanding VSA Models](docs/tutorials/05_model_comparison.md) - Compare FHRR, MAP, and Binary models
  - [VSA for Edge Computing](docs/tutorials/06_edge_computing.md) - Lightweight alternative to neural networks
  - [Hierarchical Structures](docs/tutorials/07_hierarchical_structures.md) - Trees and nested composition
  - [Multi-Modal Concept Grounding](docs/tutorials/08_multimodal_grounding.md) - Fuse vision, language, and arithmetic
  - [Neural-Symbolic Fusion (HD-Glue)](docs/tutorials/09_neural_symbolic_fusion.md) - Glue neural networks with VSA ✨ **NEW**
- [VSAX vs Other Libraries](docs/comparison.md) - Why VSAX? Feature comparison with torchhd, hdlib, PyBHV
- [Design Specification](docs/design-spec.md)
- [API Reference](https://vasanthsarathy.github.io/vsax/api/)
- [Contributing](CONTRIBUTING.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Development

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=vsax --cov-report=term-missing
```

Type checking:
```bash
mypy vsax
```

Linting:
```bash
ruff check vsax tests
```

Build documentation:
```bash
mkdocs serve
```

## License

VSAX is released under the MIT License. See [LICENSE](LICENSE) for details.

## Citation

If you use VSAX in your research, please cite:

```bibtex
@software{vsax2025,
  title = {VSAX: Vector Symbolic Algebra for JAX},
  author = {Sarathy, Vasanth},
  year = {2025},
  url = {https://github.com/vasanthsarathy/vsax},
  version = {1.0.0}
}
```

## Acknowledgments

VSAX is built on [JAX](https://github.com/google/jax) and inspired by the VSA/HDC research community.