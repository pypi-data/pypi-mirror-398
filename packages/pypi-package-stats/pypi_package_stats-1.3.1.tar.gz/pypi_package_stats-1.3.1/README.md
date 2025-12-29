# PyPI Package Stats

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/pypi-package-stats)](https://pypi.org/project/pypi-package-stats/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/pypi-package-stats?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/pypi-package-stats)
[![Documentation](https://img.shields.io/badge/docs-ysskrishna.github.io%2Fpypi--package--stats-blue.svg)](https://ysskrishna.github.io/pypi-package-stats/)

![OG Image](https://raw.githubusercontent.com/ysskrishna/pypi-package-stats/main/media/og.png)

A CLI for PyPI package stats and download analytics, built on the official pypistats API. Fetch daily, weekly, monthly, and 180-day downloads, Python version and OS breakdowns, package metadata, with flexible output (JSON or Rich console tables) and smart disk caching.


## Features

- **Package Metadata**: Name, version, description, author, license, home page, and PyPI URL
- **Download Statistics**: Last day, week, month, and 180-day download counts
- **Python Version Breakdown**: Top 5 Python versions with download percentages (last 30 days)
- **Operating System Distribution**: Top 4 operating systems with download percentages (last 30 days)
- **Flexible Output**: Human-friendly Rich tables or machine-readable JSON
- **Smart Disk Caching**: Persistent disk cache with configurable TTL (default: 1 hour)
- **Cache Management**: Inspect cache usage or clear cached responses

## Quick Start

```bash
pip install pypi-package-stats
pypi-package-stats package nestedutils
```

Get JSON output:

```bash
pypi-package-stats package nestedutils --json
```

Disable cache for a single request:

```bash
pypi-package-stats package nestedutils --no-cache
```

### Example Output

![Example Output](https://raw.githubusercontent.com/ysskrishna/pypi-package-stats/main/media/example_output.png)

## Usage

### Fetch package statistics

```bash
pypi-package-stats package <PACKAGE_NAME>
```

Example:

```bash
pypi-package-stats package nestedutils
```

> The `package` command is the primary command used to fetch metadata and download analytics for a PyPI package.

### JSON output

```bash
pypi-package-stats package <PACKAGE_NAME> --json
```

This is useful for scripting, automation, or piping data into other tools.

### Cache Management

Caching significantly speeds up repeated queries and helps avoid API rate limits when exploring multiple packages.

#### Disable caching

```bash
pypi-package-stats package <PACKAGE_NAME> --no-cache
```

#### Custom cache TTL

Set cache time-to-live in seconds (`0` disables caching):

```bash
pypi-package-stats package <PACKAGE_NAME> --cache-ttl 7200
```

#### Clear cache

```bash
pypi-package-stats cache-clear
```

#### View cache information

```bash
pypi-package-stats cache-info
```

### Help

```bash
pypi-package-stats --help
```

## Data Source & Rate Limiting

This tool uses the [pypistats](https://pypistats.org/) API to fetch PyPI package statistics. The API enforces IP-based rate limits (for example, ~5 requests/sec and ~30 requests/min at the time of writing). These limits are set by pypistats.org and may change over time.

The built-in caching system helps minimize API calls and reduce the chance of hitting rate limits. If you encounter rate limit errors, wait a few seconds between requests if making multiple queries.

## Limitations

* Python version and OS breakdowns are limited to the last 30 days
* Data availability depends on the [pypistats](https://pypistats.org/) service

## Use Cases

* Compare popularity of Python libraries
* Track adoption trends of your own packages
* Generate download statistics for reports or dashboards
* Automate analytics workflows using JSON output

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

For development setup and guidelines, see [CONTRIBUTING.md](https://github.com/ysskrishna/pypi-package-stats/blob/main/CONTRIBUTING.md).


## License

MIT License - see [LICENSE](https://github.com/ysskrishna/pypi-package-stats/blob/main/LICENSE) file for details.

## Support

If you find this library useful, please consider:

- ⭐ **Starring** the repository on GitHub to help others discover it.
- 💖 **Sponsoring** to support ongoing maintenance and development.

[Become a Sponsor on GitHub](https://github.com/sponsors/ysskrishna) | [Support on Patreon](https://patreon.com/ysskrishna)

## Links

- **PyPI Package**: [pypi.org/project/pypi-package-stats](https://pypi.org/project/pypi-package-stats/)
- **Documentation**: [ysskrishna.github.io/pypi-package-stats](https://ysskrishna.github.io/pypi-package-stats/)
- **Repository**: [github.com/ysskrishna/pypi-package-stats.git](https://github.com/ysskrishna/pypi-package-stats.git)
- **Issues**: [github.com/ysskrishna/pypi-package-stats/issues](https://github.com/ysskrishna/pypi-package-stats/issues)
- **Changelog**: [github.com/ysskrishna/pypi-package-stats/blob/main/CHANGELOG.md](https://github.com/ysskrishna/pypi-package-stats/blob/main/CHANGELOG.md)
- **Releases**: [github.com/ysskrishna/pypi-package-stats/releases](https://github.com/ysskrishna/pypi-package-stats/releases)

## Author

**Y. Siva Sai Krishna**

- GitHub: [@ysskrishna](https://github.com/ysskrishna)
- LinkedIn: [ysskrishna](https://linkedin.com/in/ysskrishna)


