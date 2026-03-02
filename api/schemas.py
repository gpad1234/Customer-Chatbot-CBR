"""Pydantic request/response models for the FastAPI layer."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# /query
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    problem: str = Field(..., min_length=1, description="The customer's problem description")
    top_k: int = Field(5, ge=1, le=20, description="Number of similar cases to retrieve")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")


class ChatQueryRequest(BaseModel):
    problem: str = Field(..., min_length=1, description="The customer's problem description")
    top_k: int = Field(3, ge=1, le=10)
    use_ai: bool = Field(True, description="Refine answer with OpenAI when key is available")


class ChatQueryResponse(BaseModel):
    answer: str
    intent: str | None
    category: str | None
    similarity_score: float
    ai_enhanced: bool


class MatchedCase(BaseModel):
    case_id: int | None
    problem: str
    solution: str
    metadata: dict[str, Any]
    similarity_score: float


class QueryResponse(BaseModel):
    answer: str
    matched_case: MatchedCase | None
    top_matches: list[MatchedCase]


# ---------------------------------------------------------------------------
# /cases
# ---------------------------------------------------------------------------

class CaseCreate(BaseModel):
    problem: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseResponse(BaseModel):
    case_id: int
    problem: str
    solution: str
    metadata: dict[str, Any]
