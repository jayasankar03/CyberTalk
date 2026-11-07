import hashlib
import secrets
import logging
import time
import httpx
import os
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from streamlit import user
from email_service import send_password_reset_email
from datetime import datetime, timedelta, timezone
from pydantic import ConfigDict
from typing import Literal
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    status,
)
from contextlib import asynccontextmanager
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
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Request,
    status,
)

from auth import (
    create_access_token,
    decode_access_token,
    get_secret_key,
)

from config import (
    OLLAMA_URL,
    MODEL_NAME,
    validate_environment,
    validate_ollama_configuration,
)

from database import (
    get_db,
    create_db_tables,
    migrate_user_account_lifecycle,
    migrate_audit_log_account_status,
    migrate_primary_admin,
    migrate_user_auth_version,
    migrate_user_profile_picture,
)

from user_model import User
from user_model import User
from audit_log_model import AuditLog
from chat_history_model import ChatHistory
from share_link_model import ShareLink
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
from uuid import uuid4

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate configuration and initialize the application."""

    logger.info("Starting CyberTalk API...")

    # Validate application configuration before database initialization.
    logger.info("Validating application configuration...")

    validate_environment()
    get_secret_key()
    validate_ollama_configuration()

    logger.info("Application configuration validation completed.")

    # Initialize database tables and migrations.
    logger.info("Initializing database tables and migrations...")

    create_db_tables()
    migrate_user_account_lifecycle()
    migrate_audit_log_account_status()
    migrate_primary_admin()
    migrate_user_auth_version()
    migrate_user_profile_picture()

    logger.info("CyberTalk API startup completed.")

    yield

    logger.info("CyberTalk API shutdown completed.")


app = FastAPI(
    title="CyberTalk API",
    lifespan=lifespan,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("cybertalk")

# ==========================================
# PROFILE PICTURE STORAGE CONFIGURATION
# ==========================================

# Store profile pictures in a dedicated server-side directory.
PROFILE_PICTURE_DIR = (
    Path(__file__).resolve().parent / "profile_pictures"
)

# Create the directory if it does not already exist.
PROFILE_PICTURE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# Maximum permitted profile-picture size: 5 MB.
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024

# Allowed image formats and their corresponding extensions.
ALLOWED_PROFILE_PICTURE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
}
def validate_profile_picture(file_content: bytes) -> str:
    """Validate profile-picture content and return its safe extension."""

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image is empty.",
        )

    if len(file_content) > MAX_PROFILE_PICTURE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Profile picture must not exceed 5 MB.",
        )

    try:
        from io import BytesIO

        with Image.open(BytesIO(file_content)) as image:
            image.verify()

        # Reopen the image after verification to inspect its format.
        with Image.open(BytesIO(file_content)) as image:
            image_format = image.format

            if image_format not in ALLOWED_PROFILE_PICTURE_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only JPEG and PNG images are allowed.",
                )

            # Enforce reasonable image dimensions.
            if image.width > 5000 or image.height > 5000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image dimensions must not exceed 5000 x 5000 pixels.",
                )

            image.load()

        return ALLOWED_PROFILE_PICTURE_FORMATS[image_format]

    except HTTPException:
        raise

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted image file.",
        )

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


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    created_at: datetime
    is_active: bool
    is_primary_admin: bool
    deactivated_at: datetime | None = None
    profile_picture: str | None = None

# JWT bearer authentication
security = HTTPBearer(auto_error=False)

class AdminRoleUpdateRequest(BaseModel):
    role: Literal["user", "admin"]

class AuditLogResponse(BaseModel):
    """Safe response model for administrator audit records."""

    id: int
    actor_user_id: int
    actor_username: str
    target_user_id: int
    target_username: str
    action: str
    previous_role: str
    new_role: str
    previous_status: str | None = None
    new_status: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserProfileUpdateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Username cannot be empty.")

        return value

    @field_validator("email")
    @classmethod
    def validate_profile_email(cls, value: str) -> str:
        value = value.strip().lower()

        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Please provide a valid email address.")

        return value
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

class ChatHistoryRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Conversation title cannot be empty.")

        return value

class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_type: str
    title: str
    content: str
    created_at: datetime

class ShareLinkCreateRequest(BaseModel):
    expires_in_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
    )


class ShareLinkCreateResponse(BaseModel):
    share_id: int
    share_url: str
    expires_at: datetime | None


class SharedConversationResponse(BaseModel):
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
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated. Please contact an administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_auth_version = payload.get("auth_version")

    if (
        type(token_auth_version) is not int
        or token_auth_version != user.auth_version
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid. Please log in again.",
        )
    return user

def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow access only to authenticated administrators."""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required.",
        )

    return current_user

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
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact an administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Generate a JWT access token.
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "auth_version": user.auth_version,
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

    current_time = datetime.now(timezone.utc)

    # Generate a secure token and store only its SHA-256 hash.
    reset_token = generate_password_reset_token()
    token_hash = hash_reset_token(reset_token)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=current_time + timedelta(minutes=30),
    )

    try:
        # Invalidate all previous unused reset tokens for this user.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update(
            {"used_at": current_time},
            synchronize_session=False,
        )

        # Save the new token and previous-token invalidation together.
        db.add(reset_record)
        db.commit()
        db.refresh(reset_record)

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
        # Invalidate the new token if email delivery fails.
        try:
            db.query(PasswordResetToken).filter(
                PasswordResetToken.id == reset_record.id,
                PasswordResetToken.used_at.is_(None),
            ).update(
                {"used_at": datetime.now(timezone.utc)},
                synchronize_session=False,
            )

            db.commit()

        except Exception:
            db.rollback()

            logger.exception(
                "Failed to invalidate a reset token after email delivery failure."
            )

        # Never log the token or email address.
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

        user.auth_version += 1

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

