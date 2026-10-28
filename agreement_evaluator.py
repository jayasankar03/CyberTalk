
import json

import httpx

from agreement import AgreementResult


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


class AgreementEvaluationError(Exception):
    """Raised when agreement evaluation fails."""


async def evaluate_agreement(
    topic: str,
    transcript: list[dict],
) -> AgreementResult:
    """Evaluate whether the stakeholders reached a meaningful agreement."""

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
Evaluate the following cybersecurity discussion impartially.

Topic:
{topic}

Complete dialogue:
{dialogue}

Determine whether the stakeholders reached a meaningful agreement.

Use these status definitions:

1. agreement_reached:
   Both stakeholders explicitly support a compatible, sufficiently clear
   shared decision. No material disagreement remains.

2. partial_agreement:
   They share some goals or decisions, but an important disagreement,
   unconfirmed proposal, or unresolved condition remains.

3. no_agreement:
   They have not accepted a meaningful shared decision.

Rules:
- Evaluate the complete dialogue, including both closing statements.
- A proposal by one stakeholder is not mutual agreement by itself.
- Do not assume agreement because the conversation ended.
- Check whether both stakeholders explicitly support the same decision.
- If one stakeholder asks for more information or has not accepted a
  proposal, do not claim full agreement on that proposal.
- Identify contradictions in the dialogue, including inconsistent
  budget totals or allocations that exceed the stated budget.
- Do not present a disputed figure or proposal as an approved action.
- Distinguish agreed decisions from proposed next steps.
- If important issues remain unresolved, list them and recommend actions.
- Use only evidence supported by the supplied dialogue.
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
                    "Assess the supplied dialogue carefully. Do not infer "
                    "consent, invent facts, or treat proposals as approvals. "
                    "Return a structured JSON result."
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
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()

        content = result["message"]["content"]
        parsed_result = json.loads(content)
        agreement = AgreementResult.model_validate(parsed_result)
        
        # Correct inconsistent agreement evaluations conservatively.
        if agreement.status == "agreement_reached":
            if not agreement.shared_decision or not agreement.shared_decision.strip():
                agreement.status = "partial_agreement"
                agreement.explanation = (
                    "The evaluation claimed full agreement but did not "
                    "identify a shared decision. Confirmation is required."
                )
                agreement.unresolved_disagreements.append(
                    "A mutually accepted shared decision has not been established."
                )
                agreement.next_actions.append(
                    "Ask both stakeholders to confirm a specific shared decision."
                )

            elif agreement.unresolved_disagreements:
                agreement.status = "partial_agreement"
                agreement.explanation = (
                    "The evaluation reported full agreement but also listed "
                    "unresolved disagreements. These must be clarified."
                )
                agreement.next_actions.append(
                    "Resolve the listed disagreements before declaring full agreement."
                )

        if agreement.status == "no_agreement" and agreement.shared_decision:
            agreement.status = "partial_agreement"
            agreement.explanation = (
                "The evaluation reported no agreement but also supplied "
                "a shared decision. The decision requires confirmation."
            )
            agreement.unresolved_disagreements.append(
                "The status and shared decision in the evaluation are inconsistent."
            )
            agreement.next_actions.append(
                "Confirm whether both stakeholders accept the proposed decision."
            )

        return agreement

    except httpx.HTTPError as exc:
        raise AgreementEvaluationError(
            f"Ollama agreement evaluation failed: {exc}"
        ) from exc

    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise AgreementEvaluationError(
            "Ollama returned an invalid agreement evaluation response."
        ) from exc
