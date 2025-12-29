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


# Module-level cache for project metadata
_cached_metadata: Optional[ProjectMetadata] = None

def get_resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(base_path, relative_path)

def get_project_metadata() -> ProjectMetadata:
    global _cached_metadata
    
    # Return cached metadata if available
    if _cached_metadata is not None:
        return _cached_metadata
    
    toml_path = get_resource_path("pyproject.toml")
    data = {}
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    
    # Cache the result
    _cached_metadata = ProjectMetadata(
        name=get_at(data, "project.name", ""),
        version=get_at(data, "project.version", ""),
        repository_url=get_at(data, "project.urls.Repository", ""),
        author=get_at(data, "tool.internalurls.author_name", ""),
        author_url=get_at(data, "tool.internalurls.author_linkedin", "")
    )
    
    return _cached_metadata