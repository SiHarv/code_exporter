"""Shared helper functions for the code exporter app."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_EXTENSIONS = [".php", ".dart", ".js"]

# Folder names that should always be excluded when scanning.
DEFAULT_EXCLUDED_DIR_NAMES = {
    "vendor",
    "node_modules",
    ".git",
    ".idea",
    ".vscode",
    "storage",
    ".dart_tool",
    "build",
    "__pycache__",
}

# Relative folder paths that should always be excluded when scanning.
DEFAULT_EXCLUDED_RELATIVE_PATHS = {
    "bootstrap/cache",
    "ios/Pods",
    "android/.gradle",
}

SEPARATOR = "=" * 50


def normalize_extension_list(extensions: Iterable[str]) -> set[str]:
    """Return normalized extension strings like {'.php', '.js'} in lowercase."""
    normalized = set()
    for ext in extensions:
        cleaned = ext.strip().lower()
        if not cleaned:
            continue
        if not cleaned.startswith("."):
            cleaned = f".{cleaned}"
        normalized.add(cleaned)
    return normalized


def normalize_path_for_compare(value: str) -> str:
    """Normalize path strings to a stable forward-slash format for comparisons."""
    return value.replace("\\", "/").strip("/")


def split_excluded_inputs(excluded_items: Iterable[str]) -> tuple[set[str], set[str]]:
    """Split excluded items into folder names and relative paths.

    Inputs that contain '/' are treated as relative paths.
    Other values are treated as folder names.
    """
    excluded_names: set[str] = set()
    excluded_paths: set[str] = set()

    for item in excluded_items:
        cleaned = item.strip()
        if not cleaned:
            continue

        normalized = normalize_path_for_compare(cleaned)
        if "/" in normalized:
            excluded_paths.add(normalized)
        else:
            excluded_names.add(normalized)

    return excluded_names, excluded_paths


def should_exclude_dir(relative_dir: str, dir_name: str, excluded_names: set[str], excluded_paths: set[str]) -> bool:
    """Return True when a directory should be skipped by the scanner."""
    normalized_rel = normalize_path_for_compare(relative_dir)

    if dir_name in excluded_names:
        return True

    if normalized_rel in excluded_paths:
        return True

    for excluded_path in excluded_paths:
        if normalized_rel.startswith(f"{excluded_path}/"):
            return True

    return False


def is_probably_binary(file_path: Path, chunk_size: int = 4096) -> bool:
    """Quickly detect binary files by checking for null bytes and control-character ratio."""
    try:
        data = file_path.read_bytes()[:chunk_size]
    except OSError:
        return True

    if not data:
        return False

    if b"\x00" in data:
        return True

    # Treat too many unusual control characters as a binary indicator.
    text_like = bytes(range(32, 127)) + b"\n\r\t\b\f"
    non_text_count = sum(byte not in text_like for byte in data)
    return (non_text_count / len(data)) > 0.30


def safe_read_text(file_path: Path) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Read text with UTF-8 first, then fallback encodings.

    Returns:
        (content, encoding_used, error_message)
    """
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]

    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding), encoding, None
        except UnicodeDecodeError:
            continue
        except OSError as err:
            return None, None, str(err)

    return None, None, "Could not decode using UTF-8 or fallback encodings"


def build_file_block(relative_path: str, content: str) -> str:
    """Create the file section format requested by the project requirements."""
    return (
        f"{SEPARATOR}\n"
        f"FILE: {relative_path}\n"
        f"{SEPARATOR}\n\n"
        f"{content}\n\n"
    )


def default_export_name() -> str:
    """Return a timestamp-based fallback file name."""
    return datetime.now().strftime("code_export_%Y%m%d_%H%M%S")


def build_summary_section(
    root_folder: str,
    included_extensions: Iterable[str],
    excluded_items: Iterable[str],
    total_exported: int,
    decode_skipped: Iterable[str],
) -> str:
    """Build the final summary text that is appended to all output formats."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    included = ", ".join(sorted(included_extensions))
    excluded = ", ".join(sorted(excluded_items))
    skipped_decode = list(decode_skipped)

    summary_lines = [
        "",
        SEPARATOR,
        "EXPORT SUMMARY",
        SEPARATOR,
        f"Export Date/Time: {timestamp}",
        f"Root Folder: {root_folder}",
        f"Included Extensions: {included}",
        f"Excluded Folders: {excluded}",
        f"Total Exported Files: {total_exported}",
    ]

    if skipped_decode:
        summary_lines.append(f"Skipped (Decode Failed): {len(skipped_decode)}")
        for item in skipped_decode:
            summary_lines.append(f"- {item}")

    summary_lines.append("")
    return "\n".join(summary_lines)
