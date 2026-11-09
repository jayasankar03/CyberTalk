# CyberTalk — Two Chatbots, One Agreement

CyberTalk is a local AI-powered cybersecurity collaboration platform. It brings two user-defined cybersecurity stakeholders together for a structured discussion, evaluates whether they reach a meaningful agreement, and identifies unresolved issues and practical next steps.

The application also includes a cybersecurity question-and-answer assistant, user authentication, conversation management, secure sharing, and administrator account management.

## 1. Key Features

### AI-powered cybersecurity discussion
- Define any two distinct stakeholder roles; stakeholders are not restricted to predefined personas.
- Enter a cybersecurity topic and select between 1 and 5 discussion rounds.
- Generate alternating responses from both stakeholders.
- Generate closing statements from each stakeholder.
- Evaluate the discussion and return a structured agreement result.

### Agreement evaluation
The evaluator identifies:
- Agreement status: `agreement_reached`, `partial_agreement`, or `no_agreement`.
- Explanation of the evaluation.
- Shared decision supported by both stakeholders.
- Unresolved disagreements.
- Recommended next actions.

The evaluation applies conservative agreement rules. A proposal is not automatically treated as approval, outstanding third-party approval is treated as a dependency, and unresolved material disagreements prevent an unsupported full-agreement result.

### Cybersecurity Q&A
- Ask individual cybersecurity-related questions.
- Check whether a question is relevant to cybersecurity before generating an answer.
- Return concise, practical answers from the local AI model.
- Reject questions that are clearly outside the cybersecurity scope.

### User accounts and authentication
- User registration and login.
- Username or email-based login.
- Secure password hashing using Argon2.
- JWT-based authentication.
- Authenticated password changes.
- Password recovery through email.
- Single-use, expiring password-reset tokens stored as hashes.
- Account activation and deactivation checks.

### Profile management
- View and update username and email.
- Upload and replace a profile picture.
- JPEG and PNG image validation.
- Profile picture upload limit of 5 MB.

### Conversation management
- Automatically save dialogue and Q&A conversations to account history.
- View previous conversations.
- Rename conversations.
- Delete individual conversations or all saved conversations.
- Export conversations as PDF or TXT.
- Create read-only sharing links with optional expiration.
- Revoke existing sharing links.

### Administrator dashboard
- Search registered users.
- View account details.
- Update user roles.
- Deactivate and reactivate accounts.
- View administrator audit history.
- Protect the primary administrator account and prevent unsafe administrator-role changes.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI |
| Frontend | Streamlit |
| Programming language | Python |
| AI runtime | Ollama |
| Default AI model | Llama 3.2 3B (`llama3.2:3b`) |
| Database | SQLite |
| ORM | SQLAlchemy |
| Data validation | Pydantic |
| Authentication | JWT |
| Password hashing | Argon2 |
| HTTP client | HTTPX and Requests |
| Email delivery | SMTP |
| PDF generation | ReportLab |
| Image validation | Pillow |
| Testing | pytest and unittest |

## 3. Application Architecture

CyberTalk uses a separate FastAPI backend and Streamlit frontend.

```text
                  User
                   |
                   v
            Streamlit Frontend
                   |
                   | HTTP requests
                   v
              FastAPI API
              /         \
             /           \
            v             v
      SQLite Database   Ollama API
            |             |
            |             v
            |        Llama 3.2 3B
            |
            v
     Users, conversations,
     reset tokens, sharing
     links and audit logs
```

The backend manages authentication, account permissions, conversation storage, agreement evaluation, and communication with Ollama. The frontend provides the user interface and communicates with the backend through HTTP requests.

## 4. Prerequisites

Install the following before starting:

1. Python 3.10 or later.
2. Git.
3. Ollama.
4. The `llama3.2:3b` model.
5. An SMTP account if email-based password recovery is required.

Download the model:

```bash
ollama pull llama3.2:3b
```

Start Ollama if it is not already running:

```bash
ollama serve
```

The default Ollama endpoint is:

```text
http://127.0.0.1:11434/api/chat
```

## 5. Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/jayasankar03/CyberTalk.git
cd CyberTalk
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the virtual environment

Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 5: Configure environment variables

Create a `.env` file in the project root using `.env.example` as the template.

Configure the application secret, environment, Ollama settings, and email settings as appropriate.

Generate a secure application secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Example development configuration:

```env
CYBERTALK_SECRET_KEY=your-generated-secret
CYBERTALK_ENV=development

OLLAMA_URL=http://127.0.0.1:11434/api/chat
MODEL_NAME=llama3.2:3b

CYBERTALK_PASSWORD_RESET_URL=http://localhost:8501/

CYBERTALK_SMTP_HOST=smtp.gmail.com
CYBERTALK_SMTP_PORT=587
CYBERTALK_SMTP_USERNAME=your-email@gmail.com
CYBERTALK_SMTP_PASSWORD=your-app-password
CYBERTALK_SMTP_FROM_EMAIL=your-email@gmail.com
```

