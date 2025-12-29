import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from pypipackagestats.core.models import ProjectMetadata
from nestedutils import get_at


try:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib
except ImportError:
    raise ImportError("tomli is required for Python < 3.11")


def get_resource_path(relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.exists():
        return candidate

    candidate = Path(__file__).parent.parent / relative_path
    if candidate.exists():
        return candidate

    raise FileNotFoundError(f"Resource not found: {relative_path}")


# Module-level cache for project metadata
_cached_metadata: Optional[ProjectMetadata] = None


def _parse_pyproject(path: Path) -> Dict[str, Any]:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{path} not found.")
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Error parsing TOML: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error reading {path}: {e}")


def get_project_metadata() -> ProjectMetadata:
    global _cached_metadata
    
    # Return cached metadata if available
    if _cached_metadata is not None:
        return _cached_metadata
    
    # Read and parse the file only once
    data = _parse_pyproject(get_resource_path("pyproject.toml"))
    
    # Cache the result
    _cached_metadata = ProjectMetadata(
        name=get_at(data, "project.name", ""),
        version=get_at(data, "project.version", ""),
        repository_url=get_at(data, "project.urls.Repository", ""),
        author=get_at(data, "tool.internalurls.author_name", ""),
        author_url=get_at(data, "tool.internalurls.author_linkedin", "")
    )
    
    return _cached_metadata