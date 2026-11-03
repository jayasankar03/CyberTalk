import json
import logging

import httpx

from agreement import AgreementResult


logger = logging.getLogger("cybertalk")


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
Evaluate this cybersecurity discussion using only the evidence provided.

Topic: {topic}

Complete dialogue:
{dialogue}

Select exactly one status:
- agreement_reached: Both stakeholders explicitly support the same
  clear decision, with no material unresolved disagreement.
- partial_agreement: Common ground exists, but a material issue,
  disagreement, or condition remains unresolved.
- no_agreement: No meaningful mutually accepted decision exists.

Rules:
- Include both closing statements in the evaluation.
- A proposal is not an agreement unless both stakeholders support it.
- Check contradictions, including conflicting budget figures.
- Separate agreed decisions from proposed actions.
- Do not invent facts or infer consent.
- If evidence is insufficient, do not claim full agreement.
- Keep explanations concise and lists focused.

Return only valid JSON with exactly these fields:
{{
  "status": "agreement_reached",
  "explanation": "Brief evidence-based explanation.",
  "shared_decision": "Mutually accepted decision, or null.",
  "unresolved_disagreements": [],
  "next_actions": []
}}

Allowed statuses: agreement_reached, partial_agreement, no_agreement.
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
        "options": {
            "num_predict": 180,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()

            logger.info(
                "Ollama metrics - agreement evaluation: "
                "total=%.2fs, load=%.2fs, prompt=%.2fs, "
                "generation=%.2fs, prompt_tokens=%s, generated_tokens=%s",
                result.get("total_duration", 0) / 1_000_000_000,
                result.get("load_duration", 0) / 1_000_000_000,
                result.get("prompt_eval_duration", 0) / 1_000_000_000,
                result.get("eval_duration", 0) / 1_000_000_000,
                result.get("prompt_eval_count", 0),
                result.get("eval_count", 0),
            )

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
