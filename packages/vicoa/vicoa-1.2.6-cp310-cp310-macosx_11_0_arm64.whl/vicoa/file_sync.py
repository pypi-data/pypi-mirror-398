"""File syncing for @ mention autocomplete.

This module handles scanning project directories and syncing file lists
to the backend for autocomplete functionality. It respects .gitignore
patterns and excludes common cache/build directories.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import pathspec
except ImportError:
    pathspec = None  # Graceful degradation if not installed


# Common patterns to always exclude (even if not in .gitignore)
# These are directories/files that are rarely useful for @ mentions
DEFAULT_EXCLUDE_PATTERNS = [
    ".git/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "__pycache__/",
    "node_modules/",
    ".venv/",
    "venv/",
    ".tox/",
    ".eggs/",
    "*.egg-info/",
    "dist/",
    "build/",
    "target/",  # Rust build output
    ".next/",  # Next.js
    ".nuxt/",  # Nuxt
    "coverage/",
    ".coverage",
    ".nyc_output/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
]


def get_excluded_dir_names() -> set:
    """Extract directory names from DEFAULT_EXCLUDE_PATTERNS.

    Converts patterns like ".git/", "node_modules/" into a set of directory
    names for use in directory filtering. Skips file patterns (*.ext).

    Returns:
        Set of directory names to exclude (e.g., {".git", "node_modules", ...})
    """
    excluded = set()
    for pattern in DEFAULT_EXCLUDE_PATTERNS:
        # Skip file patterns (contain wildcards)
        if "*" in pattern:
            continue

        # Strip trailing slashes and add to set
        dir_name = pattern.rstrip("/")
        if dir_name:  # Ignore empty strings
            excluded.add(dir_name)

    return excluded


def load_gitignore_patterns(project_path: Path) -> List[str]:
    """Load patterns from .gitignore file.

    Args:
        project_path: Path to project directory

    Returns:
        List of gitignore patterns
    """
    gitignore_path = project_path / ".gitignore"
    if not gitignore_path.exists():
        return []

    patterns = []
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
    except Exception:
        # Silently ignore errors reading .gitignore
        pass

    return patterns


def get_cache_path(project_path: str) -> Path:
    """Get cache file path for a given project path.

    Uses SHA256 hash of normalized project path to generate unique cache filename.

    Args:
        project_path: Absolute path to project directory

    Returns:
        Path to cache file in ~/.vicoa/cache/
    """
    # Normalize path and create hash
    normalized = os.path.realpath(project_path)
    path_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]

    # Cache directory: ~/.vicoa/cache/
    cache_dir = Path.home() / ".vicoa" / "cache"
    cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    return cache_dir / f"{path_hash}.json"


def load_sync_cache(project_path: str) -> Dict[str, Any]:
    """Load sync cache for a project.

    Args:
        project_path: Absolute path to project directory

    Returns:
        Cache dict with keys: newest_dir_mtime, file_count, last_sync_timestamp
        Returns empty dict if cache doesn't exist or is invalid.
    """
    cache_path = get_cache_path(project_path)

    if not cache_path.exists():
        return {}

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        # Invalid cache file
        return {}


def save_sync_cache(
    project_path: str,
    newest_dir_mtime: float,
    file_count: int,
) -> None:
    """Save sync cache for a project.

    Args:
        project_path: Absolute path to project directory
        newest_dir_mtime: Newest directory modification time (as float timestamp)
        file_count: Number of files synced
    """
    import time

    cache_path = get_cache_path(project_path)

    cache_data = {
        "project_path": os.path.realpath(project_path),
        "newest_dir_mtime": newest_dir_mtime,
        "file_count": file_count,
        "last_sync_timestamp": time.time(),
    }

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
    except Exception:
        # Silently fail - cache is optional
        pass


def get_newest_dir_mtime(project_path: str) -> float:
    """Get the newest modification time among all directories in project.

    This is a fast operation that only stats directories (not files).
    Used to detect structural changes (file/directory additions/deletions).

    Args:
        project_path: Absolute path to project directory

    Returns:
        Newest directory mtime as float timestamp, or 0.0 if project doesn't exist
    """
    base = Path(project_path)

    if not base.exists() or not base.is_dir():
        return 0.0

    # Get excluded directories from DEFAULT_EXCLUDE_PATTERNS
    skip_dirs = get_excluded_dir_names()

    try:
        # Start with root directory mtime
        max_mtime = base.stat().st_mtime

        # Scan all subdirectories (fast - only directories, not files)
        for dir_path in base.rglob("*/"):
            # Skip if any parent directory should be excluded
            if any(part in skip_dirs for part in dir_path.parts):
                continue

            try:
                mtime = dir_path.stat().st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
            except (OSError, PermissionError):
                # Skip directories we can't access
                continue

        return max_mtime
    except Exception:
        # If anything fails, return 0 to force rescan
        return 0.0


def scan_project_files(
    project_path: str,
    max_files: int = 100_000,
    respect_gitignore: bool = True,
    additional_excludes: Optional[List[str]] = None,
) -> List[str]:
    """Scan project directory for files to enable @ mentions.

    This function walks the project directory and collects file paths,
    respecting .gitignore patterns and common exclude patterns.

    Args:
        project_path: Absolute path to project directory
        max_files: Maximum number of files to return (default 100,000)
        respect_gitignore: Whether to respect .gitignore patterns (default True)
        additional_excludes: Additional patterns to exclude (optional)

    Returns:
        List of folder paths (with "/" suffix) and file paths from project_path.
        Example: ["src/", "src/components/", "lib/", "src/main.py", "lib/utils.ts"]

    Note:
        Duplicates between DEFAULT_EXCLUDE_PATTERNS and .gitignore are handled
        automatically by pathspec - no need for manual deduplication.
    """
    base = Path(project_path)
    if not base.exists() or not base.is_dir():
        return []

    # Collect all exclude patterns
    exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.copy()

    if respect_gitignore:
        gitignore_patterns = load_gitignore_patterns(base)
        exclude_patterns.extend(gitignore_patterns)

    if additional_excludes:
        exclude_patterns.extend(additional_excludes)

    # Create pathspec matcher (handles duplicates internally)
    if pathspec:
        spec = pathspec.PathSpec.from_lines("gitwildmatch", exclude_patterns)
    else:
        # Fallback: no filtering if pathspec not available
        spec = None
        print("Warning: pathspec not installed, file filtering may not work correctly")

    # Scan files and extract folders
    files = []
    folders = set()
    try:
        for file_path in base.rglob("*"):
            # Only include files, not directories
            if not file_path.is_file():
                continue

            try:
                relative_path = file_path.relative_to(base)
                relative_str = str(relative_path)

                # Check if file should be excluded
                if spec and spec.match_file(relative_str):
                    continue

                files.append(relative_str)

                # Extract parent folders (e.g., "src/components/chat.tsx" -> {"src/", "src/components/"})
                parts = relative_path.parts
                for i in range(len(parts) - 1):  # Exclude the file itself
                    folder = "/".join(parts[: i + 1]) + "/"
                    folders.add(folder)

                # Stop at max_files limit
                if len(files) >= max_files:
                    print(f"⚠️  Large project detected: {max_files}+ files found")
                    print(f"    Only syncing first {max_files} files for performance")
                    print("    File mentions may be incomplete")
                    break

            except ValueError:
                # Skip files outside base path (shouldn't happen with rglob)
                continue

    except Exception as e:
        print(f"Warning: Error scanning files: {e}")

    # Combine folders and files (no sorting for performance)
    return list(folders) + files


def sync_project_files(
    api_key: str,
    base_url: str,
    project_path: str,
) -> None:
    """Sync project files to backend for @ mention autocomplete.

    This is the main entry point for file syncing. It scans the project
    directory and uploads the file list to the backend.

    Uses directory modification time caching to skip unnecessary rescans.
    Only rescans if directories have been added/deleted/modified since last sync.

    Args:
        api_key: Vicoa API key
        base_url: Vicoa API base URL
        project_path: Absolute path to project directory

    Note:
        This function silently fails to avoid blocking agent startup
        if file sync encounters errors.
    """
    try:
        from vicoa.sdk.client import VicoaClient

        # Normalize project path (resolve symlinks, remove trailing slash)
        normalized_path = os.path.realpath(project_path)

        # Quick check: get newest directory mtime
        current_mtime = get_newest_dir_mtime(normalized_path)

        # Load cache
        cache = load_sync_cache(normalized_path)
        cached_mtime = cache.get("newest_dir_mtime")

        # If cache exists and mtime hasn't changed, skip sync
        if cached_mtime is not None and current_mtime <= cached_mtime:
            # No structural changes detected - skip sync
            return

        # Cache miss or changes detected - perform full scan
        print("Preparing files for @ mentions...")

        files = scan_project_files(normalized_path)

        if not files:
            # No files to sync
            return

        # Update cache BEFORE syncing to backend
        # This ensures cache is saved even if backend sync fails
        current_mtime = get_newest_dir_mtime(normalized_path)
        save_sync_cache(normalized_path, current_mtime, len(files))

        # Sync to backend (allow this to fail without affecting cache)
        try:
            client = VicoaClient(api_key=api_key, base_url=base_url)
            client.sync_files(project_path=normalized_path, files=files)
        except Exception:
            # Backend sync failed, but cache was already saved
            # Silently continue - don't block agent startup
            pass

    except Exception:
        # Unexpected error during scan/cache operations
        # Silently fail - don't block agent startup
        pass
