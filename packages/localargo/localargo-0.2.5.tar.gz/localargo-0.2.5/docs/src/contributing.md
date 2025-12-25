# Contributing

We welcome contributions to Localargo! This document provides guidelines for contributing to the project.

## Development Setup

### Quick Setup with Mise (Recommended)

1. **Install Mise:**
   ```bash
   # macOS with Homebrew
   brew install mise

   # Or install manually
   curl https://mise.jdx.dev/install.sh | sh
   ```

2. **Clone and setup:**
   ```bash
   git clone https://github.com/govflows/localargo.git
   cd localargo

   # Install all development tools
   mise install

   # Create Hatch environment
   hatch env create
   ```

   This will automatically install and configure:
   - Python 3.12
   - KinD, kubectl, ArgoCD CLI
   - Hatch, mdBook
   - All other development tools

### Manual Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/govflows/localargo.git
   cd localargo
   ```

2. **Set up development environment:**
   ```bash
   # Install in development mode with dev dependencies
   pip install -e ".[dev]"
   ```

3. **Run tests:**
   ```bash
   # Run the test suite
   hatch run test
   ```

4. **Type checking:**
   ```bash
   # Run MyPy type checking
   hatch run typecheck
   ```

## Code Style

This project follows these coding standards:

- **Ruff**: For code formatting and linting
- **MyPy**: For static type checking
- **pydoclint**: For docstring validation

Run the full pre-commit check with:
```bash
mise run precommit
```

## Project Structure

```text
src/localargo/
├── __about__.py      # Version information
├── __init__.py       # Package initialization
├── __main__.py       # Main entry point
├── cli/              # Command-line interface
│   └── commands/     # CLI command implementations
├── config/           # Configuration handling
│   └── manifest.py   # Manifest parsing
├── core/             # Core business logic
│   ├── argocd.py     # ArgoCD client
│   ├── checkers.py   # Status checkers
│   ├── execution.py  # Execution engine
│   └── executors.py  # Step executors
├── providers/        # Cluster providers (kind, k3s)
└── utils/            # Utility functions

tests/                # Test suite
docs/                 # Documentation (mdbook)
```

## Adding New Commands

Localargo uses Click for CLI commands. To add a new command:

1. Add the command function in the appropriate file under `src/localargo/cli/commands/`
2. Register it in the CLI group
3. Update this documentation

Example:
```python
@localargo.command()
def new_command():
    """Description of the new command."""
    click.echo("New command executed!")
```

## Testing

LocalArgo follows a **mocked testing philosophy** where all tests are fully isolated and require no external dependencies.

### Development and Testing Loop

All developers must run the following before committing or opening a PR:

```bash
# Run the full precommit suite
mise run precommit
```

This runs:
1. `hatch fmt` - Format code
2. `hatch run lizard` - Check code complexity
3. `hatch run pydoclint` - Validate docstrings
4. `hatch run typecheck` - Type check with MyPy
5. `hatch run test` - Run all tests

All tests are fully mocked -- no Kubernetes, Docker, or Kind binaries are required.

### Writing Tests

- Write tests in the `tests/` directory
- Use pytest for testing framework
- All subprocess calls must be mocked (see `tests/conftest.py`)
- Tests should verify command construction, not execution
- Use the `mock_subprocess_run` fixture from conftest.py

## Documentation

- Update the mdbook documentation in `docs/src/` for any new features
- Keep README.md up to date
- Use clear, concise language

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run `mise run precommit` to verify all checks pass
5. Update documentation if needed
6. Commit your changes: `git commit -am 'Add my feature'`
7. Push to the branch: `git push origin feature/my-feature`
8. Submit a pull request

## License

By contributing to Localargo, you agree that your contributions will be licensed under the same MIT license that covers the project.
