from dotenv import load_dotenv, dotenv_values
import os
import pprint
import argparse
from io import StringIO

load_dotenv()
_env = dotenv_values()
for _key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
    if _env.get("HF_TOKEN"):
        os.environ[_key] = _env["HF_TOKEN"]

from unstructured.partition.pdf import partition_pdf
from openai import OpenAI
from lxml import etree
import unstructured_pytesseract

unstructured_pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

parser = argparse.ArgumentParser(description="Extract and summarize tables from a PDF file.")
parser.add_argument("file", help="Path to the PDF file")
args = parser.parse_args()

input_filepath = args.file

# ---------- 1. Partition with table inference ----------
print("=== Partitioning PDF (hi_res + table inference) ===")
elements = partition_pdf(
    filename=input_filepath,
    strategy="hi_res",
    infer_table_structure=True,
)
print(f"Total elements: {len(elements)}")

# ---------- 2. Filter tables ----------
tables = [el for el in elements if el.category == "Table"]
print(f"Tables found: {len(tables)}\n")

# ---------- 3. First table: raw text ----------
print("=== Table 1 — raw text ===")
pprint.pprint(tables[0].text)

# ---------- 4. First table: pretty-printed HTML ----------
print("\n=== Table 1 — HTML structure ===")
table_html = tables[0].metadata.text_as_html
xml_parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse(StringIO(table_html), xml_parser)
print(etree.tostring(tree, pretty_print=True).decode())

# ---------- 5. Summarize table with OpenAI ----------
print("\n=== Table 1 — LLM summary ===")
openai_client = OpenAI(api_key=_env.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": f"Summarize the following HTML table concisely:\n\n{table_html}"},
    ],
    temperature=0,
)
print(response.choices[0].message.content)
