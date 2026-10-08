import os
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


def get_embedding(text: str) -> np.ndarray:
    """Generates vector embedding for a given text snippet using google-genai."""
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
    )
    # Convert list of floats to a float32 numpy array for FAISS
    embedding = np.array(response.embeddings[0].values, dtype=np.float32)
    return embedding


def build_faiss_index(chunks: list[str]) -> tuple[faiss.IndexFlatL2, np.ndarray]:
    """Embeds all chunks in a single batch call and builds a FAISS L2 vector index."""
    # Efficient batch embedding call
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=chunks,
    )
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

    # 2. Search relevant chunks for the current question
    relevant_chunks = retrieve_relevant_chunks(question, index, chunks, top_k=3)
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

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )
    return response.text