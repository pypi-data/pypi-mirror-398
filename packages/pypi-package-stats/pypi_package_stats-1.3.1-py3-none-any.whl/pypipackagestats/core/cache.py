from pathlib import Path
import platformdirs


def get_cache_dir() -> Path:
    """Get cache directory for diskcache (platform-specific)"""
    cache_dir = Path(platformdirs.user_cache_dir("pypipackagestats", "pypipackagestats"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

