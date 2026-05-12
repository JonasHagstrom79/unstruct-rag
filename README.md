# Preprocessing Unstructured Data

Lokalt Python-projekt för att extrahera och bearbeta text från PDF-filer med [Unstructured](https://github.com/Unstructured-IO/unstructured). Byggt som del av en Packt-kurs.

## Krav

- Python 3.x
- Windows (instruktioner nedan gäller Windows)

### Systemberoenden

Installera via winget:

```powershell
winget install --id UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
winget install --id oschwartz10612.Poppler --accept-source-agreements --accept-package-agreements
```

Lägg till i PATH (kör en rad i taget):

```powershell
$p1 = "C:\Users\<ditt-användarnamn>\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_"
$p2 = "Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin"
$env:PATH += ";C:\Program Files\Tesseract-OCR;" + $p1 + $p2
```

> För permanent PATH-ändring, starta om datorn efter att ha kört `[Environment]::SetEnvironmentVariable(...)`.

## Installation

```bash
python -m venv unstruct-rag-env
.\unstruct-rag-env\Scripts\Activate.ps1
pip install "unstructured[all-docs]"
pip install unstructured-inference
```

## Användning

Lägg en PDF-fil i projektmappen och uppdatera `PDF_FILE` i `app.py`:

```python
PDF_FILE = "din-fil.pdf"
```

Kör sedan:

```bash
python app.py
```

### Output

- Skriver ut elementtyper (Title, NarrativeText, Table etc.) och antal
- Visar de 5 första extraherade elementen
- Chunkar innehållet efter rubriker
- Exporterar alla element till `elements.json`
- Visar metadata för första elementet (koordinater, sidnummer, filtyp)

## Strategi

I `app.py` kan du välja mellan två strategier:

| Strategi | Hastighet | Kräver | Passar |
|----------|-----------|--------|--------|
| `fast` | Snabb | Inget extra | PDF med inbyggt textlager |
| `hi_res` | Långsam | Tesseract + Poppler + YOLOX-modell (217 MB, laddas ned vid första körning) | Skannade PDFer, tabeller, komplex layout |
