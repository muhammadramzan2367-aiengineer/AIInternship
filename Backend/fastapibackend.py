from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# FastAPI app
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # React / Frontend access
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# Request body structure
class PromptRequest(BaseModel):
    prompt: str

# API endpoint
@app.post("/chat")
def chat_with_llama(data: PromptRequest):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": data.prompt}
        ],
        temperature=0.7
    )

    return {
        "response": response.choices[0].message.content
    }
