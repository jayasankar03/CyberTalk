import logging
import time
import httpx
from email_service import send_password_reset_email
from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    status,
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
)

from auth import create_access_token, decode_access_token
from database import get_db, create_db_tables
from user_model import User
from chat_history_model import ChatHistory
from security import (
    hash_password,
    verify_password,
    generate_password_reset_token,
    hash_reset_token,
)
from password_reset_model import PasswordResetToken
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

class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()

        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Please provide a valid email address.")

        return value
class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)
class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    created_at: datetime
# JWT bearer authentication
security = HTTPBearer(auto_error=False)
class ChatHistoryCreateRequest(BaseModel):
    conversation_type: Literal["qa", "dialogue"]
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=50000)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Conversation title cannot be empty.")

        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Conversation content cannot be empty.")

        return value


class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_type: str
    title: str
    content: str
    created_at: datetime

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    # Reject requests without an access token.
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate the JWT.
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retrieve the user ID from the JWT subject.
    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(subject)

    # Retrieve the authenticated user from the database.
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
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

@app.post("/password-reset/request")
def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    # Use the same response for existing and unknown email addresses.
    generic_response = {
        "message": (
            "If an account exists with this email, "
            "password reset instructions will be sent."
        )
    }

    user = db.query(User).filter(
        User.email == request.email
    ).first()

    # Do not reveal whether the email is registered.
    if user is None:
        return generic_response

    # Generate a secure token and store only its SHA-256 hash.
    reset_token = generate_password_reset_token()
    token_hash = hash_reset_token(reset_token)

    current_time = datetime.now(timezone.utc)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=current_time + timedelta(minutes=30),
    )

    try:
        db.add(reset_record)
        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to create a password reset request."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process password reset request.",
        )
    # Send the reset link without exposing whether an account exists.
    try:
        send_password_reset_email(
            recipient_email=user.email,
            reset_token=reset_token,
        )
    except Exception:
        # Keep the response generic and do not log the token or email.
        logger.warning(
            "Password reset email delivery failed."
        )
    return generic_response
@app.post("/password-reset/confirm")
def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
):
    """Verify a reset token and securely update the user's password."""

    # Hash the supplied token before searching the database.
    token_hash = hash_reset_token(request.token)

    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()

    # Use one generic error for invalid, expired, and used tokens.
    invalid_token_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired password reset token.",
    )

    if reset_record is None or reset_record.used_at is not None:
        raise invalid_token_error

    current_time = datetime.now(timezone.utc)

    expires_at = reset_record.expires_at

    # SQLite may return a naive datetime even when timezone=True.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= current_time:
        raise invalid_token_error

    user = db.query(User).filter(
        User.id == reset_record.user_id
    ).first()

    if user is None:
        raise invalid_token_error

    try:
        # Atomically claim the token so concurrent requests cannot
        # successfully use the same token more than once.
        updated_count = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.id == reset_record.id,
                PasswordResetToken.used_at.is_(None),
            )
            .update(
                {"used_at": current_time},
                synchronize_session=False,
            )
        )

        if updated_count != 1:
            db.rollback()
            raise invalid_token_error

        # Hash the new password using the existing Argon2 function.
        user.hashed_password = hash_password(
            request.new_password
        )

        # Invalidate every other outstanding reset token for this user.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update(
            {"used_at": current_time},
            synchronize_session=False,
        )

        # Save the password change and token consumption together.
        db.commit()

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to complete password reset."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to reset password. Please try again.",
        )

    return {
        "message": "Password has been reset successfully."
    }
@app.get(
    "/users/me",
    response_model=UserProfileResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
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

        logger.info(
            "Ollama metrics - %s: total=%.2fs, load=%.2fs, "
            "prompt=%.2fs, generation=%.2fs, "
            "prompt_tokens=%s, generated_tokens=%s",
            stakeholder_name,
            result.get("total_duration", 0) / 1_000_000_000,
            result.get("load_duration", 0) / 1_000_000_000,
            result.get("prompt_eval_duration", 0) / 1_000_000_000,
            result.get("eval_duration", 0) / 1_000_000_000,
            result.get("prompt_eval_count", 0),
            result.get("eval_count", 0),
        )

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

# ==========================================
# AUTHENTICATED CHAT HISTORY API
# ==========================================

@app.post(
    "/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_chat_history(
    request: ChatHistoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a conversation for the authenticated user."""

    history = ChatHistory(
        user_id=current_user.id,
        conversation_type=request.conversation_type,
        title=request.title,
        content=request.content,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


@app.get(
    "/history",
    response_model=list[ChatHistoryResponse],
)
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all conversations belonging to the authenticated user."""

    history_records = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(
            ChatHistory.created_at.desc(),
            ChatHistory.id.desc(),
        )
        .all()
    )

    return history_records


@app.get(
    "/history/{history_id}",
    response_model=ChatHistoryResponse,
)
def get_single_chat_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve one conversation owned by the authenticated user."""

    history = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.id == history_id,
            ChatHistory.user_id == current_user.id,
        )
        .first()
    )

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return history


@app.delete("/history/{history_id}")
def delete_chat_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete one conversation owned by the authenticated user."""

    history = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.id == history_id,
            ChatHistory.user_id == current_user.id,
        )
        .first()
    )

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    db.delete(history)
    db.commit()

    return {
        "message": "Conversation deleted successfully."
    }
