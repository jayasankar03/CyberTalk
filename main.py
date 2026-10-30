
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import httpx
import time
from agreement import AgreementResult
from agreement_evaluator import (
    AgreementEvaluationError,
    evaluate_agreement,
)
from qa_service import (
    OllamaResponseError,
    answer_cybersecurity_question,
)
app = FastAPI(title="CyberTalk API")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


class ChatRequest(BaseModel):
    message: str

class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Please enter a question.")

        return value
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

@app.post("/ask")
async def ask_question(request: QARequest):
    try:
        answer = await answer_cybersecurity_question(
            request.question
        )

        if not isinstance(answer, str) or not answer.strip():
            raise OllamaResponseError(
                "The QA service returned an empty answer."
            )

        return {
            "question": request.question,
            "answer": answer.strip(),
            "model": MODEL_NAME,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except OllamaResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI service returned an invalid response. "
                "Please try again."
            ),
        ) from exc

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama Q&A request failed "
                f"({type(exc).__name__}): {repr(exc)}"
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred in the QA service.",
        ) from exc
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
    f"You are {stakeholder_name}, participating in a cybersecurity "
    "discussion. Represent your stakeholder role accurately. "
    "Be concise, practical, and respectful. Respond directly to "
    "the other stakeholder's points and work toward a realistic "
    "shared action plan. Use 2-3 complete sentences. "
    "Finish your sentences and do not end mid-thought. "
    "Never claim agreement without evidence."
)

    closing_instruction = ""
    if closing:
        closing_instruction = (
            "\nThis is your final closing statement. Use 2-3 sentences "
            "to state the action both stakeholders can support. "
            "Mention any important unresolved disagreement briefly. "
            "Do not falsely claim the other stakeholder agreed."
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
        "options": {
            "num_predict": 160,
        },
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
    dialogue_start = time.perf_counter()

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
                call_start = time.perf_counter()

                reply = await generate_persona_response(
                    stakeholder_name=stakeholder_name,
                    topic=request.topic,
                    transcript=transcript,
                )

                print(
                    f"[Timing] Discussion turn {turn} - "
                    f"{stakeholder_name}: "
                    f"{time.perf_counter() - call_start:.2f} seconds"
                )

                transcript.append({
                    "turn": turn,
                    "speaker": stakeholder_name,
                    "message": reply,
                })

        # Generate explicit closing statements.
        closing_turn = request.rounds + 1

        for stakeholder_name in stakeholder_order:
            call_start = time.perf_counter()

            reply = await generate_persona_response(
                stakeholder_name=stakeholder_name,
                topic=request.topic,
                transcript=transcript,
                closing=True,
            )

            print(
                f"[Timing] Closing statement - "
                f"{stakeholder_name}: "
                f"{time.perf_counter() - call_start:.2f} seconds"
            )

            transcript.append({
                "turn": closing_turn,
                "speaker": stakeholder_name,
                "message": reply,
            })

        # Evaluate the completed dialogue.
        evaluation_start = time.perf_counter()

        agreement: AgreementResult = await evaluate_agreement(
            topic=request.topic,
            transcript=transcript,
        )

        print(
            f"[Timing] Agreement evaluation: "
            f"{time.perf_counter() - evaluation_start:.2f} seconds"
        )

        print(
            f"[Timing] Total dialogue request: "
            f"{time.perf_counter() - dialogue_start:.2f} seconds"
        )

        return {
            "topic": request.topic,
            "rounds": request.rounds,
            "model": MODEL_NAME,
            "stakeholders": [
                {"name": stakeholder_name}
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
