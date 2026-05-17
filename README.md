# Preprocessing Unstructured Data

Local Python project for extracting, chunking, and exporting text from documents using [Unstructured](https://github.com/Unstructured-IO/unstructured). Built as part of a Packt course.

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

```powershell
python -m venv unstruct-rag-env
.\unstruct-rag-env\Scripts\Activate.ps1
pip install "unstructured[all-docs]"
pip install unstructured-inference
pip install python-dotenv
pip install chromadb
pip install openai
```

## Configuration

Create a `.env` file in the project root (never commit this file):

```
HF_TOKEN=hf_xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

## Usage

Place your source files in the `data/` folder and run the script matching the file type:

```powershell
python ./preprocessing/app_pdf.py  data/mindset.pdf
python ./preprocessing/app_html.py data/el_nino.html
python ./preprocessing/app_md.py   data/devops-roadmap.md
python ./preprocessing/app_pptx.py data/kg-paulo.pptx
```

### Output

Each script saves two files under `output/<source-name>/`:

| File | Contents |
|------|----------|
| `elements.json` | All extracted elements (raw, granular) |
| `chunks.json` | Chunked text ready for embedding/RAG |

Example after running `app_pdf.py data/mindset.pdf`:

```
output/
  mindset/
    elements.json
    chunks.json
```

Each chunk in `chunks.json` contains:
- `text` — the content to embed and send to an LLM
- `metadata` — source file, page number, file type (for citations)

### RAG — index and query

After generating `chunks.json`, index it into Chroma and query with metadata filtering:

```powershell
# Index chunks (runs once, skips if already indexed)
python ./preprocessing/app_rag.py output/mindset/chunks.json

# Ask a question
python ./preprocessing/app_rag.py output/mindset/chunks.json --query "What is a growth mindset?"

# Filter by chapter
python ./preprocessing/app_rag.py output/mindset/chunks.json --query "What is a growth mindset?" --chapter "Embracing a Growth Mindset"

# Filter by page number
python ./preprocessing/app_rag.py output/mindset/chunks.json --query "What is a growth mindset?" --page 7
```

The vector index is stored in `chroma_db/` (excluded from git).

### Table extraction and summarization

Extracts tables from a PDF, displays them as structured HTML, and summarizes with an LLM:

```powershell
python ./preprocessing/app_table.py data/embedded-images-tables.pdf
```

### Multi-document RAG bot

End-to-end pipeline that partitions, chunks, and indexes three document types (PDF, PPTX, Markdown) into a single Chroma collection, then answers questions with optional per-source filtering:

```powershell
# Kör med standardfiler
python ./preprocessing/app_rag_bot.py

# Eller välj egna filer
python ./preprocessing/app_rag_bot.py --pdf data/annan.pdf --pptx data/annan.pptx --md data/annan.md
```

Default-filer: `data/post_ocr.pdf`, `data/kg-paulo.pptx`, `data/devops-roadmap.md`

The vector index is stored in `chroma_db_rag/` (excluded from git).

| Script | vs `app_rag.py` |
|--------|----------------|
| `app_rag.py` | Flexible — takes any `chunks.json`, skips re-indexing, supports chapter/page filters |
| `app_rag_bot.py` | Complete — partitions + indexes + queries in one run, multi-document, source filtering |

## Strategy (PDF only)

In `preprocessing/app_pdf.py` you can choose between two strategies:

| Strategy | Speed | Requires | Best for |
|----------|-------|----------|----------|
| `fast` | Fast | Nothing extra | PDFs with a built-in text layer |
| `hi_res` | Slow | Tesseract + Poppler + YOLOX model (217 MB, downloaded on first run) | Scanned PDFs, tables, complex layouts |
