from sentence_transformers import SentenceTransformer

from embedding import EMBEDDING_MODEL, get_collection

TOP_K = 10

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Return the top_k most relevant chunks for the query.

    Each result is a dict with:
        text    — chunk text
        source  — source filename
        score   — cosine distance (lower = more similar)
    """
    embedding = _get_model().encode(query).tolist()
    collection = get_collection()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": text,
            "source": metadata["source"],
            "url": metadata.get("url", ""),
            "score": distance,
        })

    return chunks


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How much does a meal plan cost?"
    print(f"Query: {query}\n")
    for i, chunk in enumerate(retrieve(query), 1):
        print(f"[{i}] source: {chunk['source']}  score: {chunk['score']:.4f}")
        print(chunk["text"])
        print()
