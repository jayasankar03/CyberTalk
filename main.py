
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import httpx

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
    stakeholder_1: str = Field(min_length=2, max_length=100)
    stakeholder_2: str = Field(min_length=2, max_length=100)
    rounds: int = Field(default=2, ge=1, le=5)

    @field_validator("stakeholder_1", "stakeholder_2")
    @classmethod
    def validate_stakeholder_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Stakeholder names must contain at least 2 characters."
            )

        return value


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


async def generate_persona_response(
    stakeholder_name: str,
    topic: str,
    transcript: list,
    closing: bool = False,
) -> str:
    history = "\n".join(
        f"Turn {item['turn']} - {item['speaker']}: "
        f"{item['message']}"
        for item in transcript
    )

    if not history:
        history = "No previous discussion."

    system_prompt = (
        f"You are {stakeholder_name}, participating in a professional "
        "cybersecurity stakeholder discussion. "
        f"Represent the perspective of {stakeholder_name} based on "
        "the role or responsibilities implied by that title. "
        "Explain your reasoning clearly, consider the other "
        "stakeholder's concerns, and seek a practical, safe, "
        "and implementable agreement. "
        "Do not impersonate the other stakeholder. "
        "Do not claim that agreement exists unless the discussion "
        "supports it."
    )

    closing_instruction = ""
    if closing:
        closing_instruction = (
            "\nThis is your final closing statement. Clearly state "
            "the decision or action plan you can support, including "
            "what both stakeholders have agreed on if the discussion "
            "supports it. If important disagreements remain, state "
            "them honestly and identify a practical next step. "
            "Do not invent mutual agreement."
        )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": (
                f"Cybersecurity discussion topic: {topic}\n\n"
                f"Discussion so far:\n{history}\n\n"
                "Provide your next contribution as your assigned "
                "stakeholder. Address the topic directly, explain "
                "your reasoning, and respond to the other "
                "stakeholder's points when available. "
                "Keep your response concise and practical. "
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
            stakeholder_name="Cybersecurity Assistant",
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
    stakeholder_1 = request.stakeholder_1.strip()
    stakeholder_2 = request.stakeholder_2.strip()

    if stakeholder_1.casefold() == stakeholder_2.casefold():
        raise HTTPException(
            status_code=400,
            detail="Please provide two different stakeholders.",
        )

    stakeholder_order = [stakeholder_1, stakeholder_2]
    transcript = []

    try:
        # Generate the regular discussion rounds.
        for turn in range(1, request.rounds + 1):
            for stakeholder_name in stakeholder_order:
                reply = await generate_persona_response(
                    stakeholder_name=stakeholder_name,
                    topic=request.topic,
                    transcript=transcript,
                )

                transcript.append({
                    "turn": turn,
                    "speaker": stakeholder_name,
                    "message": reply,
                })

        # Give both stakeholders an explicit closing statement.
        closing_turn = request.rounds + 1

        for stakeholder_name in stakeholder_order:
            reply = await generate_persona_response(
                stakeholder_name=stakeholder_name,
                topic=request.topic,
                transcript=transcript,
                closing=True,
            )

            transcript.append({
                "turn": closing_turn,
                "speaker": stakeholder_name,
                "message": reply,
            })

        # Evaluate the completed dialogue.
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
                    "name": stakeholder_name,
                }
                for stakeholder_name in stakeholder_order
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
