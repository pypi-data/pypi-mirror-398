# confee - Development Guide

**Language:** [한국어](./DEVELOPMENT.ko.md) | English

## Project Structure

```
confee/
├── src/confee/                 # Main package
│   ├── __init__.py            # Package initialization and public API
│   ├── config.py              # ConfigBase and configuration base class
│   ├── loaders.py             # YAML/JSON file loaders
│   ├── overrides.py           # CLI/environment variable overrides
│   └── parser.py              # Configuration parser
│
├── tests/                      # Test suite
│   ├── test_config.py         # ConfigBase tests
│   ├── test_loaders.py        # Loader tests
│   ├── test_overrides.py      # Override tests
│   ├── test_parser.py         # Parser tests
│   └── test_advanced_features.py
│
├── pyproject.toml             # Project configuration
├── README.md                  # Documentation
└── LICENSE                    # MIT License
```

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/bestend/confee.git
cd confee
```

### 2. Set Up Development Environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate

# Or using pip
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

### 4. Run Tests

```bash
pytest tests/ -v

# With coverage
pytest tests/ --cov=confee --cov-report=html
```

---

## 📝 Code Style

### Python Version

- Minimum: Python 3.8
- Tested: Python 3.8, 3.9, 3.10, 3.11, 3.12

### Formatting & Linting

```bash
# Format code
black src/confee tests/

# Check style
ruff check src/confee tests/

# Type checking
mypy src/confee
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Class

```bash
pytest tests/test_config.py::TestConfigBaseBasics -v
```

### Run Specific Test Function

```bash
pytest tests/test_config.py::TestConfigBaseBasics::test_config_creation -v
```

### Coverage Report

```bash
pytest tests/ --cov=confee --cov-report=term-missing
```

---

## 📦 Project Layout

```
src/confee/
├── __init__.py              # Public API exports
├── config.py                # ConfigBase class
│   ├── ConfigBase           # Base configuration class
│   └── load()               # Unified parser method
├── loaders.py               # File loaders
│   ├── ConfigLoader         # YAML/JSON loader
│   └── resolve_file_references()
├── overrides.py             # Override handling
│   ├── OverrideHandler      # CLI/env override handler
│   └── Color                # Terminal color support
└── parser.py                # Configuration parser
    └── ConfigParser         # Profile and inheritance parser
```

---

## 🔧 Key Components

### ConfigBase

Main class for configuration definition:

```python
from confee import ConfigBase

class AppConfig(ConfigBase):
    name: str
    debug: bool = False
    workers: int = 4
```

**Features:**
- Pydantic V2 based
- Type validation
- Default values
- Nested fields support

### OverrideHandler

Handles CLI and environment variable overrides:

```python
from confee import OverrideHandler

config = OverrideHandler.parse(
    AppConfig,
    cli_args=["debug=true"],
    config_file="config.yaml"
)
```

### ConfigParser

Advanced parsing with inheritance:

```python
from confee import ConfigParser

parser = ConfigParser("./configs")
config = parser.parse("config.yaml", AppConfig)
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| README.md | Main documentation |
| COMPARISON.md | confee vs OmegaConf comparison |
| DEVELOPMENT.md | Development guide (this file) |

---

## 🔄 Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/bestend/confee.git
   cd confee
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

4. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

5. **Format and Lint**
   ```bash
   black src/confee tests/
   ruff check src/confee tests/
   ```

6. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: description"
   git push origin feature/my-feature
   ```

7. **Create Pull Request**

---

## 🐛 Troubleshooting

### Import Errors

```bash
# Ensure package is installed
pip install -e .
```

### Test Failures

```bash
# Clear cache
rm -rf .pytest_cache __pycache__

# Run tests again
pytest tests/ -v
```

### Type Checking Errors

```bash
# Install mypy
pip install mypy

# Run type checker
mypy src/confee
```

---

## 📋 Future Improvements

- [ ] Web-based configuration editor
- [ ] Remote configuration source support
- [ ] Advanced validation rules
- [ ] Configuration versioning
- [ ] Detailed logging and debugging
- [ ] Configuration merge strategy customization
- [ ] Performance optimization

---

## License

MIT License © 2025

---

**Language:** [한국어](./development.ko.md) | English

