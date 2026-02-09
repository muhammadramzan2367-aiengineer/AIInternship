from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client
client = Groq(api_key=GROQ_API_KEY)

# Request model
class PromptRequest(BaseModel):
    prompt: str

# Physics system prompt with structured formatting
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
        # Ask the model
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PHYSICS_SYSTEM_PROMPT},
                {"role": "user", "content": data.prompt}
            ],
            temperature=0.7
        )

        answer = response.choices[0].message.content.strip()
        
        # Check if it's physics or not
        if answer == "NOT_PHYSICS":
            return {"response": "❌ I can only answer Physics questions."}
        
        return {"response": answer}

    except Exception as e:
        print("Chat error:", e)
        return {"response": "⚠️ An error occurred while processing your request."}

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
            temperature=0.5
        )

        answer = response.choices[0].message.content.strip()

        if answer == "NOT_MEDICAL":
            return {"response": "❌ Medical questions only."}

        return {"response": answer}

    except Exception as e:
        print("Medical Chat error:", e)
        return {"response": "⚠️ Medical service unavailable."}
