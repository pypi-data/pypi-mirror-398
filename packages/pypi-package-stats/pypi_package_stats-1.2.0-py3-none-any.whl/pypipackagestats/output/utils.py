from datetime import date, datetime
from nestedutils import get_at


def humanize_number(num: int) -> str:
    """Convert large numbers to human-readable format (K, M, B)"""
    for unit in ['', 'K', 'M', 'B']:
        if abs(num) < 1000:
            return f"{num:,.1f}{unit}".rstrip('0').rstrip('.')
        num /= 1000
    return f"{num:,.1f}T"


def normalize_os_name(os_name: str) -> str:
    """Normalize OS names for display"""
    if not os_name or os_name == "null":
        return "Unknown"
    mapping = {
        "darwin": "macOS",
        "windows": "Windows",
        "linux": "Linux"
    }
    return mapping.get(os_name.lower(), os_name.title())


def get_upload_time(pkg_data: dict) -> str:
    """Extract upload_time from package data"""
    version = get_at(pkg_data, "info.version")
    
    if version:
        # Try to get upload_time from the first release file
        # Use list path to safely handle version strings that might contain special characters
        upload_time = get_at(pkg_data, ["releases", version, 0, "upload_time"])
        if not upload_time:
            upload_time = get_at(pkg_data, ["releases", version, 0, "upload_time_iso_8601"])
        if upload_time:
            return upload_time
    
    return ""


def get_last_30_days_data(data: list) -> list:
    """Filter data to last 30 days"""
    cutoff = date.today().replace(day=1)  # First day of current month
    return [d for d in data if d["date"] >= cutoff.isoformat()]


def aggregate_by_category(data: list) -> dict:
    """Aggregate downloads by category"""
    totals = {}
    for row in data:
        cat = row["category"]
        totals[cat] = totals.get(cat, 0) + row["downloads"]
    return totals


def humanize_date(date_str: str) -> str:
    """Convert ISO date string (YYYY-MM-DD) to human-readable format"""
    if not date_str:
        return date_str
    
    try:
        # Parse ISO date format (YYYY-MM-DD)
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        # Format as "Month Day, Year" (e.g., "December 7, 2025")
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        # If parsing fails, return the original string
        return date_str
