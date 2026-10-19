
from typing import Literal

from pydantic import BaseModel, Field


AgreementStatus = Literal[
    "agreement_reached",
    "partial_agreement",
    "no_agreement",
]


class AgreementResult(BaseModel):
    status: AgreementStatus = Field(
        description="The overall agreement status between the stakeholders."
    )

    explanation: str = Field(
        min_length=1,
        description="Why this agreement status was assigned."
    )

    shared_decision: str | None = Field(
        default=None,
        description="The decision both stakeholders support, if any."
    )

    unresolved_disagreements: list[str] = Field(
        default_factory=list,
        description="Important disagreements that remain unresolved."
    )

    next_actions: list[str] = Field(
        default_factory=list,
        description="Practical next steps for the stakeholders."
    )
