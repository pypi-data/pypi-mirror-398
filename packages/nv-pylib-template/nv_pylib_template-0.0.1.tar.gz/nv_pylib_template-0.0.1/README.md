# nv-pylib-template

![Version](https://img.shields.io/github/v/release/cloudvoyant/nv-pylib-template?label=version)
![Release](https://github.com/cloudvoyant/nv-pylib-template/workflows/Release/badge.svg)
![PyPI](https://img.shields.io/pypi/v/nv-pylib-template)

`nv-pylib-template` is a Python library template with modern tooling, automated versioning, and dual publishing to PyPI and GCP Artifact Registry. Built with uv for fast dependency management and includes ruff, mypy, and pytest for code quality.

## Features

Here's what this template gives you off the bat:

- **Modern Python tooling**: uv for fast dependency management, ruff for linting/formatting, mypy for type checking, pytest for testing
- **Dual publishing**: Automatic publishing to both PyPI and GCP Artifact Registry
- **Type safety**: Strict mypy configuration with comprehensive type hints
- **Code quality**: Pre-configured ruff linter with sensible defaults
- **Testing**: pytest with coverage reporting and parametrized test examples
- **Command interface**: Self-documenting `just` recipes for all development tasks
- **Environment management**: Auto-load environment variables with `direnv`
- **CI/CD**: GitHub Actions for testing on PRs and automatic releases on main
- **Semantic versioning**: Automated version bumping with conventional commits
- **Cross-platform**: Works on macOS, Linux, Windows (WSL), and Dev Containers

## Requirements

- bash 3.2+
- Python 3.12+
- uv (Python package manager)
- just (command runner)
- direnv (environment management)

Run `just setup` to install all required dependencies automatically.

Optional: `just setup --dev` for additional development tools (Docker, Claude CLI, etc.).

## Quick Start

Scaffold a new project:

```bash
# Option 1: Nedavellir CLI (automated)
nv create your-project-name --platform nv-lib-template

# Option 2: GitHub template + scaffold script
# Click "Use this template" on GitHub, then:
git clone <your-new-repo>
cd <your-new-repo>
bash scripts/scaffold.sh --project your-project-name
```

Install dependencies and start developing:

```bash
just setup              # Install Python, uv, and all dependencies
just install            # Install project dependencies with uv
just test               # Run tests with coverage
just lint               # Run linter
just format             # Format code
just type-check         # Run type checker
just build              # Build Python package
```

Development workflow:

```bash
# Make changes to your code
just format             # Format code with ruff
just lint               # Check code with ruff
just type-check         # Verify types with mypy
just test               # Run tests with pytest

# Build and publish
just build              # Creates wheel and sdist in dist/
just publish            # Publishes to PyPI and/or GCP Artifact Registry
```

Publishing setup (add to GitHub secrets):

```bash
# Required for PyPI publishing
PYPI_TOKEN              # Get from https://pypi.org/manage/account/token/

# Optional for GCP Artifact Registry
GCP_SA_KEY              # GCP service account JSON key
GCP_REGISTRY_PROJECT_ID # GCP project ID
GCP_REGISTRY_REGION     # GCP region (e.g., us-east1)
GCP_REGISTRY_NAME       # Artifact Registry name
```

Commit using conventional commits (`feat:`, `fix:`, `docs:`). Push to main and CI/CD will automatically version and publish your package.

## Documentation

To learn more about using this template, read the docs:

- [User Guide](docs/user-guide.md) - Complete setup and usage guide
- [Architecture](docs/architecture.md) - Design and implementation details

## TODO

- [ ] Pre-release publishing
- [ ] Template docs improvements

## References

- [uv - Python package manager](https://docs.astral.sh/uv/)
- [ruff - Python linter and formatter](https://docs.astral.sh/ruff/)
- [mypy - Static type checker](https://mypy.readthedocs.io/)
- [pytest - Testing framework](https://docs.pytest.org/)
- [just command runner](https://github.com/casey/just)
- [direnv environment management](https://direnv.net/)
- [semantic-release](https://semantic-release.gitbook.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [PyPI Publishing](https://packaging.python.org/)
- [GCP Artifact Registry](https://cloud.google.com/artifact-registry/docs)
