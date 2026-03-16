"""Folder scanning logic for collecting source code files recursively."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from utils.helpers import (
    is_probably_binary,
    normalize_path_for_compare,
    safe_read_text,
    should_exclude_dir,
)


@dataclass
class SourceFile:
    """Represents a source file that is safe to export."""

    absolute_path: Path
    relative_path: str
    content: str
    encoding: str


@dataclass
class ScanResult:
    """Structured output from the recursive scan operation."""

    source_files: list[SourceFile] = field(default_factory=list)
    files_found: int = 0
    skipped_folders: list[str] = field(default_factory=list)
    decode_failed_files: list[str] = field(default_factory=list)
    binary_skipped_files: list[str] = field(default_factory=list)


def scan_source_files(
    root_folder: str,
    include_extensions: set[str],
    excluded_dir_names: set[str],
    excluded_relative_paths: set[str],
    log_callback: Callable[[str], None] | None = None,
) -> ScanResult:
    """Recursively scan a folder and collect readable source files."""
    result = ScanResult()
    root_path = Path(root_folder).resolve()
    skipped_folder_set: set[str] = set()

    for current_dir, dir_names, file_names in os.walk(root_path, topdown=True):
        current_path = Path(current_dir)

        # Filter directory traversal in-place so excluded folders are never entered.
        allowed_dir_names = []
        for folder_name in dir_names:
            folder_path = current_path / folder_name
            relative_folder = normalize_path_for_compare(str(folder_path.relative_to(root_path)))
            if should_exclude_dir(relative_folder, folder_name, excluded_dir_names, excluded_relative_paths):
                skipped_folder_set.add(relative_folder)
                continue
            allowed_dir_names.append(folder_name)
        dir_names[:] = allowed_dir_names

        for file_name in file_names:
            file_path = current_path / file_name
            extension = file_path.suffix.lower()
            if extension not in include_extensions:
                continue

            result.files_found += 1
            relative_file = normalize_path_for_compare(str(file_path.relative_to(root_path)))

            if is_probably_binary(file_path):
                result.binary_skipped_files.append(relative_file)
                if log_callback:
                    log_callback(f"Skipped binary file: {relative_file}")
                continue

            content, encoding, error = safe_read_text(file_path)
            if content is None or encoding is None:
                result.decode_failed_files.append(relative_file)
                if log_callback:
                    log_callback(f"Skipped decode failure: {relative_file} ({error})")
                continue

            result.source_files.append(
                SourceFile(
                    absolute_path=file_path,
                    relative_path=relative_file,
                    content=content,
                    encoding=encoding,
                )
            )

    result.skipped_folders = sorted(skipped_folder_set)
    result.source_files.sort(key=lambda item: item.relative_path.lower())
    return result