@app.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allow an authenticated user to securely change their password."""

    # Verify that the current password is correct.
    if not verify_password(
        request.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    # Ensure the new password and confirmation match.
    if request.new_password != request.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match.",
        )

    # Prevent changing the password to the existing password.
    if verify_password(
        request.new_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )

    current_time = datetime.now(timezone.utc)

    try:
        # Hash and update the new password.
        current_user.hashed_password = hash_password(
            request.new_password
        )

        current_user.auth_version += 1

        # Invalidate all outstanding password-reset tokens.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == current_user.id,
            PasswordResetToken.used_at.is_(None),
        ).update(
            {"used_at": current_time},
            synchronize_session=False,
        )

        # Save the password update and token invalidation together.
        db.commit()

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to change password."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change password. Please try again.",
        )

    return {
        "message": "Password changed successfully."
    }
@app.get(
    "/users/me",
    response_model=UserProfileResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
@app.put(
    "/users/me",
    response_model=UserProfileResponse,
)
def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check whether another account uses the requested username.
    existing_username = (
        db.query(User)
        .filter(
            User.username == request.username,
            User.id != current_user.id,
        )
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered.",
        )

    # Check whether another account uses the requested email.
    existing_email = (
        db.query(User)
        .filter(
            User.email == request.email,
            User.id != current_user.id,
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    # Update only the permitted profile fields.
    current_user.username = request.username
    current_user.email = request.email

    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        logger.exception("Failed to update user profile.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update profile. Please try again.",
        )

    return current_user

@app.post("/users/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload or replace the authenticated user's profile picture."""

    # Read at most 5 MB + 1 byte to enforce the upload limit.
    file_content = await file.read(MAX_PROFILE_PICTURE_SIZE + 1)

    # Validate the actual image content.
    file_extension = validate_profile_picture(file_content)

    # Generate a unique server-controlled filename.
    new_filename = f"{uuid4().hex}{file_extension}"
    new_file_path = PROFILE_PICTURE_DIR / new_filename

    # Save the new image before modifying the database.
    try:
        new_file_path.write_bytes(file_content)

    except OSError:
        logger.exception("Failed to save uploaded profile picture.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save profile picture.",
        )

    # Remember the previous filename for safe replacement.
    previous_filename = current_user.profile_picture

    # Update the authenticated user's database record.
    current_user.profile_picture = new_filename

    try:
        db.commit()

    except Exception:
        db.rollback()

        # Remove the newly saved image if the database update fails.
        try:
            new_file_path.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Failed to remove an unreferenced profile picture."
            )

        logger.exception("Failed to update profile picture in database.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update profile picture.",
        )

    # Delete the previous picture only after the database update succeeds.
    if previous_filename and previous_filename != new_filename:
        # Only allow deletion of a file inside the picture directory.
        if Path(previous_filename).name == previous_filename:
            previous_file_path = (
                PROFILE_PICTURE_DIR / previous_filename
            )

            try:
                previous_file_path.unlink(missing_ok=True)

            except OSError:
                logger.warning(
                    "Could not delete previous profile picture: %s",
                    previous_filename,
                )

    return {
        "message": "Profile picture uploaded successfully.",
        "profile_picture": new_filename,
    }
@app.get("/users/me/profile-picture")
def get_my_profile_picture(
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's profile picture."""

    filename = current_user.profile_picture

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile picture has been uploaded.",
        )

    # Reject filenames containing directory traversal.
    if Path(filename).name != filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found.",
        )

    profile_directory = PROFILE_PICTURE_DIR.resolve()
    file_path = (PROFILE_PICTURE_DIR / filename).resolve()

    # Ensure the resolved file remains inside the picture directory.
    try:
        file_path.relative_to(profile_directory)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found.",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found.",
        )

    # Only serve the supported image formats.
    media_type = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
    }.get(file_path.suffix.lower())

    if media_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found.",
        )

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={"Cache-Control": "private, no-store"},
    )

