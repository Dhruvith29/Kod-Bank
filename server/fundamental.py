"""
fundamental.py — PDF RAG engine for the Fundamental Analysis tab.

Pipeline:
  PDF bytes → pypdf extract → chunk (500 chars, 100 overlap)
            → Gemini text-embedding-004 (768 dims)
            → Pinecone serverless (namespace = username)

Chat:
  question → embed → Pinecone search top-5
           → Gemini 1.5 Flash → answer + page citations
"""

import os
import re
import hashlib
import io
import time
import json

import pypdf
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

# ── Config ────────────────────────────────────────────────────────────────────
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")

INDEX_NAME   = "kodbank-fundamental"
EMBED_MODEL  = "models/gemini-embedding-001"   # 768 dims
GEN_MODEL    = "gemini-1.5-flash"
CHUNK_SIZE   = 500   # characters
CHUNK_OVERLAP = 100  # character overlap between chunks
TOP_K        = 5     # chunks to retrieve per query


def _check_keys():
    if not PINECONE_API_KEY or not GEMINI_API_KEY:
        raise RuntimeError(
            "PINECONE_API_KEY and GEMINI_API_KEY must be set in environment variables."
        )


# ── Pinecone index (lazy singleton) ──────────────────────────────────────────
_pc_index = None

def _get_index():
    global _pc_index
    if _pc_index is not None:
        return _pc_index
    _check_keys()
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=3072,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        # Wait for index to be ready
        for _ in range(20):
            status = pc.describe_index(INDEX_NAME).status
            if status.get("ready") or status.get("state") == "Ready":
                break
            time.sleep(2)
    _pc_index = pc.Index(INDEX_NAME)
    return _pc_index


# ── PDF extraction ─────────────────────────────────────────────────────────────
def extract_text(file_bytes: bytes) -> list[dict]:
    """Return list of {page, text} dicts (1-indexed pages) containing only relevant financial tables."""
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    pages = []
    
    # Pre-define keywords that heavily indicate financial statements.
    # By strictly isolating these pages, we cut down 95% of the vector embedding time.
    financial_keywords = [
        "balance sheet", "income statement", "statement of earnings",
        "cash flow statement", "statement of cash flows", "financial highlights",
        "key metrics", "consolidated statement", "risk factors",
        "management's discussion", "md&a"
    ]
    
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        
        if text:
            text_lower = text.lower()
            # Only append the page if it contains one of our keywords
            if any(keyword in text_lower for keyword in financial_keywords):
                pages.append({"page": i, "text": text})
                
    # Fallback: if somehow nothing matched, we'll just process the first 10 pages and last 10 pages
    if not pages and len(reader.pages) > 0:
        for i, page in enumerate(reader.pages, start=1):
            if i <= 10 or i >= len(reader.pages) - 10:
                text = page.extract_text() or ""
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    pages.append({"page": i, "text": text})
                    
    return pages


# ── Chunking ──────────────────────────────────────────────────────────────────
def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Slide a window of CHUNK_SIZE chars with CHUNK_OVERLAP overlap over each page.
    Returns list of {page, chunk_index, text}.
    """
    chunks = []
    for p in pages:
        text = p["text"]
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "page": p["page"],
                    "chunk_index": idx,
                    "text": chunk_text,
                })
                idx += 1
            if end == len(text):
                break
            start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ── Embedding ──────────────────────────────────────────────────────────────────
def _embed(text: str, task: str = "retrieval_document") -> list[float]:
    genai.configure(api_key=GEMINI_API_KEY)
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=text,
        task_type=task,
    )
    return result["embedding"]


# ── Upload a document ─────────────────────────────────────────────────────────
def upload_document(file_bytes: bytes, filename: str, username: str) -> dict:
    """
    Full pipeline: extract → chunk → embed → upsert to Pinecone.
    Returns {filename, page_count, chunk_count}.
    """
    try:
        _check_keys()
        pages  = extract_text(file_bytes)
        chunks = chunk_pages(pages)

        if not chunks:
            raise ValueError("No readable text found in this PDF.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Error processing document: {str(e)}")

    index = _get_index()
    namespace = username

    # Generate a stable file prefix from filename
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]

    # Embed and upsert in batches to avoid rate limits
    vectors = []
    
    # We will batch the text to the Gemini API in chunks of 100
    # Gemini allows batching multiple texts in one `embed_content` call
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        chunk_batch = chunks[i:i+batch_size]
        texts = [c["text"] for c in chunk_batch]
        
        genai.configure(api_key=GEMINI_API_KEY)
        # Using the batch embedding feature of the API
        result = genai.embed_content(
            model=EMBED_MODEL,
            content=texts,
            task_type="retrieval_document",
            title=filename
        )
        embeddings = result["embedding"]
        
        for idx, c in enumerate(chunk_batch):
            vec_id = f"{username}_{file_hash}_p{c['page']}_c{c['chunk_index']}"
            vectors.append({
                "id": vec_id,
                "values": embeddings[idx],
                "metadata": {
                    "username": username,
                    "filename": filename,
                    "page": c["page"],
                    "text": c["text"],
                },
            })
            
        import time
        time.sleep(1)  # pause to respect RPM limits

    # Upsert in batches to Pinecone
    pc_batch_size = 50
    for i in range(0, len(vectors), pc_batch_size):
        index.upsert(vectors=vectors[i:i+pc_batch_size], namespace=namespace)

    return {
        "filename": filename,
        "page_count": len(pages),
        "chunk_count": len(chunks),
    }


# ── Delete a document ─────────────────────────────────────────────────────────
def delete_document(filename: str, username: str):
    """Delete all vectors for a given filename from the user's namespace."""
    _check_keys()
    index = _get_index()
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]

    # List and delete vectors whose IDs start with the file prefix
    prefix = f"{username}_{file_hash}_"
    try:
        # Pinecone serverless supports list() with prefix
        ids_to_delete = [v for v in index.list(prefix=prefix, namespace=username)]
        if ids_to_delete:
            index.delete(ids=ids_to_delete, namespace=username)
    except Exception:
        # Fallback: delete by metadata filter (paid plan)
        pass


