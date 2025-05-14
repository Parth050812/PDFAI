from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uvicorn
from database import initialize_db, insert_pdf, get_pdf, get_pdf_content
from extract import extract_text
from qna import answer_qna

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_db()

UPLOAD_DIR = "tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

#upload api to upload the file in the above folder and store the value in the database with the databeing extracted tooo
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    extracted_text = extract_text(file_path)
    insert_pdf(file.filename, extracted_text)
    return {
        "message": "File uploaded and processed",
        "filename": file.filename
    }

#gets the pdf info
@app.get("/pdfs")
def list_pdfs():
    return get_pdf()

#the psot method of the question asked by the user to ai for the given pdf name
@app.post("/ask")
async def ask_question(data: dict):
    filename = data.get("filename")
    question = data.get("question")
    answer = answer_qna(filename, question)
    return {"answer": answer}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
