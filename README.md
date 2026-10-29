# CyberTalk: Two Chatbots, One Agreement

## 1. Project Overview

CyberTalk is a Generative AI application that simulates a cybersecurity discussion between two stakeholder personas using a locally running Large Language Model (LLM).

Users can enter a cybersecurity topic, define any two distinct stakeholder personas, and specify the number of discussion rounds. The application generates alternating dialogue, adds closing statements from both stakeholders, and evaluates whether they reach an agreement.

CyberTalk also provides a cybersecurity question-and-answer feature and a Streamlit user interface.

## 2. Key Features

- **User-defined stakeholders:** Enter any two distinct professional roles.
- **Custom cybersecurity topics:** Discuss cybersecurity risks, policies, and decisions.
- **Configurable dialogue rounds:** Select between 1 and 5 regular rounds.
- **AI-generated dialogue:** Use the locally hosted Ollama model.
- **Closing statements:** Generate a final statement from each stakeholder.
- **Agreement evaluation:** Return the status, explanation, shared decision, unresolved disagreements, and next actions.
- **Cybersecurity Q&A:** Submit cybersecurity questions and receive relevant answers.
- **Streamlit frontend:** Use a graphical interface for the application's features.
- **Input validation:** Reject invalid requests and duplicate stakeholder names.
- **Automated tests:** Test API endpoints, dialogue orchestration, agreement evaluation, and frontend behavior.
- **Error handling:** Handle relevant Ollama and agreement-evaluation failures.

## 3. Technology Stack

- Python
- FastAPI
- Streamlit
- Pydantic
- Uvicorn
- Ollama
- Llama 3.2 (3B parameter model)
- HTTPX
- pytest and Python unittest

## 4. Prerequisites

Before running CyberTalk, prepare:

1. Python and pip.
2. Git.
3. Ollama.
4. The `llama3.2:3b` model downloaded through Ollama.

Verify that Ollama is running and the model is available before testing AI-powered features.

## 5. Installation and Setup

### Step 1: Open the project directory

```bash
cd CyberTalk
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the virtual environment

For Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 5: Download the Ollama model

```bash
ollama pull llama3.2:3b
```

Ensure Ollama is running locally and the model is available.

The application uses the Ollama chat endpoint:

```text
http://127.0.0.1:11434/api/chat
```

### Step 6: Start the FastAPI backend

In the first terminal, with the virtual environment activated, run:

```bash
python -m uvicorn main:app --reload
```

### Step 7: Open the API documentation

Visit:

http://127.0.0.1:8000/docs

The Swagger interface lets you inspect API endpoints and submit requests.

### Step 8: Start the Streamlit frontend

Keep the FastAPI server running. Open a **second terminal** in the project directory, activate the same virtual environment, and run:

```bash
streamlit run frontend.py
```

Streamlit will display the local URL for the user interface, typically:

http://localhost:8501

Use the URL printed in your terminal if a different port is assigned.

## 6. API Endpoints

### `GET /`

Returns a basic welcome message.

### `GET /health`

Returns the backend health status.

Example response:

```json
{
  "status": "healthy"
}
```

### `POST /chat`

Generates a response from the configured Ollama model.

Example request:

```json
{
  "message": "What are the benefits of multi-factor authentication?"
}
```

### `POST /ask`

Answers a cybersecurity question using the Q&A service.

Example request:

```json
{
  "question": "How can an organization improve phishing protection?"
}
```

The service validates the question and handles relevant invalid or malformed AI responses.

### `POST /dialogue`

Generates a multi-round discussion between two user-defined stakeholders and evaluates the completed dialogue.

Example request:

```json
{
  "topic": "Should our organization require phishing-resistant MFA?",
  "stakeholder_1": "Chief Information Security Officer",
  "stakeholder_2": "Cloud Infrastructure Engineer",
  "rounds": 2
}
```

Stakeholder names must be distinct. The number of regular rounds must be between 1 and 5.

For `rounds = 2`, the API generates four regular contributions followed by two closing statements, for six dialogue messages in total.

The response includes the topic, stakeholder names, dialogue, configured model, and agreement evaluation.

## 7. Agreement Evaluation

The dialogue response includes an `agreement` object with:

- `status`: The evaluated agreement status.
- `explanation`: Why that status was assigned.
- `shared_decision`: The common decision, when supported by the discussion.
- `unresolved_disagreements`: Issues that remain unresolved.
- `next_actions`: Suggested follow-up actions.

Supported statuses:

- `agreement_reached`
- `partial_agreement`
- `no_agreement`

Closing statements encourage both stakeholders to identify a shared decision or next step. However, they do not guarantee genuine agreement. The evaluator must report unresolved disagreements honestly rather than inventing consensus.

## 8. Running the Tests

Activate the virtual environment and run the complete test suite:

```bash
python -m pytest -v
```

The tests cover:

- Agreement evaluation and invalid evaluation results.
- Custom stakeholder names and dialogue orchestration.
- Closing statements, speaker order, and turn numbering.
- Invalid dialogue inputs and API failure handling.
- Streamlit frontend behavior.
- Cybersecurity Q&A API validation.
- Q&A service response validation and relevance checks.

Most tests use mocked AI responses, allowing them to run without generating every response through a live Ollama model.

A passing test suite verifies the covered behavior but does not replace manual testing with the actual Ollama model.

## 9. Project Structure

```text
CyberTalk/
├── main.py
├── personas.py
├── agreement.py
├── agreement_evaluator.py
├── qa_service.py
├── frontend.py
├── test_dialogue.py
├── test_agreement_evaluator.py
├── test_frontend.py
├── test_qa_api.py
├── test_qa_service.py
├── requirements.txt
├── README.md
└── .gitignore
```

- `main.py`: FastAPI application, request validation, API endpoints, dialogue orchestration, and Ollama integration.
- `personas.py`: Persona-related definitions retained by the project.
- `agreement.py`: Structured agreement result model.
- `agreement_evaluator.py`: Agreement evaluation logic.
- `qa_service.py`: Cybersecurity question validation, relevance checks, and answer generation.
- `frontend.py`: Streamlit user interface.
- `test_dialogue.py`: Dialogue API and orchestration tests.
- `test_agreement_evaluator.py`: Agreement evaluation tests.
- `test_frontend.py`: Frontend behavior tests.
- `test_qa_api.py`: Cybersecurity Q&A API tests.
- `test_qa_service.py`: Q&A service tests.
- `requirements.txt`: Python dependencies.
- `.gitignore`: Files and directories excluded from version control.

The `.venv` directory is local and should not be committed to Git.

## 10. Current Project Status

### Implemented

- FastAPI backend and health endpoint.
- Ollama-powered text generation.
- User-defined stakeholder personas.
- Configurable multi-round dialogue.
- Closing statements for both stakeholders.
- Structured agreement evaluation.
- Cybersecurity question-and-answer service.
- Streamlit frontend.
- Input validation and API error handling.
- Automated tests for the implemented components.

### Possible future improvements

- Add broader end-to-end tests using a live Ollama model.
- Improve reliability of agreement evaluation and shared-decision generation.
- Improve user-facing diagnostics for model timeouts and service availability.
- Expand frontend usability and accessibility.

## 11. Project Goal

CyberTalk demonstrates how Generative AI can support structured cybersecurity discussions between stakeholders with different responsibilities, evaluate areas of agreement and disagreement, and identify practical next steps.

The project is developed incrementally, with Git commits tracking implementation, testing, and documentation changes.