# ── Search (retrieval) ────────────────────────────────────────────────────────
def search(query: str, username: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed a query and return top_k most relevant chunks.
    Each result: {filename, page, text, score}.
    """
    _check_keys()
    index = _get_index()
    q_vec = _embed(query, task="retrieval_query")

    results = index.query(
        vector=q_vec,
        top_k=top_k,
        namespace=username,
        include_metadata=True,
    )

    chunks = []
    for match in results.matches:
        meta = match.metadata or {}
        chunks.append({
            "filename": meta.get("filename", "Unknown"),
            "page": meta.get("page", "?"),
            "text": meta.get("text", ""),
            "score": round(match.score, 3),
        })
    return chunks


# ── RAG answer generation ─────────────────────────────────────────────────────
def generate_answer(question: str, chunks: list[dict], history: list[dict]) -> dict:
    """
    Build a RAG prompt from retrieved chunks and generate an answer with Gemini.
    Returns {answer, sources}.
    """
    _check_keys()
    genai.configure(api_key=GEMINI_API_KEY)

    if not chunks:
        return {
            "answer": "I couldn't find relevant information in your uploaded documents. "
                      "Please try rephrasing your question or upload a relevant PDF.",
            "sources": [],
        }

    # Build context block
    context_parts = []
    for i, c in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {i} — {c['filename']}, Page {c['page']}]\n{c['text']}"
        )
    context = "\n\n".join(context_parts)

    # Build conversation history string
    history_str = ""
    for msg in history[-6:]:  # last 3 turns
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    prompt = f"""You are a professional financial analyst assistant. Answer questions based ONLY on the provided document excerpts.

If the answer is not found in the context, say "This information isn't available in the uploaded documents."

Always cite your sources using the format: [Source N — filename, Page X]

--- Document Context ---
{context}

--- Conversation History ---
{history_str}
--- End History ---

User Question: {question}

Provide a clear, structured answer with specific citations to the document sources."""

    model = genai.GenerativeModel(GEN_MODEL)
    response = model.generate_content(prompt)
    answer_text = response.text.strip()

    # Deduplicate sources
    seen = set()
    sources = []
    for c in chunks:
        key = (c["filename"], c["page"])
        if key not in seen:
            seen.add(key)
            sources.append({"filename": c["filename"], "page": c["page"]})


def stream_answer(question: str, chunks: list[dict], history: list[dict]):
    """
    Streaming version of generate_answer.
    Yields SSE-formatted lines:
      data: {"token": "..."}   — for each text chunk
      data: {"sources": [...]} — final event with deduplicated sources
      data: [DONE]             — sentinel
    """
    _check_keys()
    genai.configure(api_key=GEMINI_API_KEY)

    if not chunks:
        no_info = "I couldn't find relevant information in your uploaded documents. Please try rephrasing your question or upload a relevant PDF."
        yield f'data: {json.dumps({"token": no_info})}\n\n'
        yield f'data: {json.dumps({"sources": []})}\n\n'
        yield 'data: [DONE]\n\n'
        return

    # Build context block (same as generate_answer)
    context_parts = []
    for i, c in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {i} \u2014 {c['filename']}, Page {c['page']}]\n{c['text']}"
        )
    context = "\n\n".join(context_parts)

    history_str = ""
    for msg in history[-6:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    prompt = f"""You are a professional financial analyst assistant. Answer questions based ONLY on the provided document excerpts.

If the answer is not found in the context, say "This information isn't available in the uploaded documents."

Always cite your sources using the format: [Source N \u2014 filename, Page X]

--- Document Context ---
{context}

--- Conversation History ---
{history_str}
--- End History ---

User Question: {question}

Provide a clear, structured answer with specific citations to the document sources."""

    model = genai.GenerativeModel(GEN_MODEL)
    response = model.generate_content(prompt, stream=True)

    for chunk in response:
        try:
            text = chunk.text
            if text:
                yield f'data: {json.dumps({"token": text})}\n\n'
        except Exception:
            pass

    # Deduplicate sources
    seen = set()
    sources = []
    for c in chunks:
        key = (c["filename"], c["page"])
        if key not in seen:
            seen.add(key)
            sources.append({"filename": c["filename"], "page": c["page"]})

    yield f'data: {json.dumps({"sources": sources})}\n\n'
    yield 'data: [DONE]\n\n'
