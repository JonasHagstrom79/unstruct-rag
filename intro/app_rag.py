from dotenv import load_dotenv
import argparse
import json
import os
import chromadb
from openai import OpenAI

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed(texts):
    response = openai_client.embeddings.create(
        input=texts,
        model="text-embedding-3-small",
    )
    return [item.embedding for item in response.data]


def extract_chapter(text):
    """First non-empty line of a chunk is always the section title from chunk_by_title."""
    for line in text.split("\n"):
        line = line.strip()
        if line:
            return line
    return ""


parser = argparse.ArgumentParser(description="Index chunks into Chroma and query with metadata filtering.")
parser.add_argument("chunks_file", help="Path to chunks.json (e.g. output/mindset/chunks.json)")
parser.add_argument("--query", help="Question to ask against the indexed chunks")
parser.add_argument("--page", type=int, help="Filter results to a specific page number")
parser.add_argument("--chapter", help="Filter results to a specific chapter/section title")
args = parser.parse_args()

# Derive collection name from parent folder: output/mindset/chunks.json -> "mindset"
collection_name = os.path.basename(os.path.dirname(os.path.abspath(args.chunks_file)))

chroma_client = chromadb.PersistentClient(
    path=os.path.join(os.path.dirname(__file__), "../chroma_db")
)
collection = chroma_client.get_or_create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"},
)

if collection.count() == 0:
    with open(args.chunks_file, encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Indexing {len(chunks)} chunks into '{collection_name}'...")

    documents = [c["text"] for c in chunks]
    ids = [f"{collection_name}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "filename": c["metadata"].get("filename") or "",
            "page_number": c["metadata"].get("page_number") or 0,
            "filetype": c["metadata"].get("filetype") or "",
            "chapter": extract_chapter(c["text"]),
        }
        for c in chunks
    ]
    embeddings = embed(documents)

    collection.add(documents=documents, ids=ids, metadatas=metadatas, embeddings=embeddings)
    print(f"Done. {len(chunks)} chunks stored in '{collection_name}'.")
else:
    print(f"Collection '{collection_name}' already has {collection.count()} chunks. Skipping indexing.")

if args.query:
    if args.chapter:
        where = {"chapter": args.chapter}
    elif args.page:
        where = {"page_number": args.page}
    else:
        where = None

    query_embedding = embed([args.query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where=where,
    )

    print(f"\n=== Results for: '{args.query}' ===")
    for i, (doc, meta, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        score = 1 - distance
        print(f"\n--- Result {i+1} | chapter: {meta['chapter']} | page {meta['page_number']} | score {score:.3f} ---")
        print(doc[:400])