For Gmail, use an app password where applicable rather than your normal account password.

For production, configure:

```env
CYBERTALK_ENV=production
CYBERTALK_PASSWORD_RESET_URL=https://your-approved-domain/
CYBERTALK_PASSWORD_RESET_ALLOWED_HOSTS=your-approved-domain
```

Production password-reset URLs must use HTTPS and a hostname explicitly included in `CYBERTALK_PASSWORD_RESET_ALLOWED_HOSTS`. Use a strong secret of at least 32 characters. Do not commit `.env` or real credentials to source control.

### Step 6: Start the FastAPI backend

Open the first terminal, activate the virtual environment, and run:

```bash
python -m uvicorn main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

The application validates its environment, security secret, Ollama configuration, and database initialization during startup.

### Step 7: Start the Streamlit frontend

Open a second terminal in the project directory, activate the same virtual environment, and run:

```bash
streamlit run frontend.py
```

The frontend is normally available at:

```text
http://localhost:8501
```

If the backend runs at a different address, configure `CYBERTALK_API_URL` in the environment.

Keep both the backend and frontend running while using CyberTalk.

## 6. Initial Administrator Setup

Newly registered accounts receive the standard `user` role.

The project includes `provision_initial_admin.py` to designate an existing account as the primary administrator.

Before running the script, make sure the intended account has been registered and that `TARGET_USERNAME` in the script matches that account's username.

Then run:

```bash
python provision_initial_admin.py
```

The script checks that the account exists and is active and that another primary administrator has not already been designated.

Keep access to the primary administrator account secure.

## 7. API Endpoints

All protected endpoints require a valid JWT bearer access token.

### Authentication and account management

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/register` | Register a user |
| POST | `/login` | Authenticate a user |
| POST | `/password-reset/request` | Request password recovery |
| POST | `/password-reset/confirm` | Confirm a password reset |
| POST | `/change-password` | Change the authenticated user's password |
| GET | `/users/me` | Retrieve the current profile |
| PUT | `/users/me` | Update profile information |
| POST | `/users/me/profile-picture` | Upload or replace a profile picture |
| GET | `/users/me/profile-picture` | Retrieve the profile picture |

### AI features

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/chat` | Generate an AI response |
| POST | `/ask` | Answer a cybersecurity question |
| POST | `/dialogue` | Generate a stakeholder discussion and evaluate agreement |

### Conversation history and sharing

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/history` | Save a conversation |
| GET | `/history` | Retrieve the user's conversations |
| GET | `/history/{history_id}` | Retrieve one conversation |
| PUT | `/history/{history_id}` | Rename a conversation |
| DELETE | `/history/{history_id}` | Delete one conversation |
| DELETE | `/history` | Delete all conversations |
| POST | `/history/{history_id}/share` | Create a sharing link |
| GET | `/shared/{token}` | View a shared conversation |
| DELETE | `/history/{history_id}/share/{share_id}` | Revoke a sharing link |

