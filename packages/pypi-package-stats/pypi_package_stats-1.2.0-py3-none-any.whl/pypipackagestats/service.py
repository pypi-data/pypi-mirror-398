import json
from typing import Dict, Any
from nestedutils import get_at
from pypipackagestats.core.client import PyPIClient
from pypipackagestats.output.utils import (
    get_upload_time,
    get_last_30_days_data,
    aggregate_by_category,
)
from pypipackagestats.constants import (
    TOP_PYTHON_VERSIONS_COUNT,
    TOP_OS_COUNT,
    DATE_ISO_FORMAT_LENGTH,
)
from pypipackagestats.output.formatters import (
    format_package_info,
    format_download_stats,
    format_python_versions,
    format_os_distribution,
)
from rich.console import Console

console = Console()


class PackageStatsService:
    """Service layer for processing PyPI package statistics"""

    def __init__(self, client: PyPIClient):
        self.client = client

    def extract_data(self, package: str) -> Dict[str, Any]:
        pkg_data = self.client.get_package_info(package)
        package_info = get_at(pkg_data, "info", default={})
        upload_time = get_upload_time(pkg_data)

        recent_stats = self.client.get_recent_stats(package)
        overall_stats = self.client.get_overall_stats(package)
        py_stats = self.client.get_python_minor_stats(package)
        os_stats = self.client.get_system_stats(package)

        return {
            "package_info": package_info,
            "upload_time": upload_time,
            "recent_stats": recent_stats,
            "overall_stats": overall_stats,
            "py_stats": py_stats,
            "os_stats": os_stats,
        }

    def get_processed_data(self, package: str) -> Dict[str, Any]:
        """
        Single source of truth: fetch and fully process all data into a structured dict.
        Used by both JSON and Rich output.
        """
        raw = self.extract_data(package)

        # Totals
        total_180d = sum(get_at(d, "downloads", default=0) for d in raw["overall_stats"])

        # Python versions (last 30 days)
        py_last30 = get_last_30_days_data(raw["py_stats"])
        py_totals = aggregate_by_category(py_last30)
        total_py = sum(py_totals.values())
        top_py = sorted(py_totals.items(), key=lambda x: -x[1])[:TOP_PYTHON_VERSIONS_COUNT]
        python_versions = [
            {
                "version": cat,
                "downloads": count,
                "percentage": round(100 * count / total_py, 1) if total_py > 0 else 0.0,
            }
            for cat, count in top_py
        ]

        # OS distribution (last 30 days)
        os_last30 = get_last_30_days_data(raw["os_stats"])
        os_totals = aggregate_by_category(os_last30)
        total_os = sum(os_totals.values())
        top_os = sorted(os_totals.items(), key=lambda x: -x[1])[:TOP_OS_COUNT]
        operating_systems = [
            {
                "os": cat,
                "downloads": count,
                "percentage": round(100 * count / total_os, 1) if total_os > 0 else 0.0,
            }
            for cat, count in top_os
        ]

        # Package metadata
        info = raw["package_info"]
        upload_time_str = raw["upload_time"][:DATE_ISO_FORMAT_LENGTH] if raw["upload_time"] else None

        # Handle project_urls - try different paths
        home_page = (
            get_at(info, "home_page")
            or get_at(info, "project_url")
            or get_at(info, ["project_urls", "Homepage"])
        )

        package_metadata = {
            "name": get_at(info, "name"),
            "version": get_at(info, "version"),
            "upload_time": upload_time_str,
            "description": get_at(info, "summary"),
            "author": get_at(info, "author") or get_at(info, "author_email"),
            "license": get_at(info, "license"),
            "home_page": home_page,
            "pypi_url": get_at(info, "package_url"),
        }

        downloads = {
            "last_day": get_at(raw["recent_stats"], "last_day", default=0),
            "last_week": get_at(raw["recent_stats"], "last_week", default=0),
            "last_month": get_at(raw["recent_stats"], "last_month", default=0),
            "last_180d": total_180d,
        }

        return {
            "package": package_metadata,
            "downloads": downloads,
            "python_versions": python_versions,
            "operating_systems": operating_systems,
        }


    def display_package_stats(self, package: str, as_json: bool = False) -> None:
        data = self.get_processed_data(package)
        if as_json:
            console.print(json.dumps(data, indent=2))
        else:
            format_package_info(data)
            format_download_stats(data)
            format_python_versions(data)
            format_os_distribution(data)