from unstructured.partition.pptx import partition_pptx
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json, convert_to_dict
from unstructured.cleaners.core import clean_extra_whitespace
import json
import os

DATA_DIR = "../data"
PPTX_FILE = os.path.join(DATA_DIR, "kg-paulo.pptx")

# ---------- 1. Partition ----------
print("=== Partitioning PPTX ===")
elements = partition_pptx(filename=PPTX_FILE, include_metadata=True)
print(f"Number of elements: {len(elements)}\n")

# ---------- 2. Inspect elements ----------
print("=== Element types ===")
from collections import Counter
type_counts = Counter(type(el).__name__ for el in elements)
for el_type, count in type_counts.most_common():
    print(f"  {el_type}: {count}")

print("\n=== First 5 elements ===")
for el in elements[:5]:
    text = clean_extra_whitespace(el.text)
    print(f"[{type(el).__name__}] {text[:120]}")

# ---------- 3. Chunk by title ----------
print("\n=== Chunks (chunk_by_title) ===")
chunks = chunk_by_title(elements, max_characters=500, new_after_n_chars=400)
print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i+1} ---")
    print(chunk.text[:300])

# ---------- 4. Export to JSON ----------
output_file = "elements_pptx.json"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(elements_to_json(elements))
print(f"\n=== Exported {len(elements)} elements to {output_file} ===")

# ---------- 5. Metadata for first element ----------
print("\n=== Metadata (element 0) ===")
if elements:
    data = convert_to_dict(elements[:1])
    print(json.dumps(data[0], indent=2, ensure_ascii=False))
