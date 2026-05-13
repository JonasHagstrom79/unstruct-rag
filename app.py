from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json, convert_to_dict
from unstructured.cleaners.core import clean_extra_whitespace
import json
import os

DATA_DIR = "data"
PDF_FILE = os.path.join(DATA_DIR, "milgram-1.pdf")

# ---------- 1. Partition ----------
print("=== Partitionerar PDF ===")
elements = partition_pdf(
    filename=PDF_FILE,
    strategy="hi_res",        # "fast" | "hi_res" (hi_res kräver Tesseract + Poppler + YOLOX)
    include_metadata=True,
)

print(f"Antal element: {len(elements)}\n")

# ---------- 2. Inspektera element ----------
print("=== Elementtyper ===")
from collections import Counter
type_counts = Counter(type(el).__name__ for el in elements)
for el_type, count in type_counts.most_common():
    print(f"  {el_type}: {count}")

print("\n=== Första 5 element ===")
for el in elements[:5]:
    text = clean_extra_whitespace(el.text)
    print(f"[{type(el).__name__}] {text[:120]}")

# ---------- 3. Chunka efter rubrik ----------
print("\n=== Chunkar (chunk_by_title) ===")
chunks = chunk_by_title(
    elements,
    max_characters=500,
    new_after_n_chars=400,
)
print(f"Antal chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i+1} ---")
    print(chunk.text[:300])

# ---------- 4. Exportera till JSON ----------
output_file = "elements.json"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(elements_to_json(elements))
print(f"\n=== Exporterat {len(elements)} element till {output_file} ===")

# ---------- 5. Visa metadata för första element ----------
print("\n=== Metadata (element 0) ===")
if elements:
    data = convert_to_dict(elements[:1])
    print(json.dumps(data[0], indent=2, ensure_ascii=False))
