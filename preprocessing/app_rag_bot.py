from dotenv import dotenv_values
import os
import pprint
import argparse
from io import StringIO

_env = dotenv_values()

for _key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
    if _env.get("HF_TOKEN"):
        os.environ[_key] = _env["HF_TOKEN"]

from unstructured.partition.pdf import partition_pdf
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.md import partition_md
from unstructured.chunking.title import chunk_by_title
from lxml import etree
import unstructured_pytesseract

unstructured_pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

openai_api_key = _env.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

parser = argparse.ArgumentParser(description="Multi-document RAG bot (PDF + PPTX + Markdown).")
parser.add_argument("--pdf",   default="data/post_ocr.pdf",      help="Path to PDF file")
parser.add_argument("--pptx",  default="data/kg-paulo.pptx",     help="Path to PPTX file")
parser.add_argument("--md",    default="data/devops-roadmap.md", help="Path to Markdown file")
parser.add_argument("--reset", action="store_true",              help="Clear existing index and re-index documents")
args = parser.parse_args()

persist_directory = "./chroma_db_rag/"

# ---------- 1. Partition PDF ----------
print(f"=== Partitioning PDF ({args.pdf}) ===")
pdf_elements = partition_pdf(
    filename=args.pdf,
    strategy="hi_res",
    infer_table_structure=True,
)
print(f"PDF elements: {len(pdf_elements)}")

res = pdf_elements[0].to_dict()
pprint.pprint(res)

# Extract and display first table
tables = [el for el in pdf_elements if el.category == "Table"]
if tables:
    table_html = tables[0].metadata.text_as_html
    xml_parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(StringIO(table_html), xml_parser)
    print("\n=== First Table (HTML) ===")
    print(etree.tostring(tree, pretty_print=True).decode())

# ---------- 2. Filter references and headers ----------
reference_title = [
    el for el in pdf_elements if el.text == "References" and el.category == "Title"
]
if reference_title:
    reference_title = reference_title[0]
    references_id = reference_title.id
    pdf_elements = [el for el in pdf_elements if el.metadata.parent_id != references_id]
    print("\n== Reference Title ==")
    pprint.pprint(reference_title.to_dict())

headers = [el for el in pdf_elements if el.category == "Header"]
if headers:
    print("\n== First Header ==")
    pprint.pprint(headers[0].to_dict())

pdf_elements = [el for el in pdf_elements if el.category != "Header"]
print(f"PDF elements after filtering: {len(pdf_elements)}")

# ---------- 3. Partition PPTX ----------
print(f"\n=== Partitioning PPTX ({args.pptx}) ===")
pptx_elements = partition_pptx(filename=args.pptx)
print(f"PPTX elements: {len(pptx_elements)}")

# ---------- 4. Partition Markdown ----------
print(f"\n=== Partitioning Markdown ({args.md}) ===")
md_elements = partition_md(filename=args.md)
print(f"MD elements: {len(md_elements)}")

# ---------- 5. Chunk all documents together ----------
elements = chunk_by_title(
    pdf_elements + pptx_elements + md_elements,
    combine_text_under_n_chars=100,
    max_characters=500,
    new_after_n_chars=400,
)
print(f"\nTotal chunks: {len(elements)}")

# ---------- 5b. Export elements and chunks to JSON ----------
import json
from unstructured.staging.base import elements_to_json

def export_source(source_elements, source_path):
    name = os.path.splitext(os.path.basename(source_path))[0]
    out_dir = os.path.join(os.path.dirname(__file__), "../output", name)
    os.makedirs(out_dir, exist_ok=True)
    elements_file = os.path.join(out_dir, "elements.json")
    with open(elements_file, "w", encoding="utf-8") as f:
        f.write(elements_to_json(source_elements))
    print(f"Exported {len(source_elements)} elements → {elements_file}")

export_source(pdf_elements, args.pdf)
export_source(pptx_elements, args.pptx)
export_source(md_elements, args.md)

chunks_file = os.path.join(os.path.dirname(__file__), "../output/rag_bot_chunks.json")
chunks_dicts = [{"text": el.text, "metadata": el.metadata.to_dict()} for el in elements]
with open(chunks_file, "w", encoding="utf-8") as f:
    json.dump(chunks_dicts, f, indent=2, ensure_ascii=False)
print(f"Exported {len(elements)} combined chunks → {chunks_file}")

# ---------- 6. Build LangChain documents ----------
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata

embeddings = OpenAIEmbeddings(api_key=openai_api_key)

# ---------- 7. Index into Chroma (skip if already indexed) ----------
vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
existing_count = vector_store._collection.count()

if existing_count > 0 and not args.reset:
    print(f"\nDatabase already has {existing_count} documents. Skipping indexing. (Use --reset to re-index.)")
else:
    if args.reset and existing_count > 0:
        vector_store.delete_collection()
        print(f"Cleared existing index ({existing_count} documents).")
    documents = []
    for element in elements:
        metadata = element.metadata.to_dict()
        metadata.pop("languages", None)
        metadata["source"] = metadata.get("filename", "unknown")
        documents.append(Document(page_content=element.text, metadata=metadata))

    print("\n== Sample Document ==")
    pprint.pprint(documents[3])

    Chroma.from_documents(
        filter_complex_metadata(documents),
        embeddings,
        persist_directory=persist_directory,
    )
    print(f"\nIndexed {len(documents)} documents into Chroma.")
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

# ---------- 8. Load persisted DB and create retriever ----------
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# ---------- 9. Build RAG chain (LCEL) ----------
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

template = """You are an AI assistant specialized in answering questions related to Advancing Post-OCR Correction:
A Comparative Study of Synthetic Data.
You are provided with the following extracted sections from a lengthy document and a related question. Please respond in a conversational manner.
If you are unsure of the answer, simply reply, "Hmm, I'm not sure." Avoid fabricating any responses.
You also know about DevOps roadmaps and Knowledge Graphs from the documents and context you were given.
Question: {input}
=========
{context}
=========
Respond in Markdown:"""

prompt = PromptTemplate.from_template(template)
llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", api_key=openai_api_key)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def build_chain(ret):
    return (
        {"context": ret | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

# ---------- 10. Queries ----------
print("\n== OCR Results ==\n")
pprint.pprint(build_chain(retriever).invoke("tell me about post-OCR domain?"))

print("\n== DevOps Results ==\n")
devops_retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 1, "filter": {"source": "devops-roadmap.md"}},
)
pprint.pprint(build_chain(devops_retriever).invoke(
    "what are some popular programming languages for DevOps? and what resources are available for learning them?"
))

print("\n== KG Results ==\n")
kg_retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 1, "filter": {"source": "kg-paulo.pptx"}},
)
pprint.pprint(build_chain(kg_retriever).invoke(
    "give me the main key points about Knowledge Graph?"
))
