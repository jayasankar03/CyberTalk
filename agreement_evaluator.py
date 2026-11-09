import json
import logging

import httpx

from agreement import AgreementResult
from config import OLLAMA_URL, MODEL_NAME


logger = logging.getLogger("cybertalk")

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
Evaluate the cybersecurity discussion objectively.

Topic: {topic}

Dialogue:
{dialogue}

Choose exactly one status:
- agreement_reached: Both stakeholders explicitly accept the same
  clear decision, with no material unresolved issues.
- partial_agreement: They share some decisions, but a material
  disagreement, condition, or issue remains unresolved.
- no_agreement: They have not accepted any meaningful common decision.

Evaluation rules:
- Evaluate every message, including both closing statements.
- A proposal or suggestion is not approval.
- Do not infer consent or invent facts.
- Identify conflicting commitments, conditions, and budget figures.
- Put only mutually accepted decisions in shared_decision.
- Record material unresolved issues in unresolved_disagreements.
- Include practical next actions where needed.
- If uncertain, do not declare full agreement.
- Keep the response concise and evidence-based.
- A stakeholder's general support does not mean approval of every
  specific amount, budget, deadline, or implementation detail.
- Record a specific commitment as shared only when both stakeholders
  explicitly accept that commitment.
- Treat third-party approval, such as HR approval, as a dependency
  when it is still outstanding. Include it in next_actions.
- Do not describe an initiative as fully approved when required
  stakeholder approval is still pending.
- Distinguish agreement between the two discussion participants from
  approval by people or teams outside the discussion.
- Preserve important conditions and dependencies in the evaluation.

Return only valid JSON with exactly these fields:
{{
  "status": "agreement_reached",
  "explanation": "Brief explanation based on the dialogue.",
  "shared_decision": "Mutually accepted decision, or null.",
  "unresolved_disagreements": [],
  "next_actions": []
}}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an impartial cybersecurity agreement evaluator. "
                    "Use only the supplied dialogue. Return valid JSON "
                    "matching the requested structure."
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
            "num_predict": 250,
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
