# SanTOK Complete - Comprehensive Text Processing System

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SanTOK Complete** is a comprehensive, production-ready text processing system that goes far beyond simple tokenization. It provides a complete toolkit for text analysis, semantic understanding, model training, vector storage, API deployment, and more.

## 🎯 What is SanTOK Complete?

SanTOK Complete is **NOT just a tokenizer** - it's a complete NLP (Natural Language Processing) system that includes:

- ✅ **Multiple Tokenization Methods** - Space, word, character, grammar, subword tokenization
- ✅ **Semantic Embeddings** - Generate embeddings for semantic analysis
- ✅ **Vector Stores** - Weaviate and other vector database integrations
- ✅ **Model Training** - Vocabulary building, language model training
- ✅ **API Servers** - Production-ready FastAPI servers
- ✅ **Data Integration** - Source map integration, vocabulary adaptation
- ✅ **Data Interpretation** - Text analysis and interpretation
- ✅ **Compression** - Text compression algorithms
- ✅ **Performance Testing** - Benchmarking and performance analysis
- ✅ **CLI Tools** - Command-line interfaces
- ✅ **Utilities** - Configuration, logging, validation

---

## 📋 Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Components](#core-components)
4. [Detailed Usage](#detailed-usage)
5. [API Reference](#api-reference)
6. [Examples](#examples)
7. [Architecture](#architecture)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)
10. [License](#license)

---

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Method 1: Install as Package (Recommended)

```bash
# Navigate to the module directory
cd santok_complete

# Install in editable mode (recommended for development)
pip install -e .

# Or install normally
pip install .
```

### Method 2: Add to Python Path

If you don't want to install, you can add the parent directory to your Python path:

```python
import sys
import os
sys.path.insert(0, r'C:\path\to\SanTOK-Extracted\SanTOK-9a284bcf1b497d32e2041726fa2bba1e662d2770')

import santok_complete
```

### Method 3: Set Environment Variable

**Windows:**
```cmd
set PYTHONPATH=%PYTHONPATH%;C:\path\to\SanTOK-Extracted\SanTOK-9a284bcf1b497d32e2041726fa2bba1e662d2770
```

**Linux/Mac:**
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/SanTOK-Extracted/SanTOK-9a284bcf1b497d32e2041726fa2bba1e662d2770"
```

### Verify Installation

```python
import santok_complete
print(f"SanTOK Complete Version: {santok_complete.__version__}")

from santok_complete import TextTokenizationEngine
engine = TextTokenizationEngine()
print("✅ Installation successful!")
```

---

## ⚡ Quick Start

### Basic Tokenization

```python
from santok_complete import TextTokenizationEngine

# Create engine instance
engine = TextTokenizationEngine(
    random_seed=12345,
    normalize_case=True,
    remove_punctuation=False
)

# Tokenize text
text = "Hello World! This is SanTOK Complete."
result = engine.tokenize(text, tokenization_method="whitespace")

print(f"Tokens: {result['tokens']}")
print(f"Method: {result['method']}")
```

### Generate Embeddings

```python
from santok_complete import SanTOKEmbeddingGenerator

generator = SanTOKEmbeddingGenerator()
embeddings = generator.generate("Your text here")
print(f"Embedding shape: {embeddings.shape}")
```

### Use Vector Store

```python
from santok_complete import SanTOKVectorStore

store = SanTOKVectorStore()
store.add(embeddings, metadata={"text": "Hello", "id": 1})
results = store.search(query_embedding, top_k=5)
```

---

## 🏗️ Core Components

### 1. Core Tokenization (`core/`)

The foundation of SanTOK Complete provides multiple tokenization methods:

- **TextTokenizationEngine** - Main tokenization engine with multiple methods
- **TextTokenizer** - Core tokenizer class
- **BaseTokenizer** - Base class for custom tokenizers
- **ParallelTokenizer** - Parallel processing support

**Available Tokenization Methods:**
- `whitespace` - Split by whitespace
- `word` - Word-based tokenization
- `character` - Character-level tokenization
- `grammar` - Grammar-aware tokenization
- `subword` - Subword tokenization

### 2. Embeddings (`embeddings/`)

Generate semantic embeddings for text analysis:

- **SanTOKEmbeddingGenerator** - Generate embeddings from text
- **SanTOKVectorStore** - Store and search embeddings
- **SanTOKInferencePipeline** - Inference pipeline for embeddings
- **SemanticTrainer** - Train semantic models

### 3. Training (`training/`)

Train and build language models:

- **SanTOKVocabularyBuilder** - Build vocabularies from text
- **SanTOKLanguageModelTrainer** - Train language models
- **SanTOKLanguageModel** - Language model class
- **EnhancedTrainer** - Enhanced training capabilities
- **DatasetDownloader** - Download training datasets

### 4. Vector Stores (`vector_stores/`)

Integrate with vector databases:

- **Weaviate Integration** - Full Weaviate vector database support
- Vector search and retrieval
- Metadata management

### 5. API Servers (`servers/`)

Production-ready API servers:

- **MainServer** - Full-featured FastAPI server
- **LightweightServer** - Lightweight API server
- **SimpleServer** - Simple HTTP server
- **JobManager** - Job management system
- **AdminConfig** - Admin configuration

### 6. Integration (`integration/`)

System integration modules:

- **VocabularyAdapter** - Adapt vocabularies between systems
- **SourceMapIntegration** - Source map integration

### 7. Interpretation (`interpretation/`)

Text analysis and interpretation:

- **DataInterpreter** - Interpret and analyze text data

### 8. Compression (`compression/`)

Text compression algorithms:

- **CompressionAlgorithm** - Various compression methods

### 9. Performance (`performance/`)

Testing and benchmarking:

- **TestAccuracy** - Accuracy testing
- **ComprehensivePerformanceTest** - Full performance testing
- **TestOrganizedOutputs** - Output validation

### 10. CLI (`cli/`)

Command-line interfaces:

- **Main CLI** - Primary command-line interface
- **Decode Demo** - Decoding demonstrations

### 11. Utilities (`utils/`)

Supporting utilities:

- **Config** - Configuration management
- **Logging** - Logging setup and management
- **Validation** - Input validation functions

---

## 📖 Detailed Usage

### Text Tokenization

#### Basic Tokenization

```python
from santok_complete import TextTokenizationEngine

engine = TextTokenizationEngine()
result = engine.tokenize("Hello World!", tokenization_method="whitespace")

# Access tokens
tokens = result['tokens']
for token in tokens:
    print(f"Text: {token['text']}, Index: {token['index']}")
```

#### Advanced Tokenization

```python
engine = TextTokenizationEngine(
    random_seed=12345,           # For reproducibility
    embedding_bit=False,          # Enable embedding bit
    normalize_case=True,          # Normalize to lowercase
    remove_punctuation=False,     # Keep punctuation
    collapse_repetitions=0        # No repetition collapsing
)

# Use different methods
methods = ["whitespace", "word", "character", "grammar", "subword"]

for method in methods:
    result = engine.tokenize("Your text here", tokenization_method=method)
    print(f"{method}: {len(result['tokens'])} tokens")
```

#### Comprehensive Text Analysis

```python
analysis = engine.analyze_text_comprehensive("Your text here")

# Analysis includes multiple tokenization methods
for method, data in analysis.items():
    print(f"{method}: {len(data['tokens'])} tokens")
```

### Semantic Embeddings

#### Generate Embeddings

```python
from santok_complete import SanTOKEmbeddingGenerator

generator = SanTOKEmbeddingGenerator()

# Generate embeddings
text = "This is sample text for embedding generation"
embeddings = generator.generate(text)

print(f"Embedding dimension: {embeddings.shape}")
print(f"Embedding vector: {embeddings}")
```

#### Batch Embedding Generation

```python
texts = ["First text", "Second text", "Third text"]
embeddings_list = [generator.generate(text) for text in texts]
```

### Vector Stores

#### Using SanTOK Vector Store

```python
from santok_complete import SanTOKVectorStore

store = SanTOKVectorStore()

# Add documents
doc1_embedding = generator.generate("Document 1 text")
doc2_embedding = generator.generate("Document 2 text")

store.add(doc1_embedding, metadata={"id": 1, "title": "Doc 1"})
store.add(doc2_embedding, metadata={"id": 2, "title": "Doc 2"})

# Search
query_embedding = generator.generate("Search query")
results = store.search(query_embedding, top_k=5)

for result in results:
    print(f"Score: {result['score']}, Metadata: {result['metadata']}")
```

#### Weaviate Integration

```python
from santok_complete.vector_stores.weaviate_integration import *

# Connect to Weaviate
client = connect_weaviate(url="http://localhost:8080")

# Store vectors
store_vector(client, embeddings, metadata={"text": "Sample"})

# Search
results = search_vectors(client, query_embedding, limit=10)
```

### Model Training

#### Build Vocabulary

```python
from santok_complete import SanTOKVocabularyBuilder

builder = SanTOKVocabularyBuilder()

# Build from text corpus
corpus = "Your training text corpus here..."
vocabulary = builder.build_from_text(corpus)

print(f"Vocabulary size: {len(vocabulary)}")
print(f"Vocabulary: {vocabulary}")
```

#### Train Language Model

```python
from santok_complete import SanTOKLanguageModelTrainer

trainer = SanTOKLanguageModelTrainer()

# Train model
model = trainer.train(
    training_data="path/to/training/data",
    epochs=10,
    batch_size=32
)

# Save model
model.save("path/to/save/model")
```

### API Server Deployment

#### Start Main Server

```python
from santok_complete.servers.main_server import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Start Lightweight Server

```python
from santok_complete.servers.lightweight_server import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8001)
```

#### Using the CLI

```bash
# From command line
python -m santok_complete.cli.cli "Hello World" --method whitespace

# Or if installed
santok "Hello World" --method word
```

---

## 📚 API Reference

### TextTokenizationEngine

Main tokenization engine class.

#### Constructor

```python
TextTokenizationEngine(
    random_seed: int = 12345,
    embedding_bit: bool = False,
    normalize_case: bool = True,
    remove_punctuation: bool = False,
    collapse_repetitions: int = 0
)
```

**Parameters:**
- `random_seed` (int): Seed for reproducible tokenization (default: 12345)
- `embedding_bit` (bool): Enable embedding bit for extra variation (default: False)
- `normalize_case` (bool): Convert text to lowercase (default: True)
- `remove_punctuation` (bool): Remove punctuation (default: False)
- `collapse_repetitions` (int): Collapse repeated characters (0=disabled, 1=run-aware, N=collapse to N) (default: 0)

#### Methods

##### `tokenize(text: str, tokenization_method: str = "whitespace") -> dict`

Tokenize input text using specified method.

**Parameters:**
- `text` (str): Input text to tokenize
- `tokenization_method` (str): Method to use ("whitespace", "word", "character", "grammar", "subword")

**Returns:**
- `dict`: Dictionary containing:
  - `tokens`: List of token dictionaries with 'text' and 'index'
  - `method`: Tokenization method used
  - `count`: Number of tokens

**Example:**
```python
result = engine.tokenize("Hello World!", "whitespace")
# Returns: {
#     'tokens': [{'text': 'Hello', 'index': 0}, {'text': 'World!', 'index': 1}],
#     'method': 'whitespace',
#     'count': 2
# }
```

##### `analyze_text_comprehensive(text: str) -> dict`

Analyze text using all available tokenization methods.

**Parameters:**
- `text` (str): Input text to analyze

**Returns:**
- `dict`: Dictionary with results for each method

**Example:**
```python
analysis = engine.analyze_text_comprehensive("Hello World!")
# Returns: {
#     'whitespace': {'tokens': [...], 'count': 2},
#     'word': {'tokens': [...], 'count': 2},
#     'character': {'tokens': [...], 'count': 12},
#     ...
# }
```

### SanTOKEmbeddingGenerator

Generate semantic embeddings from text.

#### Constructor

```python
SanTOKEmbeddingGenerator(config: dict = None)
```

#### Methods

##### `generate(text: str) -> numpy.ndarray`

Generate embedding vector for input text.

**Parameters:**
- `text` (str): Input text

**Returns:**
- `numpy.ndarray`: Embedding vector

### SanTOKVectorStore

Store and search embeddings.

#### Methods

##### `add(embedding: np.ndarray, metadata: dict = None) -> str`

Add embedding to the store.

**Parameters:**
- `embedding` (np.ndarray): Embedding vector
- `metadata` (dict): Optional metadata

**Returns:**
- `str`: ID of stored embedding

##### `search(query_embedding: np.ndarray, top_k: int = 10) -> list`

Search for similar embeddings.

**Parameters:**
- `query_embedding` (np.ndarray): Query embedding vector
- `top_k` (int): Number of results to return

**Returns:**
- `list`: List of results with 'score' and 'metadata'

---

## 💡 Examples

### Example 1: Complete Text Processing Pipeline

```python
from santok_complete import (
    TextTokenizationEngine,
    SanTOKEmbeddingGenerator,
    SanTOKVectorStore
)

# Initialize components
engine = TextTokenizationEngine()
generator = SanTOKEmbeddingGenerator()
store = SanTOKVectorStore()

# Process text
text = "SanTOK Complete is a comprehensive text processing system."

# Tokenize
tokens_result = engine.tokenize(text, "whitespace")
print(f"Tokens: {[t['text'] for t in tokens_result['tokens']]}")

# Generate embedding
embedding = generator.generate(text)
print(f"Embedding shape: {embedding.shape}")

# Store in vector database
doc_id = store.add(embedding, metadata={"text": text, "source": "example"})
print(f"Stored document ID: {doc_id}")

# Search
query_text = "text processing"
query_embedding = generator.generate(query_text)
results = store.search(query_embedding, top_k=3)
print(f"Search results: {len(results)} found")
```

### Example 2: Training a Custom Model

```python
from santok_complete import (
    SanTOKVocabularyBuilder,
    SanTOKLanguageModelTrainer
)

# Build vocabulary
builder = SanTOKVocabularyBuilder()
vocab = builder.build_from_text("Your training corpus...")
print(f"Vocabulary size: {len(vocab)}")

# Train model
trainer = SanTOKLanguageModelTrainer()
model = trainer.train(
    training_data="path/to/data",
    vocabulary=vocab,
    epochs=10
)

# Use model
predictions = model.predict("Input text")
```

### Example 3: API Server with Custom Endpoints

```python
from santok_complete.servers.main_server import app
from santok_complete import TextTokenizationEngine
from fastapi import FastAPI

engine = TextTokenizationEngine()

@app.post("/tokenize")
async def tokenize_endpoint(text: str, method: str = "whitespace"):
    result = engine.tokenize(text, method)
    return result

# Run server
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 🏛️ Architecture

### Module Structure

```
santok_complete/
├── __init__.py              # Main module exports
├── README.md                # This file
├── INSTALL.md               # Installation guide
├── HOW_TO_USE.md            # Usage guide
├── setup.py                 # Package setup
│
├── core/                    # Core tokenization
│   ├── core_tokenizer.py   # Core tokenizer implementation
│   ├── base_tokenizer.py   # Base tokenizer class
│   ├── parallel_tokenizer.py # Parallel processing
│   └── santok_engine.py    # Main engine
│
├── embeddings/              # Embedding generation
│   ├── embedding_generator.py
│   ├── vector_store.py
│   ├── inference_pipeline.py
│   └── semantic_trainer.py
│
├── training/                # Model training
│   ├── vocabulary_builder.py
│   ├── language_model_trainer.py
│   └── enhanced_trainer.py
│
├── servers/                 # API servers
│   ├── main_server.py
│   ├── lightweight_server.py
│   └── job_manager.py
│
├── vector_stores/           # Vector database integrations
│   └── weaviate_integration.py
│
├── integration/             # System integration
│   ├── vocabulary_adapter.py
│   └── source_map_integration.py
│
├── interpretation/          # Text interpretation
│   └── data_interpreter.py
│
├── compression/             # Compression algorithms
│   └── compression_algorithms.py
│
├── performance/             # Performance testing
│   ├── test_accuracy.py
│   └── comprehensive_performance_test.py
│
├── cli/                     # Command-line interfaces
│   ├── cli.py
│   └── main.py
│
└── utils/                   # Utilities
    ├── config.py
    ├── logging_config.py
    └── validation.py
```

### Data Flow

```
Input Text
    ↓
TextTokenizationEngine (Tokenization)
    ↓
Tokens
    ↓
SanTOKEmbeddingGenerator (Embedding Generation)
    ↓
Embeddings
    ↓
SanTOKVectorStore (Storage & Search)
    ↓
Results
```

---

## 🔧 Troubleshooting

### Common Issues

#### Import Error

**Problem:** `ModuleNotFoundError: No module named 'santok_complete'`

**Solution:**
1. Ensure you've installed the package: `pip install -e .`
2. Check Python path includes the parent directory
3. Verify you're using the correct Python environment

#### Tokenization Method Not Found

**Problem:** `ValueError: Unknown tokenization method`

**Solution:**
Use one of the supported methods: `"whitespace"`, `"word"`, `"character"`, `"grammar"`, `"subword"`

#### Embedding Generation Fails

**Problem:** Embedding generation returns errors

**Solution:**
1. Ensure input text is not empty
2. Check that required dependencies are installed
3. Verify model files are present (if using pre-trained models)

#### Server Won't Start

**Problem:** API server fails to start

**Solution:**
1. Check if port is already in use
2. Verify uvicorn is installed: `pip install uvicorn`
3. Check firewall settings

### Getting Help

- Check the documentation files: `INSTALL.md`, `HOW_TO_USE.md`
- Review examples in the `examples/` directory
- Check GitHub issues for known problems

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Santosh Chavala**

- GitHub: [@chavalasantosh](https://github.com/chavalasantosh)
- Repository: [SanTOK](https://github.com/chavalasantosh/SanTOK)

---

## 🙏 Acknowledgments

- Built with Python
- Uses FastAPI for API servers
- Integrates with Weaviate for vector storage
- Thanks to all contributors

---

## 📊 Statistics

- **Total Files:** 125+ Python files
- **Lines of Code:** 48,000+
- **Components:** 11 major modules
- **Tokenization Methods:** 5+
- **Supported Python Versions:** 3.7+

---

**SanTOK Complete** - Your complete solution for text processing, from tokenization to production deployment.
