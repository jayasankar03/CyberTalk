
import json

import httpx

from agreement import AgreementResult


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


class AgreementEvaluationError(Exception):
    """Raised when agreement evaluation fails."""


async def evaluate_agreement(
    topic: str,
    transcript: list[dict]
) -> AgreementResult:
    """
    Evaluate whether the stakeholders reached a meaningful agreement.
    """

    if not transcript:
        raise ValueError(
            "The transcript must contain at least one dialogue message."
        )

    dialogue = "\n".join(
        f"Turn {item['turn']} - {item['speaker']}: "
        f"{item['message']}"
        for item in transcript
    )

    prompt = f"""
Evaluate the following cybersecurity discussion between two stakeholders.

Topic:
{topic}

Complete dialogue:
{dialogue}

Determine whether the stakeholders reached a meaningful agreement.

Use these status definitions:

1. agreement_reached:
   Both stakeholders support a compatible, sufficiently clear decision.

2. partial_agreement:
   They agree on some decisions or actions, but important disagreements
   or unresolved conditions remain.

3. no_agreement:
   They have not reached a meaningful shared decision.

Important rules:
- Evaluate the actual dialogue, not merely the number of turns.
- Do not assume agreement simply because the discussion ended.
- Do not treat one stakeholder's proposal as a shared decision unless
  the dialogue supports that conclusion.
- Identify important unresolved disagreements.
- Recommend practical next actions.
- Be neutral and consider both stakeholders' positions.
- Return only a valid JSON object matching this structure:

{{
  "status": "agreement_reached",
  "explanation": "Explain the evidence supporting the assessment.",
  "shared_decision": "The mutually supported decision, or null.",
  "unresolved_disagreements": [],
  "next_actions": []
}}

The status must be exactly one of:
agreement_reached, partial_agreement, no_agreement.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an impartial cybersecurity agreement evaluator. "
                    "Assess the supplied dialogue carefully and return "
                    "a structured JSON result."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "format": "json",
        "stream": False,
        "keep_alive": "10m",
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

        content = result["message"]["content"]
        parsed_result = json.loads(content)

        return AgreementResult.model_validate(parsed_result)

    except httpx.HTTPError as exc:
        raise AgreementEvaluationError(
            f"Ollama agreement evaluation failed: {exc}"
        ) from exc

    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise AgreementEvaluationError(
            "Ollama returned an invalid agreement evaluation response."
        ) from exc