@app.get(
    "/admin/users",
    response_model=list[UserProfileResponse],
)
def get_all_users(
    search: str | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return registered users, optionally filtered by username or email."""

    query = db.query(User)

    if search and search.strip():
        search_pattern = f"%{search.strip()}%"

        query = query.filter(
            User.username.ilike(search_pattern)
            | User.email.ilike(search_pattern)
        )

    return query.order_by(User.id.asc()).all()

@app.get(
    "/admin/audit-logs",
    response_model=list[AuditLogResponse],
)
def get_admin_audit_logs(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return the latest administrator audit records."""

    audit_logs = (
        db.query(AuditLog)
        .order_by(
            AuditLog.created_at.desc(),
            AuditLog.id.desc(),
        )
        .limit(100)
        .all()
    )

    return audit_logs

@app.get(
    "/admin/users/{user_id}",
    response_model=UserProfileResponse,
)
def get_admin_user_details(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return safe account details for one user."""

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user

@app.patch("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    request: AdminRoleUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a user's role and record the administrator action."""

    target_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # The primary administrator can never be demoted.
    if (
        target_user.is_primary_admin
        and request.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The primary administrator cannot be demoted.",
        )

    # Never allow a role change to leave zero administrators.
    if (
        target_user.role == "admin"
        and request.role == "user"
    ):
        admin_count = db.query(User).filter(
            User.role == "admin"
        ).count()

        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last administrator cannot be demoted.",
            )


    # Administrators cannot change their own roles.
    if target_user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Administrators cannot change their own role.",
        )

    # Avoid unnecessary updates and audit entries.
    if target_user.role == request.role:
        return {
            "message": "User already has the requested role.",
            "user": UserProfileResponse.model_validate(target_user),
        }

    previous_role = target_user.role
    # Prepare the audit record using authenticated and database values.
    audit_record = AuditLog(
        actor_user_id=current_admin.id,
        actor_username=current_admin.username,
        target_user_id=target_user.id,
        target_username=target_user.username,
        action="role_changed",
        previous_role=previous_role,
        new_role=request.role,
    )

    try:
        target_user.role = request.role
        db.add(audit_record)

        # Save the role update and audit record together.
        db.commit()
        db.refresh(target_user)

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to update a user role or save its audit record."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update the user role. Please try again.",
        )

    return {
        "message": "User role updated successfully.",
        "user": UserProfileResponse.model_validate(target_user),
    }


def update_user_account_status(
    user_id: int,
    activate: bool,
    current_admin: User,
    db: Session,
):
    """Activate or deactivate a user and record the administrator action."""

    target_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # The primary administrator account cannot be deactivated.
    if not activate and target_user.is_primary_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The primary administrator cannot be deactivated.",
        )

    # Administrators cannot deactivate their own accounts.
    if not activate and target_user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Administrators cannot deactivate their own accounts.",
        )

    # Avoid unnecessary updates and audit records.
    if target_user.is_active == activate:
        return {
            "message": (
                "User is already active."
                if activate
                else "User is already deactivated."
            ),
            "user": UserProfileResponse.model_validate(target_user),
        }

    # Never deactivate the last active administrator.
    if not activate and target_user.role == "admin":
        active_admin_count = db.query(User).filter(
            User.role == "admin",
            User.is_active.is_(True),
        ).count()

        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last active administrator cannot be deactivated.",
            )

    previous_status = (
        "active" if target_user.is_active else "inactive"
    )
    new_status = "active" if activate else "inactive"

    audit_record = AuditLog(
        actor_user_id=current_admin.id,
        actor_username=current_admin.username,
        target_user_id=target_user.id,
        target_username=target_user.username,
        action=(
            "account_reactivated"
            if activate
            else "account_deactivated"
        ),
        previous_role=target_user.role,
        new_role=target_user.role,
        previous_status=previous_status,
        new_status=new_status,
    )

    try:
        target_user.auth_version += 1
        target_user.is_active = activate
        target_user.deactivated_at = (
            None if activate else datetime.now(timezone.utc)
        )

        db.add(audit_record)

        # Account status and audit record are saved together.
        db.commit()
        db.refresh(target_user)

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to update account status or save its audit record."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update account status. Please try again.",
        )

    return {
        "message": (
            "User account reactivated successfully."
            if activate
            else "User account deactivated successfully."
        ),
        "user": UserProfileResponse.model_validate(target_user),
    }


