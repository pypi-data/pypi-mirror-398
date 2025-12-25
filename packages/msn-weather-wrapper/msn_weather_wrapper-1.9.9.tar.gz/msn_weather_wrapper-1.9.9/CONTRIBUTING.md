# Contributing to MSN Weather Wrapper

Thank you for your interest in contributing to MSN Weather Wrapper! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the.jim.wyatt@outlook.com.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/msn-weather-wrapper.git
   cd msn-weather-wrapper
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/jim-wyatt/msn-weather-wrapper.git
   ```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Node.js 20+ (for frontend development)
- Podman (for containerized development)

### Local Development Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Containerized Development (Recommended)

For a fully isolated development environment:

```bash
# Initial setup
./dev.sh setup

# Start development environment
./dev.sh start

# View logs
./dev.sh logs

# Run tests
./dev.sh test
```

See [Container Development Setup](docs/CONTAINER_DEV_SETUP.md) for detailed documentation.

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

- **Bug fixes**: Fix issues reported in the issue tracker
- **Feature development**: Implement new features or enhancements
- **Documentation**: Improve or add to documentation
- **Tests**: Add or improve test coverage
- **Code quality**: Refactoring, optimization, or cleanup
- **Examples**: Add usage examples or tutorials

### Contribution Workflow

1. **Check existing issues** to see if your contribution is already being discussed
2. **Create an issue** if you're planning significant changes
3. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
4. **Make your changes** following our coding standards
5. **Test your changes** thoroughly
6. **Commit your changes** with clear, descriptive commit messages:
   ```bash
   git commit -m "feat: add weather alerts feature"
   # or
   git commit -m "fix: resolve temperature conversion bug"
   ```
7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Open a Pull Request** on GitHub

## Coding Standards

### Python Code

- **Follow PEP 8** style guidelines
- **Use type hints** for all function parameters and return values
- **Write docstrings** for all modules, classes, and functions
- **Keep line length** to 100 characters maximum
- **Use meaningful variable names** that clearly describe their purpose

### Code Quality Tools

We use the following tools to maintain code quality:

- **ruff**: Linting and code formatting
- **mypy**: Static type checking
- **bandit**: Security scanning
- **pytest**: Testing framework

#### Running Quality Checks

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy src/msn_weather_wrapper

# Security scan
bandit -r src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Frontend Code (TypeScript/React)

- **Use TypeScript** with strict mode enabled
- **Follow React best practices**
- **Use functional components** with hooks
- **Keep components small** and focused on a single responsibility
- **Add proper type definitions** for all props and state

#### Frontend Quality Checks

```bash
cd frontend

# Type check
npm run lint

# Build check
npm run build
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/test_client.py tests/test_models.py

# Security tests
pytest tests/test_security.py -v

# Integration tests (requires running containers)
podman-compose up -d
pytest tests/test_integration.py -v

# With coverage
pytest --cov=src --cov-report=html
```

### Writing Tests

- **Write tests for all new features**
- **Maintain or improve test coverage** (currently 90%)
- **Include edge cases** and error conditions
- **Use descriptive test names** that explain what is being tested
- **Follow the AAA pattern**: Arrange, Act, Assert

Example:
```python
def test_temperature_conversion():
    """Test Fahrenheit to Celsius conversion."""
    # Arrange
    fahrenheit = 68.0
    expected_celsius = 20.0

    # Act
    result = convert_fahrenheit_to_celsius(fahrenheit)

    # Assert
    assert result == expected_celsius
```

### Test Categories

- **Unit tests**: Fast tests with no external dependencies
- **Integration tests**: Tests that interact with the API
- **Security tests**: Validation of input sanitization and security features

## Pull Request Process

### Before Submitting

1. **Update documentation** if you're changing functionality
2. **Add or update tests** to cover your changes
3. **Run all tests** and ensure they pass
4. **Run quality checks** (ruff, mypy, bandit)
5. **Update CHANGELOG.md** with your changes (if significant)
6. **Rebase on latest main** to avoid merge conflicts:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### PR Requirements

- **Clear description**: Explain what changes you made and why
- **Reference issues**: Link to related issues (e.g., "Fixes #123")
- **All tests passing**: CI/CD checks must pass
- **Code review**: At least one maintainer approval required
- **No merge conflicts**: Rebase if needed
- **Documentation updated**: If applicable

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have added tests that prove my fix/feature works
- [ ] All tests pass locally
- [ ] I have updated the documentation
- [ ] I have added an entry to CHANGELOG.md (if applicable)
```

## Reporting Bugs

### Before Submitting a Bug Report

- **Check the documentation** for solutions
- **Search existing issues** to avoid duplicates
- **Try to reproduce** the bug with the latest version

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.0]
- Package version: [e.g., 0.1.0]

## Additional Context
Any other relevant information
```

## Feature Requests

We welcome feature requests! Please:

1. **Check existing issues** to see if someone already requested it
2. **Clearly describe the feature** and its use case
3. **Explain why it would be useful** to the project
4. **Provide examples** of how it would work

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Any other relevant information
```

## Development Tips

### Useful Commands

```bash
# Update dependencies
pip install -U -e ".[dev]"

# Generate SBOM
./tools/generate_sbom.sh

# Test deployment
./tools/test_deployment.sh

# Build documentation locally
mkdocs serve

# View coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Debugging

- **Use logging**: The project uses `structlog` for structured logging
- **Test in isolation**: Use `pytest -xvs` to stop on first failure
- **Container debugging**: Use `./dev.sh shell-api` for container access

### Common Issues

**Import errors after installing**:
```bash
pip install -e ".[dev]"  # Reinstall in editable mode
```

**Pre-commit hooks failing**:
```bash
pre-commit run --all-files  # Fix all issues at once
```

**Type errors with mypy**:
```bash
mypy src/msn_weather_wrapper --show-error-codes
```

## Questions?

If you have questions that aren't answered in this guide:

- **Open an issue** with the question label
- **Check the documentation** in the `docs/` directory
- **Contact the maintainer**: the.jim.wyatt@outlook.com

## License

By contributing to MSN Weather Wrapper, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to MSN Weather Wrapper!** 🎉
