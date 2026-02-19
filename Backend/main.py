from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
import shutil
from dotenv import load_dotenv
import traceback

from rag import RAGPipeline   # ← your updated rag.py

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

UPLOAD_FOLDER = "documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize RAG once at startup
rag = RAGPipeline()

# ────────────────────────────────────────────────
# FastAPI app
# ────────────────────────────────────────────────
app = FastAPI(title="Physics + Medical + RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────
# MODELS
# ────────────────────────────────────────────────
class PromptRequest(BaseModel):
    prompt: str

class QuestionRequest(BaseModel):
    question: str


# ────────────────────────────────────────────────
# PHYSICS CHAT (unchanged)
# ────────────────────────────────────────────────
PHYSICS_SYSTEM_PROMPT = """You are a Physics AI assistant with deep knowledge of physical sciences.
Only respond if the question is related to physics, mechanics, thermodynamics, waves, or related topics.
If the question is NOT physics, respond exactly with: NOT_PHYSICS

Answer in a structured way:
1. Start with a **brief explanation**.
2. Use **bullet points or numbered lists** for clarity.
3. Include **formulas** where relevant.
4. Add **examples** to illustrate concepts.
5. Organize with **headings** for complex topics.

Always make the answer easy to understand for students."""

@app.post("/chat")
def physics_chat(data: PromptRequest):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PHYSICS_SYSTEM_PROMPT},
                {"role": "user", "content": data.prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        answer = response.choices[0].message.content.strip()

        if answer == "NOT_PHYSICS":
            return {"response": "❌ I can only answer Physics questions."}

        return {"response": answer}

    except Exception as e:
        traceback.print_exc()
        return {"response": f"⚠️ {str(e)}"}


# ────────────────────────────────────────────────
# MEDICAL CHAT (unchanged)
# ────────────────────────────────────────────────
MEDICAL_SYSTEM_PROMPT = """You are a Medical AI assistant with expertise in healthcare and medical sciences.

Only respond if the user's question is related to medicine, health, or medical topics.

If the question is NOT medical, respond exactly with:
NOT_MEDICAL

Do NOT provide a final diagnosis.
Do NOT prescribe medications or treatments.
Always recommend consulting a qualified doctor or healthcare professional.

Guidelines for medical responses:
- Be accurate and medically appropriate.
- Explain concepts clearly in simple, patient-friendly language.
- Use bullet points or numbered lists when helpful.
- Mention possible causes or contributing factors where relevant.
- Include general safety or preventive advice only.
- Structure the answer with clear headings and organized sections.
"""

@app.post("/medical")
def medical_chat(data: PromptRequest):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                {"role": "user", "content": data.prompt}
            ],
            temperature=0.5,
            max_tokens=900,
        )

        answer = response.choices[0].message.content.strip()

        if answer == "NOT_MEDICAL":
            return {"response": "❌ Medical questions only."}

        return {"response": answer}

    except Exception as e:
        print("Medical Chat error:", e)
        return {"response": "⚠️ Medical service unavailable."}


# ────────────────────────────────────────────────
# RAG ENDPOINTS
# ────────────────────────────────────────────────

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file → saved to documents/ folder
    You still need to call /build-index to process it
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, detail="Only PDF files are allowed")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": "File uploaded successfully", "filename": file.filename}
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to save file: {str(e)}")


@app.post("/build-index")
def build_index():
    """
    Process all PDFs in documents/ folder → chunk → embed → store in Chroma
    """
    try:
        added = rag.build_or_update_index()
        if added == 0:
            return {"message": "No new PDFs found or no new chunks added", "added_chunks": 0}
        return {"message": "Index updated successfully", "added_chunks": added}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=f"Index build failed: {str(e)}")


@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    RAG query: retrieve relevant chunks → pass to LLM → return answer + context
    """
    if not request.question.strip():
        raise HTTPException(400, detail="Question cannot be empty")

    try:
        # ─── Step 1: Check if vector store is ready ───
        if not rag.is_ready():
            return {
                "answer": "Vector database is not initialized or empty.",
                "contexts": [],
                "sources": [],
                "debug": {"error": "Vector store not ready"}
            }

        # ─── Step 2: Retrieve with scores ───
        results = rag.retrieve(request.question, k=8)  # increased to 8 for better coverage

        # Debug: print retrieval information to terminal
        print("\n" + "="*60)
        print(f"QUERY: {request.question}")
        print(f"Retrieved {len(results)} chunks")

        if results:
            print("Top results (score - lower is better):")
            for i, r in enumerate(results[:3], 1):  # show top 3
                print(f"  {i}. score={r['score']:.4f} | {r['source']} | {r['content'][:80]}...")
        else:
            print("→ No chunks retrieved")

        collection_size = rag.vectorstore._collection.count() if rag.vectorstore else 0
        print(f"Collection total documents: {collection_size}")
        print("="*60 + "\n")

        # ─── Step 3: Handle no results case ───
        if not results:
            return {
                "answer": "I couldn't find any relevant information in the uploaded documents.",
                "contexts": [],
                "sources": [],
                "scores": [],
                "debug": {
                    "retrieved_count": 0,
                    "collection_size": collection_size,
                    "message": "No chunks matched the query (possible causes: low similarity, empty index, embedding mismatch)"
                }
            }

        # Optional: filter out very low-relevance chunks (tune threshold)
        MIN_SCORE_THRESHOLD = 0.65  # cosine distance – adjust between 0.5–0.75
        filtered_results = [r for r in results if r["score"] <= MIN_SCORE_THRESHOLD]

        if not filtered_results and results:
            print("All retrieved chunks below relevance threshold — using top 2 anyway")
            filtered_results = results[:2]  # fallback

        # Use filtered or original results
        final_results = filtered_results or results

        # ─── Step 4: Format context ───
        formatted_context = "\n\n".join(
            f"[{i+1}] Source: {r['source']} (score: {r['score']:.4f})\n{r['content'].strip()}"
            for i, r in enumerate(final_results)
        )

        # ─── Step 5: Stronger, more grounded prompt ───
        rag_prompt = f"""You are a precise document Q&A assistant.
Answer using **only** the provided context excerpts.
Do NOT use outside knowledge.
If the answer is not clearly supported by the context, respond exactly with:
"Information not found in the provided documents."

Context (with source and relevance score):
{formatted_context}

Question: {request.question}

Answer concisely, clearly, and directly:"""

        # ─── Step 6: Call LLM ───
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": rag_prompt}],
            temperature=0.2,           # lower = more deterministic
            max_tokens=900,
            top_p=0.9,
        )

        answer_text = response.choices[0].message.content.strip()

        # ─── Step 7: Return structured response ───
        return {
            "answer": answer_text,
            "contexts": [r["content"] for r in final_results],
            "sources": [r["source"] for r in final_results],
            "scores": [r["score"] for r in final_results],
            "debug": {
                "retrieved_count": len(results),
                "filtered_count": len(final_results),
                "collection_size": collection_size,
                "used_threshold": MIN_SCORE_THRESHOLD if filtered_results != results else None
            }
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error during RAG query: {str(e)}"
        )


@app.get("/status")
def get_status():
    return {
        "rag_ready": rag.is_ready(),
        "upload_folder": UPLOAD_FOLDER,
        "chunks_log": rag.get_chunks_log_path(),
        "documents_count": len([f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".pdf")])
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )