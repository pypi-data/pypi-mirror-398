# How to Use santok_complete Module

## Quick Start

### Option 1: Import from Parent Directory

```python
import sys
import os

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import santok_complete
from santok_complete import TextTokenizationEngine

# Use it
engine = TextTokenizationEngine()
result = engine.tokenize("Hello World!")
print(result)
```

### Option 2: Direct Import (if parent is in path)

```python
import sys
sys.path.insert(0, r'C:\Users\SCHAVALA\Downloads\SanTOK-Extracted\SanTOK-9a284bcf1b497d32e2041726fa2bba1e662d2770')

import santok_complete
from santok_complete import TextTokenizationEngine
```

### Option 3: Install as Package

```bash
cd santok_complete
pip install -e .
```

## Basic Usage Examples

### 1. Tokenization

```python
from santok_complete import TextTokenizationEngine

engine = TextTokenizationEngine()
result = engine.tokenize("Hello World!", tokenization_method="whitespace")
print(f"Tokens: {result['tokens']}")
```

### 2. Embeddings

```python
from santok_complete import SanTOKEmbeddingGenerator

generator = SanTOKEmbeddingGenerator()
embeddings = generator.generate("Text to embed")
print(f"Embedding shape: {embeddings.shape}")
```

### 3. Vector Store

```python
from santok_complete import SanTOKVectorStore

store = SanTOKVectorStore()
store.add(embeddings, metadata={"text": "Hello"})
results = store.search(query_embedding)
```

### 4. Training

```python
from santok_complete import SanTOKVocabularyBuilder

builder = SanTOKVocabularyBuilder()
vocab = builder.build_from_text("training text corpus")
```

### 5. Complete Analysis

```python
from santok_complete import TextTokenizationEngine

engine = TextTokenizationEngine()
analysis = engine.analyze_text_comprehensive("Your text here")
print(analysis)
```

## Available Imports

```python
from santok_complete import (
    # Core
    TextTokenizationEngine,
    TextTokenizer,
    
    # Embeddings
    SanTOKEmbeddingGenerator,
    SanTOKVectorStore,
    
    # Training
    SanTOKVocabularyBuilder,
    SanTOKLanguageModel,
    
    # Utils
    Config,
    setup_logging,
    validate_text_input,
)
```

## Running from Command Line

```bash
# From santok_complete directory
python -m santok_complete.cli.cli "Hello World"
```

