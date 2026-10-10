import os
import time
import json
import numpy as np
import faiss
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from database import get_pdf_content

load_dotenv()
client = genai.Client()

INDEX_DIR = "vector_stores"
os.makedirs(INDEX_DIR, exist_ok=True)

# The embedding model must stay the same for a PDF's whole life: the saved FAISS index
# only makes sense with vectors from the model that built it, so it is never switched.
EMBEDDING_MODEL = "gemini-embedding-2"

# Answer models, tried in this order. When one hits a rate limit (or is overloaded /
# unavailable) the next one is used. Override without touching code by setting
# GEMINI_MODELS in .env, e.g. GEMINI_MODELS=gemini-3.1-flash-lite,gemini-3.5-flash
GENERATION_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_MODELS", "gemini-3.1-flash-lite,gemini-3.6-flash").split(",")
    if m.strip()
]

# 429 = rate limit, 500/503/504 = server error or overloaded, 404 = model name not found
SWITCH_MODEL_CODES = {404, 429, 500, 503, 504}
# Only temporary errors are worth retrying on the same model (used for embeddings)
RETRYABLE_CODES = {429, 500, 503, 504}
EMBED_MAX_RETRIES = 3


def get_file_paths(filename: str) -> tuple[str, str]:
    """Returns persistent disk file paths for a given PDF's index and text chunks."""
    safe_name = os.path.splitext(filename)[0]
    index_path = os.path.join(INDEX_DIR, f"{safe_name}.index")
    chunks_path = os.path.join(INDEX_DIR, f"{safe_name}_chunks.json")
    return index_path, chunks_path


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Splits long text into overlapping chunks for indexing."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def embed_with_retry(contents):
    """Calls the embedding model, waiting and retrying a few times on temporary errors.

    The embedding model is not switched on failure (see EMBEDDING_MODEL), so the only
    option when it is rate limited is to wait a little and try again.
    """
    for attempt in range(EMBED_MAX_RETRIES + 1):
        try:
            return client.models.embed_content(model=EMBEDDING_MODEL, contents=contents)
        except APIError as err:
            if err.code not in RETRYABLE_CODES or attempt == EMBED_MAX_RETRIES:
                raise
            wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
            print(f"[embed] error {err.code}, retrying in {wait}s")
            time.sleep(wait)


def get_embedding(text: str) -> np.ndarray:
    """Generates vector embedding for a given text snippet using google-genai."""
    response = embed_with_retry(text)
    # Convert list of floats to a float32 numpy array for FAISS
    embedding = np.array(response.embeddings[0].values, dtype=np.float32)
    return embedding


def build_faiss_index(chunks: list[str]) -> tuple[faiss.IndexFlatL2, np.ndarray]:
    """Embeds all chunks in a single batch call and builds a FAISS L2 vector index."""
    # Efficient batch embedding call
    response = embed_with_retry(chunks)
    embeddings_matrix = np.array(
        [e.values for e in response.embeddings],
        dtype=np.float32
    )

    # Dimension of vectors
    dimension = embeddings_matrix.shape[1]

    # Initialize L2 distance index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_matrix)

    return index, embeddings_matrix


def get_or_create_vector_store(filename: str) -> tuple[faiss.IndexFlatL2, list[str]]:
    """Loads FAISS index and chunks from disk if available; builds and saves them if not."""
    index_path, chunks_path = get_file_paths(filename)

    # 1. Load from disk if previously built
    if os.path.exists(index_path) and os.path.exists(chunks_path):
        index = faiss.read_index(index_path)
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        return index, chunks

    # 2. Extract content, chunk, build index, and persist to disk
    document_text = get_pdf_content(filename)
    if not document_text or not document_text.strip():
        raise ValueError("The document is empty or could not be loaded.")

    chunks = chunk_text(document_text)
    index, _ = build_faiss_index(chunks)

    # Save index and chunks to disk
    faiss.write_index(index, index_path)
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    return index, chunks


def retrieve_relevant_chunks(
    question: str,
    index: faiss.IndexFlatL2,
    chunks: list[str],
    top_k: int = 3
) -> list[str]:
    """Embeds query and retrieves top-K most similar text chunks."""
    query_vector = get_embedding(question).reshape(1, -1)
    distances, indices = index.search(query_vector, top_k)

    retrieved = [chunks[i] for i in indices[0] if i < len(chunks)]
    return retrieved


def generate_with_fallback(prompt: str) -> str:
    """Generates an answer, automatically moving to the next model when one is
    rate limited, overloaded or unavailable. Raises the last error if all fail."""
    last_error = None
    for model in GENERATION_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text
        except APIError as err:
            if err.code in SWITCH_MODEL_CODES:
                print(f"[generate] {model} failed with {err.code}, trying next model")
                last_error = err
                continue
            raise  # e.g. 400/401/403: switching models won't fix it
    raise last_error


# qna.py

def answer_qna(
    filename: str,
    question: str,
    chat_history: list[dict[str, str]] = None
) -> str:
    # 1. Fetch persistent FAISS index and chunks
    try:
        index, chunks = get_or_create_vector_store(filename)
    except ValueError as err:
        return str(err)
    except APIError as err:
        return busy_message(err)

    # 2. Search relevant chunks for the current question
    try:
        relevant_chunks = retrieve_relevant_chunks(question, index, chunks, top_k=3)
    except APIError as err:
        return busy_message(err)
    context = "\n\n---\n\n".join(relevant_chunks)

    # 3. Format chat history into text
    formatted_history = ""
    if chat_history:
        # Keep recent 4-6 messages for context
        recent = chat_history[-6:]
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            formatted_history += f"{role}: {msg.get('content')}\n"

    # 4. Construct prompt with context AND conversation history
    prompt = f"""
You are a helpful assistant having a conversation with a user about the document context below.

Document Context:
{context}

Previous Conversation:
{formatted_history if formatted_history else "No previous conversation."}

Current User Question:
{question}

Answer the current question using the document context and conversation history. If the information is not in the context or conversation, state that you don't know.
"""

    # 5. Generate the answer, switching models automatically if one is rate limited
    try:
        return generate_with_fallback(prompt)
    except APIError as err:
        return busy_message(err)


def busy_message(err: APIError) -> str:
    """Friendly text shown in the chat when the Gemini API can't be used right now."""
    print(f"[gemini] request failed: {err.code} {err}")
    if err.code in RETRYABLE_CODES:
        return "The AI service is busy right now (rate limit reached). Please try again in a minute."
    return "Something went wrong while contacting the AI service. Please try again."