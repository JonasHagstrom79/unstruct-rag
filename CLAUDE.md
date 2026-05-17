# Preprocessing Unstructured Data — Projektöversikt

Packt-kurs om att extrahera, chunka och indexera text från dokument (PDF, HTML, Markdown, PPTX) med Unstructured-ramverket och ChromaDB.

## Vad som är implementerat

### Partitioneringsskript (`intro/`)
| Skript | Filtyp | Output |
|---|---|---|
| `app_pdf.py` | PDF (hi_res, OCR) | `output/<namn>/elements.json` + `chunks.json` |
| `app_html.py` | HTML | samma |
| `app_md.py` | Markdown | samma |
| `app_pptx.py` | PowerPoint | samma |

Alla skript chunkar med `chunk_by_title(combine_text_under_n_chars=100, max_characters=500, new_after_n_chars=400)`.

### RAG-pipeline (`intro/app_rag.py`)
- Läser `chunks.json`, embeddar med OpenAI (`text-embedding-3-small`), indexerar i ChromaDB
- Guardrail: hoppar över indexering om collection redan finns (`get_or_create_collection` + `count()`)
- Stöder hybrid search med `--chapter` och `--page` metadata-filter
- Vektorindex lagras i `chroma_db/`

## Hur man kör

```powershell
# Aktivera venv
.\unstruct-rag-env\Scripts\Activate.ps1

# Partitionera ett dokument
python ./intro/app_pdf.py data/mindset.pdf

# Indexera och fråga
python ./intro/app_rag.py output/mindset/chunks.json --query "What is a growth mindset?"

# Med metadata-filter
python ./intro/app_rag.py output/mindset/chunks.json --query "..." --chapter "Embracing a Growth Mindset"
python ./intro/app_rag.py output/mindset/chunks.json --query "..." --page 7
```

## Viktigt — Windows-specifikt
- Tesseract måste sättas explicit i varje skript: `unstructured_pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`
- Venv-subprocessar ärver inte PATH på Windows — PATH-lösningen räcker inte

## Pågående kurs — nästa sektion
Document Image Analysis (DIA): preprocessing av komplexa PDF:er och bilder.
Två tekniker:
- **Document Layout Models** (YOLOX) — object detection + OCR, det `hi_res` redan använder
- **Vision Transformers** — generativ, flexibel men dyrare och kan hallucinera

Hands-on-kod för bilder/tabeller kommer härnäst.
