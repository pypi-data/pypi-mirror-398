# Alethe

Alethe is an AI-powered code explainer and semantic diff tool. It generates human-readable markdown explanations for Python files and compares different versions to highlight semantic changes.

## Features

- Generate markdown explanations of Python code.
- Track file versions and compute semantic diffs between explanations.
- Works with local Hugging Face models or a stub mode for offline testing.
- CLI interface for easy usage.

## Installation

You can install Alethe from PyPI:

```bash
pip install alethe
```

## Usage

Basic CLI usage:

```bash
alethe explain path/to/file.py
alethe summary path/to/file.py
alethe diff path/to/file.py v1 v2
alethe list path/to/file.py
alethe rename old_file.py new_file.py
alethe getpath <file_id>
```

### Example

Generate an explanation for **example.py**:

```bash
alethe explain example.py
```
