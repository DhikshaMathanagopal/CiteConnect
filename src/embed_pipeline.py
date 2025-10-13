# src/embed_pipeline.py
import json
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
import numpy as np
from dotenv import load_dotenv

# --- load environment + client ---
load_dotenv()
client = OpenAI()

# --- paths ---
PROCESSED_PATH = sorted(Path("data/processed").glob("*_processed.json"))[-1]
OUTPUT_PATH = Path("data/embeddings")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

print(f"📂 Using processed file: {PROCESSED_PATH.name}")

# --- helper: split abstracts into chunks ---
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # number of characters per chunk
    chunk_overlap=50,     # slight overlap to preserve context
)

def embed_text(text):
    """Return embedding vector for a given text chunk."""
    resp = client.embeddings.create(
        model="text-embedding-3-small",  # or 'text-embedding-3-large'
        input=text
    )
    return resp.data[0].embedding

def main():
    papers = json.load(open(PROCESSED_PATH))
    all_chunks = []
    for paper in papers:
        abstract = paper.get("abstract", "")
        chunks = splitter.split_text(abstract)
        for i, chunk in enumerate(chunks):
            emb = embed_text(chunk)
            all_chunks.append({
                "paperId": paper.get("paperId"),
                "title": paper.get("title"),
                "year": paper.get("year"),
                "chunk_id": i,
                "chunk_text": chunk,
                "embedding": emb,
                "topic_label": paper.get("topic_label")
            })

    # save to JSON
    out_file = OUTPUT_PATH / f"{PROCESSED_PATH.stem}_embedded.json"
    json.dump(all_chunks, open(out_file, "w"), indent=2)
    print(f"✅ Saved {len(all_chunks)} embedded chunks → {out_file}")

if __name__ == "__main__":
    main()
