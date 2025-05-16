# PDF and AI qna

PDFAI is an AI-powered PDF assistant that enables users to upload PDF files, extract their content, and ask questions related to the documents. It utilizes Google’s **Gemini API** to provide intelligent answers based on document content, using a manual **chunking strategy (max 300 words)** — all without requiring a vector database.

## Features

- **AI-Powered Q&A** — Ask natural questions about your uploaded PDF.
- **PDF Text Extraction** — Extracts full text using PyMuPDF.
- **300-Word Chunking** — Efficiently splits long documents into 300-word chunks.
- **No Vector DB Needed** — Purely prompt-based logic to simplify architecture.
- **React Frontend** — Built with Vite and React for fast, interactive UI.
- **FastAPI Backend** — Handles file storage, text processing, and Gemini API calls.


## Tech Stack
### Frontend
- React.js
- Vite
- CSS

### Backend
- FastAPI
- PyMuPDF (fitz)
- Google Gemini API


## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Parth050812/PDFAI.git
cd PDFAI
```
### 2. Frontend setup (Vite + React)
frontend is made usinf react vite so as you enter the frontend folder download the dependencies and 
start the frontend at [http://localhost:5173/](http://localhost:5173/)
```bash
cd frontend
npm install
npm run dev
```
### 2. Backend setup (FastAPI)
backend is made using fastapi so download the dependencies first 
```bash
cd backend
pip install -r requirements.txt
```
after installation of requirement you need to create a **.env** file for storing the Google Gemini key <br>
get your free api key from aistudio google [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)<br>
Create a .env file with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
Now start your backend server 
```bash
uvicorn main:app --reload
```
Have used sqlite for database things just stores the title , datetime of upload and extracted content in the database of the pdf
## API Endpoints (FastAPI)
<table border="0" >
  <tr>
    <th width="200px">Method</th>
    <th width="200px">Endpoint</th>
    <th width="500px">Discription</th>
  </tr>
  <tr>
    <td align="center">POST</td>
    <td align="center">/upload</td>
    <td>Saves the uploaded PDF file, extracts its text, and stores it in the database.</td>
  </tr>
  <tr>
    <td align="center">GET</td>
    <td align="center">/pdfs</td>
    <td>Returns the list of stored PDF filenames.</td>
  </tr>
  <tr>
    <td align="center">POST</td>
    <td align="center">/ask</td>
    <td>Returns an AI-generated answer to the question by referencing the selected PDF's text.</td>
  </tr>
</table>


## Application Architecture Overview
### diagram of Workflow
![new HLD(1)](https://github.com/user-attachments/assets/bcca2a45-f2a2-4dc9-8c17-71aaaacb34ef)

### 1. Frontend (React + Vite)<br>
  Responsibilities:
  - Allows users to upload PDF files.
  - Displays a dropdown to select a file.
  - Provides a chat-style interface to ask questions and view AI responses.
  - Handles loading states and smooth user interaction.
### 1. AI Backend (FastAPI + Gemini API)<br>
  Responsibilities:
  - Receives PDF files and extracts text using PyMuPDF.
  - Stores extracted text in a SQLite database.
  - Uses Google Gemini Pro API for Q&A on the extracted content.
  - Splits large texts into manageable 300-word chunks for efficient processing.

### 3. Communication Flow
  - User uploads a PDF via the frontend (/upload endpoint).
  - Backend extracts text and stores it in the database.
  - User selects a file and asks a question.
  - Frontend sends the question and filename to the /ask endpoint.
  - Backend searches the stored content, chunks it, and queries Gemini Pro for an answer.
  - AI-generated answer is returned to the frontend and displayed.

### Tree of Project

``` bash
.
├── frontend
│   ├── eslint.config.js
│   ├── node_modules  (frontend modules)
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── public
│   │   ├── ai.ico
│   │   ├── head.png
│   │   └── vite.svg
│   ├── README.md
│   ├── src
│   │   ├── App.css
│   │   ├── App.jsx   (contains the Nav.jsx and Container.jsx component)
│   │   ├── assets
│   │   │   └── react.svg
│   │   ├── Container.css
│   │   ├── Container.jsx   (the message and ai response file)
│   │   ├── index.css
│   │   ├── main.jsx
│   │   ├── Nav.css
│   │   └── Nav.jsx     (the header file where we upload the file and select which file to have a qna)
│   └── vite.config.js
└── backend
    ├── database.py  (database connectivity and value insertion)
    ├── extract.py  (pdf extraction)
    ├── main.py   (fastapi endpoints)
    ├── pdfs.db    (database file)
    ├── __pycache__
    │   ├── database.cpython-312.pyc
    │   ├── extract.cpython-312.pyc
    │   ├── main.cpython-312.pyc
    │   └── qna.cpython-312.pyc
    ├── qna.py   (the ai qna generator file)
    ├── requirements.txt (requirements of the backend)
    └── tmp
        └── uploads
            └── deadlock.pdf (demo pdf)

9 directories, 29 files
```

## Acknowledgments

  - Google Gemini API for LLM power
  - PyMuPDF for efficient PDF parsing
  - FastAPI for modern backend magic
  - Vite + React for frontend awesomeness

















