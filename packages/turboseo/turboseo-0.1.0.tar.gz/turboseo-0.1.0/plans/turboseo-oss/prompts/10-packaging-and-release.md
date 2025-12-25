# Prompt 10: Packaging and Release

## Task

Prepare TurboSEO for public release on PyPI and GitHub.

## Requirements

### 1. Final pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "turboseo"
version = "0.1.0"
description = "SEO content toolkit that writes human, not AI"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    { name = "Your Name", email = "you@example.com" }
]
keywords = [
    "seo",
    "content",
    "writing",
    "ai-detection",
    "marketing",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Internet :: WWW/HTTP :: Site Management",
    "Topic :: Text Processing :: Linguistic",
]
dependencies = [
    "click>=8.0.0",
    "rich>=13.0.0",
    "textstat>=0.7.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
turboseo = "turboseo.cli.main:cli"

[project.urls]
Homepage = "https://github.com/yourusername/turboseo"
Documentation = "https://github.com/yourusername/turboseo#readme"
Repository = "https://github.com/yourusername/turboseo"
Issues = "https://github.com/yourusername/turboseo/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/turboseo"]

[tool.ruff]
target-version = "py310"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.isort]
known-first-party = ["turboseo"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=turboseo --cov-report=term-missing"

[tool.coverage.run]
source = ["src/turboseo"]
branch = true
```

### 2. GitHub Repository Setup

#### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
.venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# OS
.DS_Store
Thumbs.db

# Project specific
drafts/
research/
published/
topics/
context/*.md
!context/README.md
```

#### LICENSE (MIT)
```
MIT License

Copyright (c) 2024 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### CONTRIBUTING.md
```markdown
# Contributing to TurboSEO

Thanks for your interest in contributing!

## Development Setup

1. Clone the repo:
```bash
git clone https://github.com/yourusername/turboseo.git
cd turboseo
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

3. Install dev dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Code Style

We use Ruff for linting and formatting:

```bash
ruff check .
ruff format .
```

## Pull Request Process

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Run linter: `ruff check .`
6. Submit PR

## Adding AI Writing Patterns

If you find new AI writing patterns not in our list:

1. Add to `AI_VOCABULARY` or appropriate pattern list in `writing_standards.py`
2. Add tests in `test_writing_standards.py`
3. Update `docs/human-writing-rules.md`
4. Submit PR with examples

## Reporting Issues

Include:
- TurboSEO version
- Python version
- Sample content that shows the issue
- Expected vs actual behavior
```

### 3. GitHub Actions CI

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint with Ruff
        run: |
          ruff check .

      - name: Type check with mypy
        run: |
          mypy src/turboseo

      - name: Test with pytest
        run: |
          pytest --cov=turboseo --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  publish:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

### 4. Release Checklist

Before releasing:

- [ ] All tests pass
- [ ] Ruff shows no errors
- [ ] Version updated in `__init__.py` and `pyproject.toml`
- [ ] CHANGELOG updated
- [ ] README is accurate
- [ ] Documentation is complete

To release:

```bash
# Update version
# Edit pyproject.toml and src/turboseo/__init__.py

# Commit
git add -A
git commit -m "Release v0.1.0"

# Tag
git tag v0.1.0

# Push
git push origin main --tags
```

GitHub Actions will automatically publish to PyPI.

### 5. CHANGELOG.md

```markdown
# Changelog

All notable changes to TurboSEO will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-XX-XX

### Added
- Initial release
- Human writing standards checker based on Wikipedia's AI writing guide
- SEO analysis (keywords, readability, structure)
- CLI tool with `check`, `analyze`, `readability`, `keywords` commands
- Claude Code workspace integration (slash commands and agents)
- Comprehensive documentation

### Writing Patterns Detected
- AI vocabulary (30+ words)
- Puffery patterns (15+ patterns)
- Superficial analysis patterns
- Structural red flags
- Formatting issues
```

## Acceptance Criteria

- [ ] Package builds successfully
- [ ] Package installs from PyPI
- [ ] GitHub Actions CI passes
- [ ] All documentation renders correctly
- [ ] `turboseo --help` works after pip install
- [ ] Contributing guide is clear
