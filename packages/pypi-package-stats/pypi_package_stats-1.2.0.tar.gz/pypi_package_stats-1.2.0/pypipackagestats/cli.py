import typer
import requests
from rich.console import Console

from pypipackagestats.core.client import PyPIClient
from pypipackagestats.service import PackageStatsService
from pypipackagestats.core.cache import get_cache_dir
from pypipackagestats.constants import DEFAULT_CACHE_TTL
from pypipackagestats.output.formatters import print_project_banner

app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)
console = Console()


@app.command(no_args_is_help=True)
def package(
    package: str = typer.Argument(..., help="Package name to query"),
    json: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    cache_ttl: int | None = typer.Option(
        None,
        "--cache-ttl",
        help=f"Cache TTL in seconds (0 = disable, default = {DEFAULT_CACHE_TTL})",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Disable caching (equivalent to --cache-ttl 0)"
    ),
):
    """Display PyPI package metadata and download information."""
    # --no-cache takes precedence
    effective_ttl = 0 if no_cache else (cache_ttl if cache_ttl is not None else DEFAULT_CACHE_TTL)

    client = PyPIClient(cache_ttl=effective_ttl)
    service = PackageStatsService(client)

    try:
        service.display_package_stats(package, json)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Error:[/red] Package '{package}' not found on PyPI.")
        else:
            console.print(f"[red]Error:[/red] HTTP {e.response.status_code}: {e.response.reason}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def cache_clear():
    """Clear cache directory"""
    client = PyPIClient()
    client.clear_cache()
    console.print("[green]✓ Cache cleared successfully[/green]")


@app.command()
def cache_info():
    """Display information about the current cache."""
    cache_dir = get_cache_dir()
    client = PyPIClient()  # Uses default TTL

    size = client.get_cache_size()

    console.print(f"[cyan]Cache directory:[/cyan] {cache_dir / 'api_cache'}")
    console.print(f"[cyan]Entries:[/cyan] {size}")


def main():
    print_project_banner()
    app()


if __name__ == "__main__":
    main()
