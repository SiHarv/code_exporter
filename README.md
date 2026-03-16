# Code Exporter (Tkinter)

A beginner-friendly desktop app that scans a root folder recursively and exports source code files (`.php`, `.dart`, `.js`) into:
- TXT
- DOCX
- PDF

## Features

- Choose root folder from GUI
- Select included extensions with checkboxes
- Choose output format
- Optional output filename field
- Editable excluded folders list
- Status/progress panel
- Summary panel with:
  - selected folder
  - files found
  - files exported
  - skipped folders
- UTF-8 decoding with fallback encodings
- Binary file detection and skipping
- Final summary section included in exported files

## Default Excluded Folders

- `vendor`
- `node_modules`
- `.git`
- `.idea`
- `.vscode`
- `storage`
- `bootstrap/cache`
- `.dart_tool`
- `build`
- `ios/Pods`
- `android/.gradle`
- `__pycache__`

## Project Structure

```text
code_exporter/
|- main.py
|- exporters/
|  |- txt_exporter.py
|  |- docx_exporter.py
|  |- pdf_exporter.py
|- scanner/
|  |- file_scanner.py
|- utils/
|  |- helpers.py
|- requirements.txt
```

## Run Locally (Windows-friendly)

1. Open terminal in the `code_exporter` folder.
2. Activate your virtual environment.

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Linux
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Run the app.

```bash
python main.py
```

## Notes

- `tkinter` is included with standard Python on most Windows installs.
- If Python was installed without `tkinter`, reinstall Python and enable `tcl/tk` support.