@app.patch("/admin/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Deactivate a user account."""

    return update_user_account_status(
        user_id=user_id,
        activate=False,
        current_admin=current_admin,
        db=db,
    )


@app.patch("/admin/users/{user_id}/reactivate")
def reactivate_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reactivate a previously deactivated user account."""

    return update_user_account_status(
        user_id=user_id,
        activate=True,
        current_admin=current_admin,
        db=db,
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/ask")
async def ask_question(
    request: QARequest,
    current_user: User = Depends(get_current_user)
):
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
        error_message = str(exc)

        if error_message == "Please enter a question.":
            safe_detail = "Please enter a question."
        else:
            safe_detail = "Invalid QA request."

        logger.warning("Invalid QA request.")

        raise HTTPException(
            status_code=400,
            detail=safe_detail,
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
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
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
async def dialogue(
    request: DialogueRequest,
    current_user: User = Depends(get_current_user)
):
    dialogue_start = time.perf_counter()
    generation_start = time.perf_counter()

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

        generation_duration = (
            time.perf_counter() - generation_start
        )

        # Evaluate the completed dialogue.
        evaluation_start = time.perf_counter()

        agreement: AgreementResult = await evaluate_agreement(
            topic=request.topic,
            transcript=transcript,
        )

        evaluation_duration = (
            time.perf_counter() - evaluation_start
        )

        total_duration = time.perf_counter() - dialogue_start

        logger.info(
            "Dialogue performance: generation=%.2fs, "
            "evaluation=%.2fs, total=%.2fs",
            generation_duration,
            evaluation_duration,
            total_duration,
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
            "performance": {
                "generation_seconds": round(
                    generation_duration, 2
                ),
                "evaluation_seconds": round(
                    evaluation_duration, 2
                ),
                "total_seconds": round(
                    total_duration, 2
                ),
                "dialogue_entries": len(transcript),
            },
        }

    except AgreementEvaluationError:
        logger.exception("Agreement evaluation failed.")
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

@app.put(
    "/history/{history_id}",
    response_model=ChatHistoryResponse,
)
def rename_chat_history(
    history_id: int,
    request: ChatHistoryRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rename one conversation owned by the authenticated user."""

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

    history.title = request.title

    db.commit()
    db.refresh(history)

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


@app.delete("/history")
def delete_all_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all conversations belonging to the authenticated user."""

    deleted_count = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "message": "All conversations deleted successfully.",
        "deleted_count": deleted_count,
    }
# ==========================================
# SECURE CONVERSATION SHARING API
# ==========================================

@app.post(
    "/history/{history_id}/share",
    response_model=ShareLinkCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_share_link(
    history_id: int,
    request: ShareLinkCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a secure read-only sharing link for an owned conversation."""

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

    # Generate a cryptographically secure, unpredictable token.
    raw_token = secrets.token_urlsafe(32)

    # Store only the SHA-256 hash of the token.
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = None

    if request.expires_in_days is not None:
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(days=request.expires_in_days)
        )

    share_link = ShareLink(
        history_id=history.id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_revoked=False,
    )

    db.add(share_link)
    db.commit()
    db.refresh(share_link)

    share_url = (
        str(http_request.base_url).rstrip("/")
        + f"/shared/{raw_token}"
    )

    return ShareLinkCreateResponse(
        share_id=share_link.id,
        share_url=share_url,
        expires_at=share_link.expires_at,
    )


@app.get(
    "/shared/{token}",
    response_model=SharedConversationResponse,
)
def view_shared_conversation(
    token: str,
    db: Session = Depends(get_db),
):
    """Public read-only access to a shared conversation."""

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    share_link = (
        db.query(ShareLink)
        .filter(ShareLink.token_hash == token_hash)
        .first()
    )

    if share_link is None or share_link.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This share link is invalid or unavailable.",
        )

    if share_link.expires_at is not None:
        expiry = share_link.expires_at

        # SQLite may return a timezone-naive datetime.
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) >= expiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This share link has expired.",
            )

    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.id == share_link.history_id)
        .first()
    )

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The shared conversation is no longer available.",
        )

    # Deliberately return no owner or account information.
    return SharedConversationResponse(
        conversation_type=history.conversation_type,
        title=history.title,
        content=history.content,
        created_at=history.created_at,
    )


@app.delete(
    "/history/{history_id}/share/{share_id}",
)
def revoke_share_link(
    history_id: int,
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a share link belonging to an owned conversation."""

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

    share_link = (
        db.query(ShareLink)
        .filter(
            ShareLink.id == share_id,
            ShareLink.history_id == history.id,
        )
        .first()
    )

    if share_link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found.",
        )

    if share_link.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link is already unavailable.",
        )

    share_link.is_revoked = True

    db.commit()

    return {
        "message": "Share link revoked successfully."
    }