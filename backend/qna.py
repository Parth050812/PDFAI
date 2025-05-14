import os
import google.generativeai as genai
from dotenv import load_dotenv
from database import get_pdf_content

#load the .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# chuck maker make the chuck of 300 words 
def chunk_text(text, max_words=300):
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

#from the chucks which is most relevant will be chooosen and passed to generate the final answer
def extract_relevant_info(chunk, question):
    prompt = f"""
You are a helpful assistant. Based only on the following document chunk, extract any information relevant to the question. 
If the chunk doesn't contain relevant information, respond with "NONE".
DOCUMENT CHUNK:
{chunk}

QUESTION:
{question}

RELEVANT INFORMATION (or "NONE"):
"""
    try:
        response = model.generate_content(prompt)
        answer = response.text.strip()
        return None if answer.upper() == "NONE" else answer
    except Exception as e:
        print(f"[Chunk Error] {e}")
        return None

#generates the final answers
def generate_final_answer(extracted_info, question):
    prompt = f"""
You are a helpful assistant. Based on the following extracted information, provide a single, clear, and solid answer to the question.
Give a Bold Title at the beginning using the Question asked. Bold necessary important part to give depth of the importance
EXTRACTED INFORMATION:
{extracted_info}

QUESTION:
{question}

Only use the information provided above. If insufficient, acknowledge that.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Final Answer Error] {e}"

def answer_qna(filename, question):
    document_text = get_pdf_content(filename)
    if not document_text:
        return "Document not found in the database."

    chunks = chunk_text(document_text)
    relevant_info = []

    for chunk in chunks:
        info = extract_relevant_info(chunk, question)
        if info:
            relevant_info.append(info)

    if not relevant_info:
        return "No relevant information found in the document to answer this question."

    combined_info = "\n\n".join(relevant_info)
    return generate_final_answer(combined_info, question)
