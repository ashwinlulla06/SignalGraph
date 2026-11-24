from datetime import date as Date
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

AgentKey = Literal[
    "market_data",
    "technical",
    "anomaly",
    "cross_market",
    "sector",
    "macro",
    "filings",
    "news",
    "regulatory",
    "risk",
    "skeptic",
    "verifier"
]

class SupervisorPlan(BaseModel):
    selected_agents : list[AgentKey] = Field(
        min_length=1, 
        description="The smallest set of registered specialist agent keys required to investigate the question."
    )

    routing_summary : str

class InvestigationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str = Field(
        min_length=3,
        max_length=500,
    )

    symbol: str = Field(
        min_length=1,
        max_length=20,
    )

    investigation_date: Date | None = Field(
        default=None,
        alias="date"
    )

class NewsAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=2000)
    confidence : float = Field(ge=0.0, le=1.0)
    relevant_article_ids : list[str] = Field(default_factory=list, max_length=5)


class VerifierAnalysis(BaseModel):
    verdict : Literal[
        "supported", 
        "partially_supported", 
        "unsupported", 
        "insufficient_evidence"
    ]
    summary : str = Field(min_length=1, max_length=2500)
    confidence : float = Field(ge=0.0, le=1.0, description="Confidence in the verifier's verdict, not confidence in the original claim.")
    reviewed_evidence_ids : list[str] = Field(default_factory=list, max_length=10)


class VerificationPlan(BaseModel):
    required_checks: list[
        Literal[
            "market_quote",
            "company_news",
            "ai_sector",
            "government_policy",
        ]
    ] = Field(
        min_length=1,
        max_length=4,
    )

    reasoning: str = Field(
        min_length=1,
        max_length=1000,
    )


class SkepticAnalysis(BaseModel):
    summary : str = Field(
        min_length=1, max_length=2500
    )
    confidence : float = Field(
        ge=0.0, le=1.0
    )
    reviewed_evidence_ids : list[str] = Field(default_factory=list, max_length=10)


class SynthesisReport(BaseModel):
    final_report : str = Field(min_length=1, max_length=5000)
