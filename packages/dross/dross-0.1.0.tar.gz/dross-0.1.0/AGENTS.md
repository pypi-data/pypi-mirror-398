# Dross Agent Documentation

## Make Targets

Dross provides a complete development lifecycle via Make:

```bash
make sync           # Sync dependencies (includes all groups)
make fmt            # Format code with ruff
make lint           # Lint and auto-fix issues
make typecheck      # Type check with pyright
make test           # Run unit & integration tests
make build          # Build distribution package
make qa             # Run all quality checks (fmt, lint, typecheck, test, build)
make clean          # Clean cache and temp files
make distclean      # Full cleanup including .venv
make help           # Show this help
```

## CLI Commands

Dross provides minimal CLI utilities:

```bash
dross --version                    # Show version
dross --help                       # Show help

dross config validate              # Validate kef.yaml configuration
dross schema                       # Show medallion schema structure
```

## Development Workflow

After modifying code:

```bash
# Format and lint
make fmt
make lint

# Type check
make typecheck

# Run tests
make test

# Run all checks
make qa
```

## CI/CD Integration

Use `make qa` in your CI/CD pipeline to run all quality checks:

```yaml
# GitHub Actions example
- name: Quality Assurance
  run: make qa
```

## Testing

Dross uses pytest for testing:

```bash
# Run all tests
make test

# Run specific test file
uv run pytest test/unit/test_models.py

# Run with coverage
make test.coverage
```

## Building

```bash
# Build distribution
make build

# Built artifacts are in:
# - dist/dross-*.whl (wheel)
# - dist/dross-*.tar.gz (source)
```

## Dependencies

See `pyproject.toml` for:
- **Core dependencies**: mlflow, duckdb, scikit-learn, unitycatalog-client, click, pyyaml
- **Dev dependencies**: pytest, ruff, pyright, pytest-cov

Update with:

```bash
make sync
```
