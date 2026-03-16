"""Tkinter desktop app for exporting code files into TXT, DOCX, or PDF."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from exporters.docx_exporter import export_to_docx
from exporters.pdf_exporter import export_to_pdf
from exporters.txt_exporter import export_to_txt
from scanner.file_scanner import ScanResult, scan_source_files
from utils.helpers import (
    DEFAULT_EXCLUDED_DIR_NAMES,
    DEFAULT_EXCLUDED_RELATIVE_PATHS,
    build_summary_section,
    default_export_name,
    normalize_extension_list,
    split_excluded_inputs,
)


class CodeExporterApp:
    """Main GUI application class."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Code Exporter")
        self.root.geometry("1024x760")

        self.selected_folder = tk.StringVar(value="No folder selected")
        self.filename_var = tk.StringVar(value="")
        self.output_format_var = tk.StringVar(value="TXT")
        self.custom_extensions_var = tk.StringVar(value="")

        self.summary_folder_var = tk.StringVar(value="-")
        self.summary_found_var = tk.StringVar(value="0")
        self.summary_exported_var = tk.StringVar(value="0")
        self.summary_skipped_var = tk.StringVar(value="0")

        self.extension_vars = {
            ".php": tk.BooleanVar(value=True),
            ".dart": tk.BooleanVar(value=True),
            ".js": tk.BooleanVar(value=True),
            ".html": tk.BooleanVar(value=True),
            ".css": tk.BooleanVar(value=True),
        }

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        folder_frame = ttk.LabelFrame(container, text="1) Select Root Folder", padding=10)
        folder_frame.pack(fill="x", pady=6)

        ttk.Button(folder_frame, text="Choose Folder", command=self.choose_folder).pack(side="left")
        ttk.Label(folder_frame, textvariable=self.selected_folder, wraplength=760).pack(
            side="left", padx=12
        )

        settings_frame = ttk.LabelFrame(container, text="2) Export Settings", padding=10)
        settings_frame.pack(fill="x", pady=6)

        ext_frame = ttk.Frame(settings_frame)
        ext_frame.pack(anchor="w", fill="x")
        ttk.Label(ext_frame, text="Include extensions:").pack(side="left", padx=(0, 8))
        for ext, var in self.extension_vars.items():
            ttk.Checkbutton(ext_frame, text=ext, variable=var).pack(side="left", padx=4)

        custom_ext_frame = ttk.Frame(settings_frame)
        custom_ext_frame.pack(anchor="w", fill="x", pady=(8, 0))
        ttk.Label(custom_ext_frame, text="Custom extensions (comma-separated):").pack(
            side="left", padx=(0, 8)
        )
        ttk.Entry(custom_ext_frame, textvariable=self.custom_extensions_var, width=40).pack(side="left")

        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(anchor="w", fill="x", pady=(8, 0))
        ttk.Label(format_frame, text="Output format:").pack(side="left", padx=(0, 8))
        ttk.Combobox(
            format_frame,
            textvariable=self.output_format_var,
            values=["TXT", "DOCX", "PDF"],
            width=10,
            state="readonly",
        ).pack(side="left")

        ttk.Label(format_frame, text="Output filename (optional):").pack(side="left", padx=(20, 8))
        ttk.Entry(format_frame, textvariable=self.filename_var, width=35).pack(side="left")

        exclude_frame = ttk.LabelFrame(container, text="3) Excluded Folders (Editable)", padding=10)
        exclude_frame.pack(fill="x", pady=6)

        self.exclude_listbox = tk.Listbox(exclude_frame, height=8)
        self.exclude_listbox.pack(side="left", fill="x", expand=True)

        scroll = ttk.Scrollbar(exclude_frame, orient="vertical", command=self.exclude_listbox.yview)
        scroll.pack(side="left", fill="y")
        self.exclude_listbox.config(yscrollcommand=scroll.set)

        controls = ttk.Frame(exclude_frame)
        controls.pack(side="left", padx=10, anchor="n")

        self.exclude_entry = ttk.Entry(controls, width=30)
        self.exclude_entry.pack(fill="x")
        ttk.Button(controls, text="Add", command=self.add_excluded_item).pack(fill="x", pady=(6, 0))
        ttk.Button(controls, text="Remove Selected", command=self.remove_selected_excluded).pack(
            fill="x", pady=(6, 0)
        )

        for item in sorted(DEFAULT_EXCLUDED_DIR_NAMES | DEFAULT_EXCLUDED_RELATIVE_PATHS):
            self.exclude_listbox.insert("end", item)

        action_frame = ttk.Frame(container)
        action_frame.pack(fill="x", pady=8)

        ttk.Button(action_frame, text="Start Export", command=self.start_export).pack(side="left")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(
            action_frame,
            variable=self.progress_var,
            maximum=100,
            length=300,
            mode="determinate",
        )
        self.progress.pack(side="left", padx=10)

        status_frame = ttk.LabelFrame(container, text="Status / Progress", padding=10)
        status_frame.pack(fill="both", expand=True, pady=6)

        self.status_box = ScrolledText(status_frame, height=12, wrap="word")
        self.status_box.pack(fill="both", expand=True)
        self.status_box.configure(state="disabled")

        summary_frame = ttk.LabelFrame(container, text="Summary", padding=10)
        summary_frame.pack(fill="x", pady=6)

        ttk.Label(summary_frame, text="Selected folder:").grid(row=0, column=0, sticky="w")
        ttk.Label(summary_frame, textvariable=self.summary_folder_var, wraplength=760).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(summary_frame, text="Files found:").grid(row=1, column=0, sticky="w")
        ttk.Label(summary_frame, textvariable=self.summary_found_var).grid(row=1, column=1, sticky="w")

        ttk.Label(summary_frame, text="Files exported:").grid(row=2, column=0, sticky="w")
        ttk.Label(summary_frame, textvariable=self.summary_exported_var).grid(row=2, column=1, sticky="w")

        ttk.Label(summary_frame, text="Skipped folders:").grid(row=3, column=0, sticky="w")
        ttk.Label(summary_frame, textvariable=self.summary_skipped_var).grid(row=3, column=1, sticky="w")

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Choose root folder")
        if not selected:
            return

        self.selected_folder.set(selected)
        self.summary_folder_var.set(selected)
        self.log(f"Selected folder: {selected}")

    def add_excluded_item(self) -> None:
        value = self.exclude_entry.get().strip()
        if not value:
            return

        existing = set(self.exclude_listbox.get(0, "end"))
        if value in existing:
            self.log(f"Already excluded: {value}")
            return

        self.exclude_listbox.insert("end", value)
        self.exclude_entry.delete(0, "end")
        self.log(f"Added excluded folder: {value}")

    def remove_selected_excluded(self) -> None:
        selected_indices = list(self.exclude_listbox.curselection())
        if not selected_indices:
            return

        for index in reversed(selected_indices):
            value = self.exclude_listbox.get(index)
            self.exclude_listbox.delete(index)
            self.log(f"Removed excluded folder: {value}")

    def log(self, message: str) -> None:
        self.status_box.configure(state="normal")
        self.status_box.insert("end", f"{message}\n")
        self.status_box.see("end")
        self.status_box.configure(state="disabled")
        self.root.update_idletasks()

    def _get_selected_extensions(self) -> set[str]:
        selected = [ext for ext, var in self.extension_vars.items() if var.get()]

        custom_input = self.custom_extensions_var.get().strip()
        if custom_input:
            selected.extend(part.strip() for part in custom_input.split(","))

        return normalize_extension_list(selected)

    def _get_excluded_items(self) -> list[str]:
        return [self.exclude_listbox.get(i) for i in range(self.exclude_listbox.size())]

    def _choose_output_path(self, output_format: str, filename_base: str) -> str | None:
        ext_map = {"TXT": ".txt", "DOCX": ".docx", "PDF": ".pdf"}
        extension = ext_map[output_format]

        initial_name = filename_base if filename_base else default_export_name()
        if not initial_name.lower().endswith(extension):
            initial_name += extension

        return filedialog.asksaveasfilename(
            title="Choose export file location",
            defaultextension=extension,
            initialfile=initial_name,
            filetypes=[(f"{output_format} files", f"*{extension}"), ("All files", "*.*")],
        )

    def _update_export_progress(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress_var.set(0)
            return
        percent = (current / total) * 100
        self.progress_var.set(percent)
        self.root.update_idletasks()

    def _reset_progress(self) -> None:
        self.progress_var.set(0.0)
        self.summary_exported_var.set("0")
        self.root.update_idletasks()

    def start_export(self) -> None:
        folder = self.selected_folder.get()
        if folder == "No folder selected":
            messagebox.showwarning("Missing Folder", "Please choose a root folder first.")
            return

        selected_extensions = self._get_selected_extensions()
        if not selected_extensions:
            messagebox.showwarning("Missing Extensions", "Please select at least one extension.")
            return

        excluded_items = self._get_excluded_items()
        excluded_names, excluded_paths = split_excluded_inputs(excluded_items)

        output_format = self.output_format_var.get()
        filename_base = self.filename_var.get().strip()

        self._reset_progress()
        self.log("Starting recursive scan...")

        scan_result = scan_source_files(
            root_folder=folder,
            include_extensions=selected_extensions,
            excluded_dir_names=excluded_names,
            excluded_relative_paths=excluded_paths,
            log_callback=self.log,
        )

        self._update_summary_after_scan(scan_result)

        if not scan_result.source_files:
            self.log("No exportable files found.")
            messagebox.showinfo("No Files", "No matching readable source files were found.")
            return

        output_path = self._choose_output_path(output_format, filename_base)
        if not output_path:
            self.log("Export cancelled by user.")
            return

        summary_section = build_summary_section(
            root_folder=folder,
            included_extensions=sorted(selected_extensions),
            excluded_items=sorted(excluded_items),
            total_exported=len(scan_result.source_files),
            decode_skipped=scan_result.decode_failed_files,
        )

        self.log(f"Exporting {len(scan_result.source_files)} files to {output_format}...")

        try:
            if output_format == "TXT":
                export_to_txt(
                    output_path=output_path,
                    source_files=scan_result.source_files,
                    summary_section=summary_section,
                    progress_callback=self._update_export_progress,
                )
            elif output_format == "DOCX":
                export_to_docx(
                    output_path=output_path,
                    source_files=scan_result.source_files,
                    summary_section=summary_section,
                    progress_callback=self._update_export_progress,
                )
            elif output_format == "PDF":
                export_to_pdf(
                    output_path=output_path,
                    source_files=scan_result.source_files,
                    summary_section=summary_section,
                    progress_callback=self._update_export_progress,
                )
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

            self.summary_exported_var.set(str(len(scan_result.source_files)))
            self.log(f"Export complete: {output_path}")

            if scan_result.decode_failed_files:
                self.log(f"Decode skipped files: {len(scan_result.decode_failed_files)}")
            if scan_result.binary_skipped_files:
                self.log(f"Binary skipped files: {len(scan_result.binary_skipped_files)}")

            messagebox.showinfo("Success", f"Export finished successfully.\n\nSaved to:\n{output_path}")
        except Exception as err:  # noqa: BLE001 - show friendly error in GUI
            self.log(f"Export failed: {err}")
            messagebox.showerror("Export Failed", str(err))

    def _update_summary_after_scan(self, scan_result: ScanResult) -> None:
        self.summary_found_var.set(str(scan_result.files_found))
        self.summary_skipped_var.set(str(len(scan_result.skipped_folders)))

        self.log(f"Files found (matching extension): {scan_result.files_found}")
        self.log(f"Files ready to export: {len(scan_result.source_files)}")
        self.log(f"Skipped folders: {len(scan_result.skipped_folders)}")

        if scan_result.skipped_folders:
            preview = ", ".join(scan_result.skipped_folders[:6])
            if len(scan_result.skipped_folders) > 6:
                preview += ", ..."
            self.log(f"Skipped folder list: {preview}")


def main() -> None:
    root = tk.Tk()
    app = CodeExporterApp(root)
    app.log("Ready. Choose a folder and click Start Export.")
    root.mainloop()


if __name__ == "__main__":
    main()
