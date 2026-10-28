# CyberTalk: Two Chatbots, One Agreement

## 1. Project Overview

CyberTalk is a Generative AI application that simulates a cybersecurity discussion between two stakeholder personas using a locally running Large Language Model (LLM).

Users can provide a cybersecurity topic, define two stakeholder personas, and specify the number of discussion rounds. The application generates an alternating dialogue and evaluates whether the stakeholders reach an agreement.

The goal is to help explore cybersecurity decisions from different stakeholder perspectives and identify practical, mutually acceptable next steps.

## 2. Key Features

- **User-defined stakeholders:** Enter any two distinct stakeholder names or professional roles.
- **Custom cybersecurity topics:** Explore questions, risks, policies, and security decisions.
- **Configurable dialogue rounds:** Choose between 1 and 5 regular discussion rounds.
- **AI-generated dialogue:** Generate responses using the locally hosted Ollama language model.
- **Closing statements:** Give both stakeholders an opportunity to summarize their positions and proposed next steps.
- **Structured agreement evaluation:** Report the agreement status, explanation, shared decision, unresolved disagreements, and next actions.
- **Input validation:** Reject invalid requests and identical stakeholder names.
- **Automated testing:** Use Python's `unittest` framework and FastAPI's test client.

## 3. Technology Stack

- Python
- FastAPI
- Pydantic
- Uvicorn
- Ollama
- Llama 3.2 (3B parameter model)
- HTTPX
- Python `unittest`

A Streamlit frontend is a planned enhancement and is not yet part of the current backend implementation.

## 4. Prerequisites

Before running CyberTalk, install or prepare the following:

1. Python and pip.
2. Git.
3. Ollama.
4. The `llama3.2:3b` model downloaded in Ollama.

Verify that Ollama is installed and the required model is available before testing the AI-powered endpoints.

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

The current backend uses the Ollama chat endpoint at:

```text
http://127.0.0.1:11434/api/chat
```

### Step 6: Start the FastAPI server

```bash
python -m uvicorn main:app --reload
```

### Step 7: Open the API documentation

Visit:

http://127.0.0.1:8000/docs

The interactive Swagger UI allows you to inspect endpoints and submit test requests.

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

### `POST /dialogue`

Generates a multi-round discussion between two user-defined cybersecurity stakeholders and evaluates the resulting agreement.

Example request:

```json
{
  "topic": "Should our organization require phishing-resistant MFA?",
  "stakeholder_1": "Chief Information Security Officer",
  "stakeholder_2": "Cloud Infrastructure Engineer",
  "rounds": 2
}
```

The stakeholder names can be changed to other distinct roles. The number of regular discussion rounds must be between 1 and 5.

The API generates two stakeholder contributions per regular round, followed by two additional closing statements.

## 7. Agreement Evaluation

The dialogue response includes an `agreement` object containing:

- `status`: The evaluated agreement status.
- `explanation`: Why that status was assigned.
- `shared_decision`: The common decision, when supported by the discussion.
- `unresolved_disagreements`: Issues that remain unresolved.
- `next_actions`: Suggested follow-up actions.

The agreement status can be:

- `agreement_reached`
- `partial_agreement`
- `no_agreement`

The evaluator assesses the generated dialogue. Closing statements encourage the stakeholders to identify a shared next step, but they do not guarantee that genuine agreement will always be reached. Unresolved disagreements must be reported honestly.

## 8. Running the Tests

With the virtual environment activated, run the dialogue and agreement evaluator tests:

```bash
python -m unittest -v test_dialogue test_agreement_evaluator
```

Alternatively, discover and run the complete test suite:

```bash
python -m unittest discover -v
```

The tests cover dialogue orchestration, custom stakeholder names, turn numbering, closing statements, input validation, and agreement evaluation.

Most of these tests use mocked model responses, so they do not require live AI generation for every test.

## 9. Project Structure

```text
CyberTalk/
├── main.py
├── agreement.py
├── agreement_evaluator.py
├── test_dialogue.py
├── test_agreement_evaluator.py
├── requirements.txt
├── README.md
├── .gitignore
└── .venv/
```

- `main.py`: FastAPI application, request validation, Ollama calls, and dialogue orchestration.
- `agreement.py`: Structured agreement result model and status validation.
- `agreement_evaluator.py`: Agreement evaluation logic.
- `test_dialogue.py`: Automated tests for dialogue requests and orchestration.
- `test_agreement_evaluator.py`: Automated tests for agreement evaluation.
- `requirements.txt`: Python dependencies.
- `.gitignore`: Files and directories excluded from version control.

The virtual environment should remain local and must not be committed to Git.

## 10. Current Project Status

Implemented:

- FastAPI backend and health endpoint.
- Ollama-powered text generation.
- User-defined stakeholder personas.
- Configurable multi-round stakeholder dialogue.
- Closing statements for both stakeholders.
- Structured agreement evaluation.
- Input validation and automated tests.

Planned enhancements:

- Build a user-friendly Streamlit frontend.
- Improve handling of Ollama service failures and model timeouts.
- Add further integration and end-to-end tests.
- Improve the reliability of shared-decision generation and agreement evaluation.

## 11. Project Goal

CyberTalk aims to demonstrate how Generative AI can facilitate structured cybersecurity discussions between stakeholders with different responsibilities, evaluate areas of agreement and disagreement, and identify actionable next steps.

The project is being developed incrementally, with Git commits used to track implementation and testing progress.
