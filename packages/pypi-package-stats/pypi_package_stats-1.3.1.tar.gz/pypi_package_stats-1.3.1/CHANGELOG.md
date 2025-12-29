# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1]

### Fixed

- Fixed pyproject.toml Missing error by forcing inclusion in wheel build
- Fixed get_resource_path function to fetch pyproject.toml from the correct path

## [1.3.0]

### Fixed

- Fixed pyproject.toml parsing error by improving path resolution for PyInstaller and different execution environments

### Added

- PyPI downloads badge to README
- MkDocs theme overrides for improved documentation styling

### Changed

- Improved README flow and formatting
- Enhanced rate limiting documentation with clearer explanations

## [1.2.0]

### Added

- MkDocs documentation site with GitHub Pages deployment
- GitHub Actions workflow for automated documentation deployment
- Refactored CONTRIBUTING.md with comprehensive contribution guidelines
- Documentation site accessible at https://ysskrishna.github.io/pypi-package-stats/

### Changed

- Updated nestedutils dependency to v1.1.2
- Improved package keywords for better discoverability on PyPI
- Updated documentation URL in pyproject.toml to point to GitHub Pages
- Enhanced README with documentation badge and improved structure

## [1.1.0]

### Added

- Development documentation (DEVELOPMENT.md) with contribution guidelines
- Release documentation (RELEASE.md) with release process instructions
- Human-readable date formatting for package upload times (e.g., "December 7, 2025")
- OS name normalization (darwin → macOS, windows → Windows, linux → Linux)
- CLI welcome banner with ASCII art about the project
- Example output image in media directory

### Changed
- Improved CLI help text formatting and clarity
- Enhanced README documentation with better structure and examples
- Refined default value handling for better user experience
- Improved CLI output formatting and consistency

## [1.0.0]

### Added
- Initial release of PyPI Package Stats
- CLI tool to fetch comprehensive PyPI package information
- Package metadata display:
  - Name, version, upload time
  - Description, author, license
  - Home page and PyPI URL
- Download statistics:
  - Last day, week, month, and 180-day download counts
  - Excludes mirror downloads
- Python version breakdown:
  - Top 5 Python versions (last 30 days)
  - Download percentages and counts
- Operating system distribution:
  - Top 4 operating systems (last 30 days)
  - Download percentages and counts
- JSON output format option
- Persistent disk caching with configurable TTL (default: 3600 seconds)
- Cache management commands:
  - Clear cache
  - View cache information
- Rich terminal output with formatted tables
- Support for Python 3.8+

[1.3.1]: https://github.com/ysskrishna/pypi-package-stats/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/ysskrishna/pypi-package-stats/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/ysskrishna/pypi-package-stats/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/ysskrishna/pypi-package-stats/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/ysskrishna/pypi-package-stats/releases/tag/v1.0.0

