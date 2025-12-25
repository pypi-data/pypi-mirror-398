# Contributing to CVE Report Aggregator

Thank you for your interest in contributing to the CVE Report Aggregator!

## Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated changelog generation and
semantic versioning. All commit messages should follow this format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

Must be one of the following:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Scope (Optional)

The scope should be the name of the affected component (e.g., `scanner`, `cli`, `aggregator`, `severity`).

### Subject

A brief description of the change:

- Use imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No period (.) at the end

### Examples

```
feat(scanner): add support for custom SBOM formats

Implements custom SBOM format detection and parsing to support
non-standard vulnerability scanning tools.

Closes #123
```

```
fix(severity): correct CVSS 3.x score extraction for Trivy format

The extraction logic was failing to handle vendor-specific CVSS data
in Trivy reports. Updated to properly iterate over vendor keys.
```

```
docs: update README with Docker usage instructions
```

```
chore(deps): update idna version constraint
```

## Pull Request Process

1. **Fork the repository** and create your branch from `develop`
1. **Write conventional commit messages** for all your commits
1. **Add tests** if applicable
1. **Update documentation** if you're adding new features
1. **Ensure all tests pass** by running `uv run pytest tests`
1. **Run linting** with `uv run ruff check src tests`
1. **Create a pull request** targeting the `develop` branch

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Grype and/or Trivy (optional, for scanner integration tests)

### Installation

```bash
# Clone the repository
git clone https://github.com/mkm29/cve-report-aggregator.git
cd cve-report-aggregator

# Install dependencies
uv sync --all-extras --dev

# Run tests
uv run pytest tests

# Run linting
uv run ruff check src tests
uv run ruff format --check src tests
```

## Release Process

Releases are automated using [Release Please](https://github.com/googleapis/release-please):

1. Commits following conventional commit format are automatically analyzed
1. When changes are merged to `main`, Release Please creates/updates a release PR
1. Merging the release PR triggers:
   - Version bump in `pyproject.toml`
   - CHANGELOG.md update
   - GitHub release creation
   - PyPI package publication
   - Docker image build and push

### GitHub Actions Permissions

To enable automated releases, ensure the following repository setting is enabled:

**Settings → Actions → General → Workflow permissions**

- ✅ Allow GitHub Actions to create and approve pull requests

## Questions?

Feel free to open an issue for any questions or concerns.
