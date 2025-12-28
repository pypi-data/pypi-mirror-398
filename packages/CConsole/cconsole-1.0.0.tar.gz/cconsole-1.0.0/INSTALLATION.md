# Installation Guide

## Local Installation (Without Publishing)

### Method 1: Editable Install (Recommended for Development)

Navigate to the project directory and run:

```bash
cd path/to/CoolCmd
pip install -e .
```

This installs the package in "editable" mode. Changes to source files are reflected immediately.

### Method 2: Direct Install from Directory

```bash
pip install path/to/CoolCmd
```

### Method 3: Build and Install Wheel

```bash
cd path/to/CoolCmd
pip install build
python -m build
pip install dist/CConsole-1.0.0-py3-none-any.whl
```

### Method 4: Install from Git (Private Repo)

```bash
pip install git+https://github.com/username/CConsole.git
```

Or with SSH:
```bash
pip install git+ssh://git@github.com/username/CConsole.git
```

## Verify Installation

```python
from CConsole import Console
print(Console)
```

## Uninstall

```bash
pip uninstall CConsole
```

## Publishing to PyPI (When Ready)

### 1. Create PyPI Account
Register at https://pypi.org/account/register/

### 2. Install Tools
```bash
pip install build twine
```

### 3. Build Package
```bash
python -m build
```

### 4. Upload to TestPyPI (Optional)
```bash
twine upload --repository testpypi dist/*
```

### 5. Upload to PyPI
```bash
twine upload dist/*
```

## Troubleshooting

**Import Error:**
Ensure you're in the correct Python environment.

**Permission Error:**
Run terminal as administrator or use `--user` flag:
```bash
pip install --user -e .
```
