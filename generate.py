import os

from dotenv import load_dotenv
from groq import Groq

from retrieval import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "Answer the question using only the information in the provided documents. "
    "If the documents don't contain enough information to answer, say "
    "'I don't have enough information on that.'\n\n"
    "Format your answer with in-text citations. After each claim, cite the source "
    "as a Markdown hyperlink using the format [[source]](url), like: "
    "\"Dinner costs $19.99 [[source]](https://dining.umd.edu/home/hours-locations/dining-halls/door-prices). "
    "Students living on campus must purchase a Resident Plan "
    "[[source]](https://dining.umd.edu/students/resident-plans).\"\n\n"
    "Only use information from the provided documents. Do not add facts from outside "
    "the documents."
)


def build_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        label = chunk["url"] if chunk.get("url") else chunk["source"]
        parts.append(f"[{label}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def generate(query: str, top_k: int = 5) -> str:
    chunks = retrieve(query, top_k=top_k)
    context = build_context(chunks)

    user_message = f"Documents:\n\n{context}\n\nQuestion: {query}"

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the door price for a student dinner?"
    print(f"Query: {query}\n")
    print(generate(query))
