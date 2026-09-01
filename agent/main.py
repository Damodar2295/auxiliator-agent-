"""Main FastAPI application."""

from __future__ import annotations

import argparse
import logging
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agent.initialize import lifespan
from agent.knowledge import index_markdown, resolve_identity, retrieve
from config.constants import RAG_RETRIEVAL_THRESHOLD

logger = logging.getLogger("auxiliator")


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    user_id: str | None = None
    session_id: str | None = None
    department: str | None = None


class Source(BaseModel):
    source: str
    department: str | None = None
    score: float


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    sources: list[Source]


class RetrievalRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    score_threshold: float = Field(default=RAG_RETRIEVAL_THRESHOLD, ge=-1.0, le=1.0)
    department: str | None = None


class IndexRequest(BaseModel):
    file_path: str
    department: str


class PlaybookRequest(BaseModel):
    opportunity_name: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    industry: str | None = None
    customer_segment: str | None = None
    deal_value: float | None = Field(default=None, ge=0)
    product: str | None = None
    region: str | None = None
    days_in_stage: int | None = Field(default=None, ge=0)
    recent_activity: str | None = None
    pain_points: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    user_id: str | None = None
    session_id: str | None = None


class PlaybookResponse(BaseModel):
    opportunity_name: str
    recommended_playbook: str
    user_id: str
    session_id: str
    sources: list[Source]


app = FastAPI(
    title="Salesforce Playbook Agent",
    description="Evidence-grounded next-best-action recommendations for Salesforce opportunities.",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    return response


@app.get("/")
async def root():
    return {"message": "Salesforce Playbook Agent API", "version": "0.2.0"}


@app.get("/api/v1/health/live")
async def live():
    return {"status": "alive"}


@app.get("/api/v1/health/ready")
async def ready():
    healthy = all(hasattr(app.state, name) for name in ("graph", "embeddings", "document_store"))
    if not healthy:
        raise HTTPException(status_code=503, detail="Service is not ready")
    return {"status": "ready", "checks": {"document_store": {"status": "healthy"}}}


@app.post("/api/v1/index")
async def index(request: IndexRequest):
    try:
        return await index_markdown(app, request.file_path, request.department)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Indexing failed")
        raise HTTPException(status_code=503, detail="Knowledge indexing is unavailable") from exc


@app.post("/api/v1/retrieve")
async def retrieve_knowledge(request: RetrievalRequest):
    try:
        results = await retrieve(app, request.question, request.top_k, request.score_threshold, request.department)
        return {"question": request.question, "results": results}
    except Exception as exc:
        logger.exception("Retrieval failed")
        raise HTTPException(status_code=503, detail="Knowledge retrieval is unavailable") from exc


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_id = resolve_identity(request.user_id, "user")
    session_id = resolve_identity(request.session_id, "session")
    try:
        matches = await retrieve(app, request.query, 5, 0.1, request.department)
        context = "\n\n".join(item["content"] for item in matches)
        prompt = request.query if not context else f"Question: {request.query}\n\nRetrieved context:\n{context}"
        result = await app.state.graph.ainvoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"configurable": {"thread_id": session_id, "user_id": user_id}},
        )
        messages = result.get("messages", [])
        response_text = next(
            (str(message.content) for message in reversed(messages) if getattr(message, "type", None) == "ai"),
            "",
        )
        sources = [
            Source(source=item.get("source", ""), department=item.get("department"), score=item["score"])
            for item in matches
        ]
        return ChatResponse(response=response_text, user_id=user_id, session_id=session_id, sources=sources)
    except Exception as exc:
        logger.exception("Chat failed")
        raise HTTPException(status_code=503, detail="Assistant service is temporarily unavailable") from exc


@app.post("/api/v1/playbook/recommend", response_model=PlaybookResponse)
async def recommend_playbook(request: PlaybookRequest):
    """Recommend a seller-reviewed playbook grounded in approved sales knowledge."""
    user_id = resolve_identity(request.user_id, "user")
    session_id = resolve_identity(request.session_id, "session")
    opportunity_facts = {
        "opportunity_name": request.opportunity_name,
        "stage": request.stage,
        "industry": request.industry,
        "customer_segment": request.customer_segment,
        "deal_value": request.deal_value,
        "product": request.product,
        "region": request.region,
        "days_in_stage": request.days_in_stage,
        "recent_activity": request.recent_activity,
        "pain_points": request.pain_points,
        "competitors": request.competitors,
    }
    query = "Salesforce playbook for " + ", ".join(
        f"{key}={value}" for key, value in opportunity_facts.items() if value not in (None, "", [])
    )
    try:
        matches = await retrieve(app, query, 7, 0.0, "sales")
        context = "\n\n".join(f"Source: {item.get('source', '')}\n{item['content']}" for item in matches)
        prompt = (
            "Create a seller-reviewed next-best-action playbook for this Salesforce opportunity.\n"
            f"Opportunity facts: {opportunity_facts}\n\n"
            "Return these sections: Assessment, Recommended actions (owner and timing), Risks, "
            "Missing information, Evidence, and Confidence. Do not invent facts or perform CRM actions.\n\n"
            f"Retrieved context:\n{context or 'No matching knowledge was found.'}"
        )
        result = await app.state.graph.ainvoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"configurable": {"thread_id": session_id, "user_id": user_id}},
        )
        response_text = next(
            (
                str(message.content)
                for message in reversed(result.get("messages", []))
                if getattr(message, "type", None) == "ai"
            ),
            "",
        )
        sources = [
            Source(
                source=item.get("source", ""),
                department=item.get("department"),
                score=item["score"],
            )
            for item in matches
        ]
        return PlaybookResponse(
            opportunity_name=request.opportunity_name,
            recommended_playbook=response_text,
            user_id=user_id,
            session_id=session_id,
            sources=sources,
        )
    except Exception as exc:
        logger.exception("Playbook recommendation failed")
        raise HTTPException(status_code=503, detail="Playbook recommendation is temporarily unavailable") from exc


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    uvicorn.run(
        "agent.main:app",
        host=args.host,
        port=args.port,
        log_level="debug" if os.getenv("DEBUG_MODE", "false").lower() == "true" else "info",
    )
