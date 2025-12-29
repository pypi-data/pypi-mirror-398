# Contributing to Git Miner

Thank you for your interest in contributing to Git Miner! This document provides guidelines for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive. All contributors are expected to adhere to these principles.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
make lint

# Format code
make format
```

## Making Changes

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and small

### Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Aim for 80%+ code coverage

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add search by language filter
fix: handle rate limit errors gracefully
docs: update README with examples
test: add tests for query builder
```

## Submitting Changes

1. Push to your fork
2. Create a pull request
3. Describe your changes clearly
4. Reference related issues

## Pull Request Checklist

- [ ] Code passes all tests
- [ ] Code is properly formatted (ruff format)
- [ ] Code passes linting (ruff check)
- [ ] New features include tests
- [ ] Documentation is updated
- [ ] Commit messages are clear

## Getting Help

- Open an issue for bugs or feature requests
- Ask questions in discussions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
