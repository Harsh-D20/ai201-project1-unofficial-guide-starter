import os

import chromadb
from sentence_transformers import SentenceTransformer

from chunker import chunk_document

DOCS_DIR = "documents"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "dining_guide"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def _parse_url(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("URL_SOURCE:"):
            return line.split("URL_SOURCE:", 1)[1].strip()
    return ""


def build_index(docs_dir: str = DOCS_DIR, chroma_dir: str = CHROMA_DIR) -> chromadb.Collection:
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=chroma_dir)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunks: list[dict] = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(docs_dir, filename)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        url = _parse_url(text)
        for chunk in chunk_document(text, source=filename):
            chunk["url"] = url
            all_chunks.append(chunk)

    texts = [c["text"] for c in all_chunks]
    ids = [f"chunk_{i}" for i in range(len(all_chunks))]

    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"source": c["source"], "url": c["url"]} for c in all_chunks],
    )

    print(f"Indexed {len(all_chunks)} chunks from {docs_dir}/ into {chroma_dir}/")
    return collection


def get_collection(chroma_dir: str = CHROMA_DIR) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=chroma_dir)
    return client.get_collection(COLLECTION_NAME)


if __name__ == "__main__":
    build_index()
