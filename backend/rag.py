"""
RAG pipeline — document ingestion, chunking, embedding, and retrieval.
Uses ChromaDB with the default all-MiniLM-L6-v2 sentence-transformer model.
"""

import io
import uuid
import chromadb
from chromadb.utils import embedding_functions

default_ef = embedding_functions.DefaultEmbeddingFunction()
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="hr_policies",
    embedding_function=default_ef,
)


def process_and_store_document(file_content: bytes, filename: str) -> tuple[bool, str]:
    """
    Extract text from a PDF or plain-text file, chunk it, and upsert
    embeddings into ChromaDB.
    Returns (success: bool, message: str).
    """
    try:
        # ── Text extraction ──────────────────────────────────────────
        text = ""
        if filename.lower().endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n\n"
        else:
            text = file_content.decode("utf-8")

        # ── Chunking ─────────────────────────────────────────────────
        raw_chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 50]
        chunks: list[str] = []
        for rc in raw_chunks:
            if len(rc) > 1000:
                words = rc.split(" ")
                for i in range(0, len(words), 150):
                    chunk = " ".join(words[i : i + 150])
                    if chunk.strip():
                        chunks.append(chunk)
            else:
                chunks.append(rc)

        if not chunks:
            return False, "No readable text extracted from document."

        # ── Store in ChromaDB ────────────────────────────────────────
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {"source": filename, "section": f"Chunk {i + 1}"}
            for i in range(len(chunks))
        ]

        collection.add(documents=chunks, metadatas=metadatas, ids=ids)
        return True, f"Successfully stored {len(chunks)} chunks from '{filename}'."

    except Exception as e:
        return False, f"Processing failed: {e}"


def search_policies(query: str, n_results: int = 5) -> list[dict]:
    """
    Similarity search against the ChromaDB collection.
    Returns list of dicts with keys: text, source, section, distance.
    """
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        if not results["documents"] or not results["documents"][0]:
            return []

        formatted = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            formatted.append(
                {
                    "text": doc,
                    "source": meta.get("source", "Unknown"),
                    "section": meta.get("section", "Unknown"),
                    "distance": dist,
                }
            )
        return formatted

    except Exception as e:
        print(f"ChromaDB query error: {e}")
        return []


def get_collection_count() -> int:
    """Return the number of documents currently stored."""
    return collection.count()
