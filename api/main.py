"""FastAPI application entry point.

Run with:
    uvicorn api.main:app --reload

Set OPENAI_API_KEY in a .env file at the project root to enable AI-enhanced replies.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env from project root (silently ignored if not present)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.schemas import (
    CaseCreate,
    CaseResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    MatchedCase,
    QueryRequest,
    QueryResponse,
)
from case_base.db import delete_case, get_case, init_db, insert_case
from case_base.models import Case
from chatbot.llm import refine
from chatbot.orchestrator import query as cbr_query

_STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Pre-warm the retrieval vector cache so the first real query is fast
    from case_base.db import get_all_cases
    from retrieval.engine import retrieve
    cases = get_all_cases()
    if cases:
        retrieve("warmup", cases, top_k=1)
    yield


app = FastAPI(
    title="CBR Customer Support Chatbot",
    description="Case-Based Reasoning chatbot that adapts past support resolutions to new queries.",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Chat UI
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def chat_ui() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


# ---------------------------------------------------------------------------
# Chat query endpoint (used by the UI)
# ---------------------------------------------------------------------------

@app.post("/chat-query", response_model=ChatQueryResponse, summary="Chat query (UI endpoint)")
def chat_query(req: ChatQueryRequest) -> ChatQueryResponse:
    result = cbr_query(req.problem, top_k=req.top_k)

    intent = None
    category = None
    if result.matched_case is not None:
        intent = result.matched_case.metadata.get("intent")
        category = result.matched_case.metadata.get("category")

    answer = result.answer
    ai_enhanced = False
    if req.use_ai and result.matched_case is not None:
        refined = refine(req.problem, result)
        if refined != result.answer:
            answer = refined
            ai_enhanced = True

    return ChatQueryResponse(
        answer=answer,
        intent=intent,
        category=category,
        similarity_score=result.similarity_score,
        ai_enhanced=ai_enhanced,
    )


# ---------------------------------------------------------------------------
# Query endpoint (JSON API)
# ---------------------------------------------------------------------------

@app.post("/query", response_model=QueryResponse, summary="Submit a customer problem")
def handle_query(req: QueryRequest) -> QueryResponse:
    result = cbr_query(req.problem, top_k=req.top_k, min_score=req.min_score)

    matched = None
    if result.matched_case is not None:
        matched = MatchedCase(
            case_id=result.matched_case.case_id,
            problem=result.matched_case.problem,
            solution=result.matched_case.solution,
            metadata=result.matched_case.metadata,
            similarity_score=result.similarity_score,
        )

    top = [
        MatchedCase(
            case_id=c.case_id,
            problem=c.problem,
            solution=c.solution,
            metadata=c.metadata,
            similarity_score=s,
        )
        for c, s in result.top_matches
    ]

    return QueryResponse(answer=result.answer, matched_case=matched, top_matches=top)


# ---------------------------------------------------------------------------
# Case management endpoints
# ---------------------------------------------------------------------------

@app.post("/cases", response_model=CaseResponse, status_code=201, summary="Add a new case")
def create_case(body: CaseCreate) -> CaseResponse:
    case = Case(problem=body.problem, solution=body.solution, metadata=body.metadata)
    new_id = insert_case(case)
    return CaseResponse(
        case_id=new_id,
        problem=body.problem,
        solution=body.solution,
        metadata=body.metadata,
    )


@app.get("/cases/{case_id}", response_model=CaseResponse, summary="Get a case by ID")
def read_case(case_id: int) -> CaseResponse:
    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return CaseResponse(
        case_id=case.case_id,  # type: ignore[arg-type]
        problem=case.problem,
        solution=case.solution,
        metadata=case.metadata,
    )


@app.delete("/cases/{case_id}", status_code=204, summary="Delete a case")
def remove_case(case_id: int) -> None:
    if not delete_case(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
