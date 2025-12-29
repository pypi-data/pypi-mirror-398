# Contributing Guide

Thank you for your interest in contributing to `pypi-package-stats`! This guide will help you get started with development and understand how to contribute effectively.

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful, inclusive, and constructive in all interactions.

## Getting Started

Before you begin, make sure you have:

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) - A fast Python package installer and resolver
- Git installed and configured

## Development Setup

### Installing uv

If you don't have `uv` installed, you can install it using [UV Getting Started](https://docs.astral.sh/uv/getting-started/installation/)

### Setting Up the Development Environment

1. Fork the repository on GitHub

2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/pypi-package-stats.git
cd pypi-package-stats
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/ysskrishna/pypi-package-stats.git
```

4. Install the project and development dependencies using `uv`:

```bash
uv sync --dev
```

This will:
- Create a virtual environment (if it doesn't exist)
- Install the project in editable mode
- Install all development dependencies (including testing and documentation tools)

## Making Changes

1. Create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix-name
```

2. Make your changes following the [Code Style](#code-style) guidelines


## Submitting Changes

1. **Update Documentation**: If you've added new features or changed behavior, update the relevant documentation:
   - Update `README.md` if the API or usage has changed
   - Update `CHANGELOG.md` with a description of your changes
   - Update docstrings if you've modified functions

2. **Commit Your Changes**: Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: description of what you added"
```

Good commit messages:
- Start with a verb in imperative mood (e.g., "Add", "Fix", "Update")
- Be concise but descriptive
- Reference issue numbers if applicable (e.g., "Fix #123: description")

3. **Push to Your Fork**:

```bash
git push origin feature/your-feature-name
```

4. **Create a Pull Request**:
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template with:
     - Description of changes
     - Related issues (if any)
     - Testing performed
     - Any breaking changes

5. **Respond to Feedback**: Be open to feedback and ready to make changes if requested

## Code Style

### General Guidelines

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Add docstrings to all public functions and classes
- Keep lines under 100 characters when possible

### Type Hints

- Use type hints for function parameters and return values
- The project includes a `py.typed` marker file, so type hints are important

### Documentation

- Use clear, concise docstrings
- Follow the existing docstring format in the codebase
- Include parameter descriptions and return value descriptions
- Add examples for complex functions

### Import Organization

- Group imports: standard library, third-party, local
- Use absolute imports
- Keep imports at the top of the file

## Building the Package

To build the package locally:

```bash
uv build
```

This will create distribution files in the `dist/` directory:
- `pypi-package-stats-<version>-py3-none-any.whl` (wheel)
- `pypi-package-stats-<version>.tar.gz` (source distribution)

### Installing the Local Package

To test the package installation locally:

```bash
# Install from the built wheel
uv pip install dist/pypi-package-stats-*.whl

# Or install in editable mode for development
uv pip install -e .
```

## Development Usage

### Run the tool during development

```bash
uv run pypi-package-stats package <PACKAGE_NAME>
```

Example:

```bash
uv run pypi-package-stats package nestedutils
```

### JSON output

Get output in JSON format:

```bash
uv run pypi-package-stats package <PACKAGE_NAME> --json
```

### Cache management

#### Disable caching

```bash
uv run pypi-package-stats package <PACKAGE_NAME> --no-cache
```

#### Custom cache TTL

Set cache time-to-live in seconds (0 = disable):

```bash
uv run pypi-package-stats package <PACKAGE_NAME> --cache-ttl 7200
```

#### Clear cache

```bash
uv run pypi-package-stats cache-clear
```

#### View cache information

```bash
uv run pypi-package-stats cache-info
```

### Help

```bash
uv run pypi-package-stats --help
uv run pypi-package-stats package --help
```

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [pytest Documentation](https://docs.pytest.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Type Hints Documentation](https://docs.python.org/3/library/typing.html)

## Questions?

If you have questions or need help, feel free to:
- Open an issue on GitHub
- Check existing issues and discussions
- Review the codebase and documentation

Thank you for contributing to `pypi-package-stats`! 🎉

