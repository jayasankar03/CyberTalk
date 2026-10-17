
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx

from personas import PERSONAS

app = FastAPI(title="CyberTalk API")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


class ChatRequest(BaseModel):
    message: str


class DialogueRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    rounds: int = Field(default=2, ge=1, le=5)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


async def generate_persona_response(
    persona_key: str,
    topic: str,
    transcript: list
) -> str:
    persona = PERSONAS[persona_key]

    history = "\n".join(
        f"Turn {item['turn']} - {item['speaker']}: "
        f"{item['message']}"
        for item in transcript
    )

    if not history:
        history = "No previous discussion."

    messages = [
        {
            "role": "system",
            "content": persona["system_prompt"]
        },
        {
            "role": "user",
            "content": (
                f"Cybersecurity discussion topic: {topic}\n\n"
                f"Discussion so far:\n{history}\n\n"
                "Provide your next contribution as this stakeholder. "
                "Address the topic directly, explain your reasoning, "
                "and respond to the other stakeholder's points when "
                "available. Keep your response concise and practical. "
                "Do not impersonate the other stakeholder. "
                "Do not claim that an agreement has been reached "
                "unless the discussion supports that conclusion."
            )
        }
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "keep_alive": "10m"
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json=payload
        )
        response.raise_for_status()
        result = response.json()

    return result["message"]["content"].strip()


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        reply = await generate_persona_response(
            persona_key="security_officer",
            topic=request.message,
            transcript=[]
        )

        return {
            "reply": reply,
            "model": MODEL_NAME
        }

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama request failed "
                f"({type(exc).__name__}): {repr(exc)}"
            )
        ) from exc


@app.post("/dialogue")
async def dialogue(request: DialogueRequest):
    transcript = []

    stakeholder_order = [
        "security_officer",
        "it_operations_manager"
    ]

    try:
        for turn in range(1, request.rounds + 1):
            for persona_key in stakeholder_order:
                persona = PERSONAS[persona_key]

                reply = await generate_persona_response(
                    persona_key=persona_key,
                    topic=request.topic,
                    transcript=transcript
                )

                transcript.append({
                    "turn": turn,
                    "speaker": persona["name"],
                    "message": reply
                })

        return {
            "topic": request.topic,
            "rounds": request.rounds,
            "model": MODEL_NAME,
            "dialogue": transcript
        }

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama dialogue request failed "
                f"({type(exc).__name__}): {repr(exc)}"
            )
        ) from exc
