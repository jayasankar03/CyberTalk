
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx

from personas import PERSONAS
from agreement import AgreementResult
from agreement_evaluator import (
    AgreementEvaluationError,
    evaluate_agreement,
)

app = FastAPI(title="CyberTalk API")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


class ChatRequest(BaseModel):
    message: str


class DialogueRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    stakeholder_1: str
    stakeholder_2: str
    rounds: int = Field(default=2, ge=1, le=5)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/personas")
async def list_personas():
    """Return available stakeholder choices without exposing prompts."""
    return {
        "personas": [
            {
                "key": key,
                "name": persona["name"],
                "role": persona["role"],
                "goals": persona["goals"],
                "priorities": persona["priorities"],
            }
            for key, persona in PERSONAS.items()
        ]
    }


async def generate_persona_response(
    persona_key: str,
    topic: str,
    transcript: list,
    closing: bool = False,
) -> str:
    persona = PERSONAS[persona_key]

    history = "\n".join(
        f"Turn {item['turn']} - {item['speaker']}: "
        f"{item['message']}"
        for item in transcript
    )

    if not history:
        history = "No previous discussion."

    closing_instruction = ""
    if closing:
        closing_instruction = (
            "\nThis is your final closing statement. Clearly state "
            "the decision or action plan you can support, including "
            "what both stakeholders have agreed on if the discussion "
            "supports it. If important disagreements remain, state "
            "them honestly and identify a practical next step both "
            "stakeholders can take. Do not invent mutual agreement."
        )

    messages = [
        {
            "role": "system",
            "content": persona["system_prompt"],
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
                "Do not claim agreement unless the discussion supports it."
                f"{closing_instruction}"
            ),
        },
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "keep_alive": "10m",
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()

    return result["message"]["content"].strip()


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        reply = await generate_persona_response(
            persona_key="security_officer",
            topic=request.message,
            transcript=[],
        )

        return {
            "reply": reply,
            "model": MODEL_NAME,
        }

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama request failed "
                f"({type(exc).__name__}): {repr(exc)}"
            ),
        ) from exc


@app.post("/dialogue")
async def dialogue(request: DialogueRequest):
    stakeholder_order = [
        request.stakeholder_1,
        request.stakeholder_2,
    ]

    # Validate the user's selections before calling Ollama.
    for stakeholder_key in stakeholder_order:
        if stakeholder_key not in PERSONAS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown stakeholder '{stakeholder_key}'. "
                    "Use GET /personas to see available choices."
                ),
            )

    if request.stakeholder_1 == request.stakeholder_2:
        raise HTTPException(
            status_code=400,
            detail="Please select two different stakeholders.",
        )

    transcript = []

    try:
        # Generate the regular discussion rounds.
        for turn in range(1, request.rounds + 1):
            for persona_key in stakeholder_order:
                persona = PERSONAS[persona_key]

                reply = await generate_persona_response(
                    persona_key=persona_key,
                    topic=request.topic,
                    transcript=transcript,
                )

                transcript.append({
                    "turn": turn,
                    "speaker": persona["name"],
                    "message": reply,
                })

        # Add an explicit closing statement from each stakeholder.
        closing_turn = request.rounds + 1

        for persona_key in stakeholder_order:
            persona = PERSONAS[persona_key]

            reply = await generate_persona_response(
                persona_key=persona_key,
                topic=request.topic,
                transcript=transcript,
                closing=True,
            )

            transcript.append({
                "turn": closing_turn,
                "speaker": persona["name"],
                "message": reply,
            })

        # Evaluate the completed dialogue using Commit 7's evaluator.
        agreement: AgreementResult = await evaluate_agreement(
            topic=request.topic,
            transcript=transcript,
        )

        return {
            "topic": request.topic,
            "rounds": request.rounds,
            "model": MODEL_NAME,
            "stakeholders": [
                {
                    "key": key,
                    "name": PERSONAS[key]["name"],
                    "role": PERSONAS[key]["role"],
                }
                for key in stakeholder_order
            ],
            "dialogue": transcript,
            "agreement": agreement.model_dump(),
        }

    except AgreementEvaluationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agreement evaluation failed: {str(exc)}",
        ) from exc

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama dialogue request failed "
                f"({type(exc).__name__}): {repr(exc)}"
            ),
        ) from exc
