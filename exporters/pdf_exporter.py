"""PDF exporter implementation."""

from __future__ import annotations

from typing import Callable

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from scanner.file_scanner import SourceFile


def _wrap_line_by_chars(text: str, max_chars: int) -> list[str]:
    """Wrap a line by fixed character width for stable PDF rendering."""
    if max_chars <= 0:
        return [text]

    if len(text) <= max_chars:
        return [text]

    wrapped = []
    start = 0
    while start < len(text):
        wrapped.append(text[start : start + max_chars])
        start += max_chars
    return wrapped


def export_to_pdf(
    output_path: str,
    source_files: list[SourceFile],
    summary_section: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """Write exported code to PDF using monospaced text and safe page wrapping."""
    page_width, page_height = A4
    margin = 40
    y = page_height - margin
    line_height = 11
    font_name = "Courier"
    font_size = 9
    max_line_width = page_width - (2 * margin)

    # Estimate the maximum number of characters that fit using monospace width.
    char_width = canvas.Canvas(output_path).stringWidth("M", font_name, font_size) or 5.4
    max_chars_per_line = int(max_line_width // char_width)

    pdf = canvas.Canvas(output_path, pagesize=A4)
    pdf.setTitle("Code Export")
    pdf.setFont(font_name, font_size)

    def draw_line(line: str) -> None:
        nonlocal y
        if y <= margin:
            pdf.showPage()
            pdf.setFont(font_name, font_size)
            y = page_height - margin
        pdf.drawString(margin, y, line)
        y -= line_height

    def draw_text_block(text: str) -> None:
        for raw_line in text.splitlines() or [""]:
            for wrapped_line in _wrap_line_by_chars(raw_line, max_chars_per_line):
                draw_line(wrapped_line)

    draw_line("CODE EXPORT")
    draw_line("")

    total = len(source_files)
    separator = "=" * 50

    for index, src_file in enumerate(source_files, start=1):
        draw_line(separator)
        draw_line(f"FILE: {src_file.relative_path}")
        draw_line(separator)
        draw_line("")
        draw_text_block(src_file.content)
        draw_line("")

        if progress_callback:
            progress_callback(index, total)

    draw_text_block(summary_section)
    pdf.save()
