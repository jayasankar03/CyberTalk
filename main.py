
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="CyberTalk API")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


class ChatRequest(BaseModel):
    message: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat")
async def chat(request: ChatRequest):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": request.message
            }
        ],
        "stream": False,
        "keep_alive": "10m"
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

        return {
            "reply": result["message"]["content"],
            "model": MODEL_NAME
        }

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed ({type(exc).__name__}): {repr(exc)}"
        ) from exc
