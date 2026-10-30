
import logging
import time
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db, create_db_tables
from user_model import User
from security import hash_password, verify_password
from auth import create_access_token
import httpx
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field, field_validator
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("cybertalk")

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "llama3.2:3b"

class DialogueGenerationError(Exception):
    """Raised when dialogue generation returns an invalid response."""


def extract_dialogue_content(result: object) -> str:
    """Validate an Ollama dialogue response and extract its content."""

    if not isinstance(result, dict):
        raise DialogueGenerationError(
            "Ollama returned an invalid dialogue response."
        )

    message = result.get("message")

    if not isinstance(message, dict):
        raise DialogueGenerationError(
            "Ollama response is missing a valid message."
        )

    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise DialogueGenerationError(
            "Ollama returned empty or invalid dialogue content."
        )

    return content.strip()
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError(
                "Username must contain at least 3 characters."
            )

        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()

        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Please provide a valid email address.")

        return value
class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Username or email is required.")

        return value
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

# Create database tables when the application starts.
@app.on_event("startup")
def startup_event():
    create_db_tables()


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    # Check whether the username already exists.
    existing_username = db.query(User).filter(
        User.username == request.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered.",
        )

    # Check whether the email already exists.
    existing_email = db.query(User).filter(
        User.email == request.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    # Hash the password before storing it.
    hashed_password = hash_password(request.password)

    # Create the new user.
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password,
        role="user",
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered.",
        )

    return {
        "message": "User registered successfully.",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "created_at": new_user.created_at,
        },
    }

@app.post("/login")
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    # Find the user by username or email.
    identifier = request.identifier

    user = db.query(User).filter(
        (User.username == identifier)
        | (User.email == identifier.lower())
    ).first()

    # Reject unknown users and incorrect passwords.
    if user is None or not verify_password(
        request.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate a JWT access token.
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,
    }

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
        logger.warning(
            "Invalid QA request: %s",
            str(exc),
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except OllamaResponseError:
        logger.exception(
            "Ollama returned an invalid response during QA."
        )
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI service returned an invalid response. "
                "Please try again."
            ),
        )

    except httpx.HTTPError:
        logger.exception(
            "Ollama communication failed during QA."
        )
        raise HTTPException(
            status_code=502,
            detail="The AI service is temporarily unavailable. Please try again.",
        )

    except Exception:
        logger.exception(
            "Unexpected error occurred in the QA endpoint."
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred in the QA service.",
        )

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
    try:
        result = response.json()
    except ValueError as exc:
        raise DialogueGenerationError(
            "Ollama returned an invalid JSON response."
        ) from exc

    return extract_dialogue_content(result)


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

    except DialogueGenerationError:
        logger.exception("Invalid response during chat generation.")
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an invalid response. Please try again.",
        )

    except httpx.HTTPError:
        logger.exception("Ollama request failed during chat generation.")
        raise HTTPException(
            status_code=502,
            detail="The AI service is temporarily unavailable. Please try again.",
        )

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

                logger.info(
                    "Discussion turn %s - %s completed in %.2f seconds",
                    turn,
                    stakeholder_name,
                    time.perf_counter() - call_start,
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

            logger.info(
                "Closing statement - %s completed in %.2f seconds",
                stakeholder_name,
                time.perf_counter() - call_start,
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

        logger.info(
            "Agreement evaluation completed in %.2f seconds",
            time.perf_counter() - evaluation_start,
        )

        logger.info(
            "Total dialogue request completed in %.2f seconds",
            time.perf_counter() - dialogue_start,
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

    except AgreementEvaluationError:
        logger.exception(
            "Agreement evaluation failed for topic: %s",
            request.topic,
        )
        raise HTTPException(
            status_code=502,
            detail="The agreement evaluation service failed. Please try again.",
        )
    except DialogueGenerationError:
        logger.exception(
        "Invalid Ollama response during dialogue generation."
        )
        raise HTTPException(
        status_code=502,
        detail="The AI service returned an invalid response. Please try again.",
        )
    except httpx.HTTPError:
        logger.exception(
            "Ollama communication failed during dialogue generation."
        )
        raise HTTPException(
            status_code=502,
            detail="The AI service is temporarily unavailable. Please try again.",
        )