### Administrator operations

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/admin/users` | Search and list users |
| GET | `/admin/users/{user_id}` | Retrieve account details |
| PATCH | `/admin/users/{user_id}/role` | Update a user's role |
| PATCH | `/admin/users/{user_id}/deactivate` | Deactivate an account |
| PATCH | `/admin/users/{user_id}/reactivate` | Reactivate an account |
| GET | `/admin/audit-logs` | Retrieve administrator audit history |

### General endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend welcome response |
| GET | `/health` | Backend health status |

For request and response schemas, use the interactive Swagger documentation at `/docs`.

## 8. Stakeholder Dialogue Example

Example request:

```json
{
  "topic": "Should our organization require phishing-resistant MFA?",
  "stakeholder_1": "Chief Information Security Officer",
  "stakeholder_2": "Cloud Infrastructure Engineer",
  "rounds": 2
}
```

Both stakeholder roles are user-defined. The same role cannot be used for both stakeholders.

For two regular rounds, the application generates:

- Two alternating contributions per round.
- One closing statement from each stakeholder.
- Six dialogue messages in total.

The completed dialogue is passed to the agreement evaluator.

The response includes the discussion, stakeholder information, model information, agreement result, and AI performance metrics.

## 9. Agreement Evaluation

The agreement evaluator uses the complete discussion, including both closing statements.

It distinguishes between:

- `agreement_reached`: Both stakeholders explicitly accept a clear shared decision, with no material unresolved issues.
- `partial_agreement`: Some decisions are shared, but a material issue, disagreement, or condition remains.
- `no_agreement`: No meaningful common decision has been accepted.

The evaluator also checks for inconsistent results. For example, a result claiming full agreement without a shared decision is downgraded rather than accepted as full agreement.

A proposal is not treated as approval, and outstanding third-party approval remains a dependency.

## 10. Security and Data Management

CyberTalk includes several security controls:

- Argon2 password hashing.
- Signed JWT authentication with a 30-minute default access-token lifetime.
- Database-backed user and role verification.
- Account activation checks.
- Authentication-version checks for invalidating older sessions after relevant account changes.
- SHA-256 hashing of password-reset and sharing tokens before storage.
- Expiring, single-use password-reset tokens.
- Generic password-reset request responses to reduce account enumeration.
- Role-based administrator authorization.
- Protection against self-demotion and removal of the last administrator.
- Administrator audit records for account-management actions.
- Validation of uploaded profile-picture content, format, size, and dimensions.
- Read-only public conversation sharing with expiration and revocation support.

The SQLite database is created in the project directory as:

```text
cybertalk.db
```

Profile pictures are stored separately in:

```text
profile_pictures/
```

Conversation data, user accounts, password-reset records, sharing records, and audit history are managed by the backend.

Do not expose the database, profile-picture directory, environment file, or application secrets publicly.

## 11. Running the Test Suite

Activate the virtual environment and run:

```bash
python -m pytest -v
```

Or use the concise output:

```bash
pytest -q
```

The test suite covers:

- Registration and login.
- Authentication and authorization.
- Password hashing and token handling.
- Password recovery and email delivery.
- Profile management and profile pictures.
- Account lifecycle management.
- Administrator operations and audit history.
- Dialogue generation and response structure.
- Agreement evaluation.
- Cybersecurity Q&A validation and response handling.
- Conversation history and ownership.
- Sharing links, expiration, and revocation.
- Frontend behavior.
- Startup and configuration validation.

Most AI-related tests use mocked responses, so the test suite does not require every test to generate a live response through Ollama. A separate manual run with Ollama is still useful for checking real model behavior and performance.

## 12. Project Structure

```text
CyberTalk/
│
├── main.py
├── frontend.py
├── config.py
├── database.py
│
├── auth.py
├── security.py
├── user_model.py
├── chat_history_model.py
├── password_reset_model.py
├── share_link_model.py
├── audit_log_model.py
│
├── agreement.py
├── agreement_evaluator.py
├── personas.py
├── qa_service.py
│
├── email_service.py
├── provision_initial_admin.py
│
├── styles/
│   └── cybertalk.css
│
├── tests/
│   ├── ai_api_test_helpers.py
│   ├── test_admin_api.py
│   ├── test_agreement_evaluator.py
│   ├── test_ai_endpoint_authenticated.py
│   ├── test_ai_endpoint_security.py
│   ├── test_auth.py
│   ├── test_change_password_api.py
│   ├── test_chat_history_api.py
│   ├── test_chat_history_model.py
│   ├── test_config.py
│   ├── test_dialogue.py
│   ├── test_dialogue_response.py
│   ├── test_email_service.py
│   ├── test_frontend.py
│   ├── test_login.py
│   ├── test_password_reset_api.py
│   ├── test_password_reset_model.py
│   ├── test_profile.py
│   ├── test_qa_api.py
│   ├── test_qa_service.py
│   ├── test_registration.py
│   ├── test_security.py
│   ├── test_share_links_api.py
│   ├── test_startup.py
│   └── test_user_model.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Important modules

| File | Responsibility |
|---|---|
| `main.py` | FastAPI application, authentication dependencies, API endpoints, dialogue orchestration, and Ollama integration |
| `frontend.py` | Streamlit interface, workspaces, authentication UI, history, profile, and administrator dashboard |
| `config.py` | Environment and Ollama configuration |
| `database.py` | SQLite database connection, table creation, and schema migrations |
| `auth.py` | JWT token creation and verification |
| `security.py` | Password hashing and secure token utilities |
| `user_model.py` | User account and profile data |
| `chat_history_model.py` | Saved conversation records |
| `password_reset_model.py` | Password-reset token records |
| `share_link_model.py` | Conversation sharing records |
| `audit_log_model.py` | Administrator audit records |
| `agreement.py` | Agreement response schema |
| `agreement_evaluator.py` | AI-powered agreement evaluation and consistency checks |
| `qa_service.py` | Cybersecurity relevance validation and Q&A generation |
| `email_service.py` | Password-reset email creation and SMTP delivery |
| `provision_initial_admin.py` | Initial primary administrator setup |
| `styles/cybertalk.css` | Shared frontend styling |

## 13. Project Objective

CyberTalk demonstrates how locally hosted Generative AI can support structured cybersecurity decision-making between stakeholders with different responsibilities.

By combining stakeholder dialogue, conservative agreement evaluation, cybersecurity Q&A, secure account management, and conversation history, the application provides a complete platform for exploring cybersecurity decisions and identifying practical areas of agreement.