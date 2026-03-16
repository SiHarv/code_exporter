"""TXT exporter implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from scanner.file_scanner import SourceFile
from utils.helpers import build_file_block


def export_to_txt(
    output_path: str,
    source_files: list[SourceFile],
    summary_section: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Write exported code to a plain UTF-8 text file."""
    path = Path(output_path)
    total = len(source_files)

    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("CODE EXPORT\n\n")
        for index, src_file in enumerate(source_files, start=1):
            handle.write(build_file_block(src_file.relative_path, src_file.content))
            if progress_callback:
                progress_callback(index, total)

        handle.write(summary_section)
