# Contributing to Dross

Thank you for your interest in contributing! This document provides guidelines for contributions.

## Development Setup

```bash
# Clone and setup
git clone <repo>
cd packages/dross

# Sync dependencies
make sync

# Verify setup
make test
```

## Code Style

We use:
- **ruff** for formatting and linting
- **pyright** for type checking
- **pytest** for testing

Format before committing:

```bash
make fmt
make lint
make typecheck
```

## Testing

Add tests for new features:

```bash
# Run all tests
make test

# Run with coverage
make test.coverage
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Run `make qa` to verify all checks pass
4. Add changelog entry in CHANGELOG.md
5. Submit PR with clear description

## Reporting Issues

Please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Python version and environment info

Thank you!
