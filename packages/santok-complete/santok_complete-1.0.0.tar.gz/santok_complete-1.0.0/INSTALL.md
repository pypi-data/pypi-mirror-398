# Installation Guide for santok_complete

## Installation Methods

### Method 1: Install as Editable Package (Recommended for Development)

```bash
# Navigate to the module directory
cd C:\Users\SCHAVALA\Downloads\SanTOK-Extracted\SanTOK-9a284bcf1b497d32e2041726fa2bba1e662d2770\santok_complete

# Install in editable mode (changes to code are immediately available)
pip install -e .
```

This installs the package in "editable" mode, meaning you can still modify the code and changes will be reflected immediately.

### Method 2: Install from Directory

```bash
# From parent directory
pip install ./santok_complete
```

### Method 3: Install from Source (Development)

```bash
# Clone or download the repository first, then:
cd santok_complete
pip install .
```

### Method 4: Use Without Installation (Add to Path)

If you don't want to install, you can add it to Python path:

```python
import sys
import os
sys.path.insert(0, r'C:\Users\SCHAVALA\Downloads\SanTOK-Extracted\SanTOK-9a284bcf1b497d32e2041726fa2bba1e662d2770\santok_complete')

import santok_complete
```

Or set PYTHONPATH environment variable:

**Windows:**
```cmd
set PYTHONPATH=%PYTHONPATH%;C:\Users\SCHAVALA\Downloads\SanTOK-Extracted\SanTOK-9a284bcf1b497d32e2041726fa2bba1e662d2770
```

**Linux/Mac:**
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/santok_complete/parent"
```

## Verify Installation

After installation, verify it works:

```python
import santok_complete
print(santok_complete.__version__)

from santok_complete import TextTokenizationEngine
engine = TextTokenizationEngine()
print("Installation successful!")
```

## Uninstall

To uninstall:

```bash
pip uninstall santok-complete
```

## Requirements

- Python 3.7 or higher
- No external dependencies required for basic tokenization (pure Python)
- Optional: TensorFlow, NumPy, etc. for advanced features (embeddings, training)

## Troubleshooting

### Issue: Module not found after installation

**Solution:** Make sure you're using the correct Python environment:
```bash
python -m pip install -e .
```

### Issue: Import errors

**Solution:** Check that all dependencies are installed if using advanced features:
```bash
pip install numpy tensorflow  # If needed
```

### Issue: Permission denied

**Solution:** Use `--user` flag:
```bash
pip install --user -e .
```

