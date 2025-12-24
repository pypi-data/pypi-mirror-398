# Contributing to usenc

Thank you for considering contributing to usenc! This document provides guidelines for contributing.

## Development Setup

### 1. Fork and Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/usenc.git
cd usenc
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# OR
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev,docs]"
```

This installs:
- **Core package** - usenc library and CLI
- **dev dependencies** - pytest, pytest-cov, ruff, mypy, bandit, pre-commit
- **docs dependencies** - mkdocs, mkdocs-material, mkdocstrings

### 4. Set Up Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit:

```bash
# Install pre-commit hooks
pre-commit install
```

The hooks will automatically run:
- **ruff** - Fast Python linter and formatter
- **mypy** - Static type checker
- **bandit** - Security vulnerability scanner
- **Standard checks** - Trailing whitespace, file endings, YAML/TOML validation

### 5. Verify the Installation

Run the test suite to ensure everything is working:

```bash
pytest
```

Run linting and formatting checks manually:

```bash
# Lint code
ruff check src tests

# Format code
ruff format src tests

# Type check
mypy src/usenc

# Security scan
bandit -r src/usenc
```

Or run all pre-commit hooks manually:

```bash
pre-commit run --all-files
```

## Development Workflow

### Making Changes

1. **Activate your virtual environment** (if not already active):
   ```bash
   source venv/bin/activate
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make your changes** and test them:
   ```bash
   pytest
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

   Pre-commit hooks will automatically run. If they fail:
   - Review the changes made by auto-fixes
   - Stage the fixed files: `git add .`
   - Commit again: `git commit -m "Description of changes"`

5. **Push to your fork**:
   ```bash
   git push origin feature/my-feature
   ```

### Pre-commit Hook Behavior

When you commit, the following checks run automatically:

1. **Code Formatting** - ruff auto-formats your code
2. **Linting** - ruff checks for code quality issues
3. **Type Checking** - mypy validates type annotations
4. **Security Scanning** - bandit looks for security vulnerabilities
5. **File Checks** - removes trailing whitespace, fixes line endings

If any check fails or makes changes:
- **Auto-fixed issues** (formatting, whitespace) - Stage and commit again
- **Errors that need manual fixes** (type errors, security issues) - Fix the code, then commit again

To skip hooks in emergencies (not recommended):
```bash
git commit --no-verify -m "Emergency fix"
```

## Code Style

- Code must be backward compatible with python 3.8
- Follow PEP 8 style guidelines (enforced by ruff)
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and small
- Use type hints for function signatures (checked by mypy)

## Documentation

Add docstrings to code to document your new encoder:

```python
class HexEncoder(Encoder):
    """
    Short encoder description

    Long encoder description, multiple lines, ...

    Examples:
    hello world -> 68656C6C6F20776F726C64
    other -> 6F74686572
    """

    params = {
        'param_name': {
            'type': str,
            'default': '',
            'help': 'Description of the param'
        },
    }
    ...
```

Build and preview documentation locally:

```bash
mkdocs serve
```

## Pull Request Process

1. **Follow the Development Workflow** (see above)

2. **Open a Pull Request** on GitHub targeting the `main` branch

3. **Ensure your PR passes all checks**:
   - GitHub Actions CI tests
   - Code coverage requirements
   - All pre-commit hooks pass

### PR Checklist

- [ ] Virtual environment set up and activated
- [ ] Pre-commit hooks installed and passing
- [ ] Tests pass locally (`pytest`)
- [ ] Code formatted with ruff (`ruff format src tests`)
- [ ] No linting errors (`ruff check src tests`)
- [ ] Type checks pass (`mypy src/usenc`)
- [ ] No security issues (`bandit -r src/usenc`)
- [ ] Snapshots for new encoders are correct
- [ ] Documentation updated if needed
- [ ] Commit messages are clear and descriptive

## Adding New Encoders

See the [Adding Encoders](adding-encoders.md) guide for detailed instructions.

## Reporting Issues

When reporting issues, please include:

- Python version
- usenc version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Questions?

Open an issue on GitHub or start a discussion!
