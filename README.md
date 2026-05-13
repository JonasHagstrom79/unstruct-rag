# Preprocessing Unstructured Data

Local Python project for extracting and processing text from PDF files using [Unstructured](https://github.com/Unstructured-IO/unstructured). Built as part of a Packt course.

## Requirements

- Python 3.x
- Windows (instructions below apply to Windows)

### System Dependencies

Install via winget:

```powershell
winget install --id UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
winget install --id oschwartz10612.Poppler --accept-source-agreements --accept-package-agreements
```

Add to PATH (run one line at a time):

```powershell
$p1 = "C:\Users\<your-username>\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_"
$p2 = "Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin"
$env:PATH += ";C:\Program Files\Tesseract-OCR;" + $p1 + $p2
```

> For a permanent PATH change, restart your computer after running `[Environment]::SetEnvironmentVariable(...)`.

## Installation

```bash
python -m venv unstruct-rag-env
.\unstruct-rag-env\Scripts\Activate.ps1
pip install "unstructured[all-docs]"
pip install unstructured-inference
```

## Usage

Place a PDF file in the project folder and update `PDF_FILE` in `app.py`:

```python
PDF_FILE = "your-file.pdf"
```

Then run:

```bash
python app.py
```

### Output

- Prints element types (Title, NarrativeText, Table, etc.) and counts
- Displays the first 5 extracted elements
- Chunks the content by headings
- Exports all elements to `elements.json`
- Displays metadata for the first element (coordinates, page number, file type)

## Strategy

In `app.py` you can choose between two strategies:

| Strategy | Speed | Requires | Best for |
|----------|-------|----------|----------|
| `fast` | Fast | Nothing extra | PDFs with a built-in text layer |
| `hi_res` | Slow | Tesseract + Poppler + YOLOX model (217 MB, downloaded on first run) | Scanned PDFs, tables, complex layouts |
