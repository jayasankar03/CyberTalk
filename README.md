# CyberTalk: Two Chatbots, One Agreement

## Project Overview

CyberTalk is a Generative AI project that simulates a cybersecurity discussion between two stakeholder personas and aims to reach a mutually acceptable agreement on a given topic.

The project focuses on persona-based dialogue, stakeholder priorities, and agreement generation.

## Current Progress

- Created the initial FastAPI backend.
- Implemented a basic welcome endpoint.
- Prepared the project for incremental development.

## Technology Stack

- Python
- FastAPI
- Uvicorn
- Ollama for local language model inference (planned integration)
- Streamlit for the frontend (planned integration)

## Getting Started

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the environment on Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the backend

```bash
python -m uvicorn main:app --reload
```

### 5. Open the API documentation

Visit http://127.0.0.1:8000/docs in your browser.

## Current API Endpoint

- `GET /` — Returns a welcome message.

## Future Development

- Integrate Ollama with FastAPI.
- Implement two cybersecurity stakeholder personas.
- Develop the multi-turn dialogue engine.
- Implement agreement detection.
- Build the frontend.
- Add automated tests.

## Project Status

Initial backend setup in progress.