# main.py
import os
import shutil
import traceback
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

from rag import RAGPipeline, UPLOAD_FOLDER

load_dotenv()

app = FastAPI(title="Physics + Medical + PDF RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

rag = RAGPipeline()


# ─── Models ────────────────────────────────────────────────────────────────

class PromptRequest(BaseModel):
    prompt: str


class QuestionRequest(BaseModel):
    question: str


class RAGResponse(BaseModel):
    answer: str
    context_used: List[str]


# ─── Physics ───────────────────────────────────────────────────────────────

PHYSICS_SYSTEM_PROMPT = """You are a Physics AI assistant with deep knowledge of physical sciences.
Only respond if the question is related to physics, mechanics, thermodynamics, waves, optics, electricity, modern physics, or related topics.
If the question is NOT physics-related, respond exactly with: NOT_PHYSICS

Answer in a structured, student-friendly way:
1. **Brief explanation**
2. Use **bullet points** or **numbered lists**
3. Include **relevant formulas** (use LaTeX if possible)
4. Add **simple examples**
5. Use **headings** for multi-part questions"""

@app.post("/chat/physics")
def physics_chat(data: PromptRequest):
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PHYSICS_SYSTEM_PROMPT},
                {"role": "user", "content": data.prompt}
            ],
            temperature=0.65,
            max_tokens=680
        )
        answer = resp.choices[0].message.content.strip()

        if answer == "NOT_PHYSICS":
            return {"response": "❌ This endpoint only answers Physics questions."}

        return {"response": answer}

    except Exception as e:
        traceback.print_exc()
        return {"response": f"⚠️ Error: {str(e)}"}


# ─── Medical ───────────────────────────────────────────────────────────────

MEDICAL_SYSTEM_PROMPT = """You are a helpful Medical AI assistant.
Only respond if the question is related to medicine, health, diseases, anatomy, physiology, or medical concepts.

If the question is NOT medical, respond exactly with: NOT_MEDICAL

Rules:
- NEVER give a final diagnosis
- NEVER prescribe medication or treatment
- ALWAYS recommend seeing a qualified doctor
- Use clear, simple language
- Structure answers with headings and bullet points when helpful"""

@app.post("/chat/medical")
def medical_chat(data: PromptRequest):
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                {"role": "user", "content": data.prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )
        answer = resp.choices[0].message.content.strip()

        if answer == "NOT_MEDICAL":
            return {"response": "❌ Medical & health questions only."}

        return {"response": answer}

    except Exception as e:
        print("Medical error:", e)
        return {"response": "⚠️ Service temporarily unavailable."}


# ─── RAG Endpoints ─────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, detail="Only PDF files allowed")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": f"File uploaded: {file.filename}"}
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to save file: {str(e)}")


@app.post("/build")
def build_rag_index():
    try:
        count = rag.build_or_update_index()
        if count == 0:
            return {"message": "No PDFs found or no content extracted"}
        return {"message": f"Vector index (re)built — {count} chunks"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=f"Build failed: {str(e)}")

@app.post("/ask", response_model=RAGResponse)
async def ask_rag_question(req: QuestionRequest):
    """
    Ask a question using RAG (retrieval-augmented generation).
    
    Required JSON body format:
    {
      "question": "Your question here"
    }
    """
    # ────────────────────────────────────────────────────────────────
    # Debug logging – helps identify frontend payload problems
    print(f"[ASK] Received request → question length: {len(req.question or '')}")
    print(f"[ASK] Full validated model: {req.dict()}")
    # ────────────────────────────────────────────────────────────────

    # Early rejection for obviously invalid input
    if not req.question or not isinstance(req.question, str):
        raise HTTPException(
            status_code=422,
            detail="Field 'question' is required and must be a non-empty string"
        )

    question = req.question.strip()
    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty after trimming whitespace"
        )

    if len(question) > 2000:  # reasonable upper limit
        raise HTTPException(
            status_code=422,
            detail="Question is too long (max 2000 characters)"
        )

    try:
        # Check if vector database is ready
        if not rag.is_ready():
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail="Vector index is not yet built. Please upload PDFs and call /build endpoint first."
            )

        # Retrieve relevant chunks
        chunks = rag.retrieve(question, k=4)

        if not chunks or all(not c.strip() for c in chunks):
            return RAGResponse(
                answer="Sorry, I couldn't find any relevant information in the uploaded documents.",
                context_used=[]
            )

        # Format context nicely
        context_lines = []
        for i, chunk in enumerate(chunks, 1):
            cleaned = chunk.strip()
            if cleaned:
                context_lines.append(f"[Excerpt {i}]\n{cleaned}")
        context = "\n\n".join(context_lines)

        # Structured, strict prompt
        prompt = f"""You are a precise and helpful assistant.
Answer the question using **only** the provided context excerpts.
Do NOT use any external knowledge.
If the context does not contain sufficient information to answer accurately, 
clearly state that you don't have enough information.

Context excerpts:
{context}

Question: {question}

Answer concisely, naturally and directly:"""

        # Call Groq model
        llm_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=650,
            top_p=0.92,
            presence_penalty=0.1,
            frequency_penalty=0.0,
        )

        answer_text = llm_response.choices[0].message.content.strip()

        return RAGResponse(
            answer=answer_text,
            context_used=chunks
        )

    except RuntimeError as runtime_err:
        # Usually related to vector store / retrieval failures
        raise HTTPException(
            status_code=400,
            detail=f"Retrieval system error: {str(runtime_err)}"
        )

    except Exception as general_err:
        traceback.print_exc()
        error_str = str(general_err).lower()

        if "422" in error_str or "validation" in error_str or "unprocessable" in error_str:
            raise HTTPException(
                status_code=422,
                detail="Invalid request format. Expected JSON: {\"question\": \"your question\"}"
            )

        if any(word in error_str for word in ["rate limit", "quota", "429"]):
            raise HTTPException(
                status_code=429,
                detail="Rate limit reached. Please try again in a few moments."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Internal error while processing your question: {str(general_err)}"
        )

@app.get("/health")
def health_check():
    pdf_files = len([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".pdf")])
    return {
        "status": "ok",
        "pdfs_uploaded": pdf_files,
        "vectorstore_ready": rag.is_ready(),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "chunks_file": rag.get_chunk_file_path()
    }


@app.get("/chunks-info")
def chunks_file_info():
    path = rag.get_chunk_file_path()
    if not os.path.exists(path):
        return {"status": "chunks_file_not_created_yet"}

    try:
        line_count = sum(1 for _ in open(path, "r", encoding="utf-8"))
        return {
            "chunks_file": path,
            "chunk_count": line_count,
            "description": "Each line is JSON with text, source_file, timestamp, etc."
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )