# Prompt 01: Project Setup

## Task

Set up the TurboSEO Python project structure with modern packaging.

## Requirements

1. Create the directory structure:
```
turboseo/
├── src/
│   └── turboseo/
│       ├── __init__.py
│       ├── analyzers/
│       │   └── __init__.py
│       └── cli/
│           └── __init__.py
├── tests/
│   └── __init__.py
├── pyproject.toml
├── README.md
└── LICENSE
```

2. Create `pyproject.toml` with:
   - Name: `turboseo`
   - Python: `>=3.10`
   - Dependencies:
     - `click` (CLI)
     - `rich` (terminal output)
     - `textstat` (readability)
     - `pydantic` (data validation)
   - Dev dependencies:
     - `pytest`
     - `pytest-cov`
     - `ruff` (linting)
   - CLI entry point: `turboseo`

3. Create minimal `README.md` with:
   - Project name and tagline
   - Installation instructions
   - Basic usage

4. Add MIT LICENSE file

5. Create `src/turboseo/__init__.py` with version `0.1.0`

## Acceptance Criteria

- [ ] `pip install -e .` works
- [ ] `turboseo --help` shows CLI help
- [ ] `pytest` runs (even with no tests)
- [ ] `ruff check .` passes
