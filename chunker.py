CHUNK_SIZE = 500
OVERLAP = 50

# Separators tried in order: paragraph → line → sentence → word → character
_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    pieces = _split_recursive(text.strip(), _SEPARATORS, chunk_size)
    return _merge_with_overlap(pieces, chunk_size, overlap)


def _parse_url(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("URL_SOURCE"):
            return line.split("URL_SOURCE", 1)[1].lstrip(":=").strip()
    return ""


def chunk_document(text: str, source: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    """Return chunks as dicts with 'text', 'source', and 'url' keys."""
    url = _parse_url(text)
    return [
        {"text": chunk, "source": source, "url": url}
        for chunk in chunk_text(text, chunk_size, overlap)
    ]


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Split text into pieces that each fit within chunk_size, trying separators in order."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # Find the first separator that appears in the text
    sep = next((s for s in separators if s == "" or s in text), None)
    if sep is None:
        return [text]

    next_seps = separators[separators.index(sep) + 1:]

    parts = text.split(sep) if sep != "" else [text[i] for i in range(len(text))]
    result = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) <= chunk_size:
            result.append(part)
        else:
            result.extend(_split_recursive(part, next_seps, chunk_size))

    return result


def _merge_with_overlap(pieces: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Combine pieces into chunks up to chunk_size, carrying the last `overlap`
    characters of each finished chunk into the start of the next."""
    chunks = []
    buf = ""

    for piece in pieces:
        candidate = f"{buf} {piece}".strip() if buf else piece
        if len(candidate) <= chunk_size:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            tail = buf[-overlap:] if buf and overlap else ""
            buf = f"{tail} {piece}".strip() if tail else piece

    if buf:
        chunks.append(buf)

    return chunks


if __name__ == "__main__":
    import os

    docs_dir = "documents"
    all_chunks = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(docs_dir, filename)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        chunks = chunk_document(text, source=filename)

        print(f"{filename} ({len(text)} chars) → {len(chunks)} chunks")

        all_chunks.extend(chunks)

    print(f"\nTotal chunks: {len(all_chunks)}")

    # print 5 random chunks
    import random
    print("\nSample chunks:")
    for chunk in random.sample(all_chunks, 5):
        print(f"[source: {chunk['source']}]  [url: {chunk['url']}]")
        print(chunk["text"])
        print("---")