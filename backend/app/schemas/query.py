"""
DocIntel AI — Query & Citation Schemas.

Pydantic models for Q&A, citations, confidence scoring, and agent traces.
"""

from typing import Any, Optional, Literal

from pydantic import BaseModel, Field

# Citation
class Citation(BaseModel):
    """Citation linking answer to source document."""
    doc_id: str
    doc_name: str
    page_number: int
    chunk_id: str
    section_path: Optional[str] = None
    text_snippet: str = Field(max_length=500)  # 200 char preview
    bbox: Optional[dict[str, float]] = None  # {x0, y0, x1, y1}
    relevance_score: float = Field(ge=0.0, le=1.0)

# Statements with Citations
class Statement(BaseModel):
    """A single claim in an answer with citation references."""
    claim: str
    citation_chunk_ids: list[str]

# Confidence
class ConfidenceScore(BaseModel):
    """Confidence score breakdown."""
    score: float = Field(ge=0.0, le=1.0)
    level: Literal["high", "medium", "low"]
    retrieval_score: float = Field(ge=0.0, le=1.0)
    groundedness_score: float = Field(ge=0.0, le=1.0)
    llm_confidence: float = Field(ge=0.0, le=1.0)
    citation_coverage: float = Field(ge=0.0, le=1.0)

# Agent Trace
class AgentTraceStep(BaseModel):
    """Single step in agent execution trace."""
    agent: str  # planner, router, retriever, synthesizer, verifier
    action: str
    result_summary: str
    duration_ms: int
    metadata: Optional[dict[str, Any]] = None

class AgentTrace(BaseModel):
    """Full agent execution trace."""
    steps: list[AgentTraceStep]
    total_duration_ms: int

# Query Request & Response
class QueryRequest(BaseModel):
    """Q&A query request."""
    session_id: Optional[str] = None
    document_ids: list[str]
    query: str
    options: Optional[dict[str, Any]] = Field(
        default_factory=lambda: {"stream": True, "include_trace": True}
    )

class QueryResponse(BaseModel):
    """Q&A query response (non-streaming)."""
    message_id: str
    answer: str
    statements: list[Statement]
    citations: list[Citation]
    confidence: ConfidenceScore
    trace: Optional[AgentTrace] = None
    not_found_reason: Optional[str] = None

# Synthesizer Output (LLM structured output)
class SynthesizerOutput(BaseModel):
    """Structured output from synthesizer agent (via Instructor)."""
    answer: str
    statements: list[Statement]
    not_found_reason: Optional[str] = None

# Verifier Output
class VerificationVerdict(BaseModel):
    """Verification result for a single statement."""
    statement: str
    verdict: Literal["ENTAILED", "PARTIAL", "CONTRADICTED", "NOT_SUPPORTED"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class VerificationResult(BaseModel):
    """Aggregated verification results."""
    verdicts: list[VerificationVerdict]
    overall_groundedness: float = Field(ge=0.0, le=1.0)
    should_accept: bool

# Planner Output
class Plan(BaseModel):
    """Planner agent output."""
    intent: Literal["qa", "extraction", "comparison", "clarification_needed"]
    sub_queries: list[str]
    strategy: Literal["single_retrieval", "multi_retrieval", "table_lookup", "structured_extract"]
    reasoning: str
    requires_clarification: bool = False
    clarification_question: Optional[str] = None

# WebSocket Events
class WSTokenEvent(BaseModel):
    """Streaming token event."""
    event: str = "token"
    content: str

class WSCitationEvent(BaseModel):
    """Citation event."""
    event: str = "citation"
    citations: list[Citation]

class WSConfidenceEvent(BaseModel):
    """Confidence score event."""
    event: str = "confidence"
    score: float
    level: str

class WSAgentStepEvent(BaseModel):
    """Agent step event."""
    event: str = "agent_step"
    step: AgentTraceStep

class WSDoneEvent(BaseModel):
    """Stream completion event."""
    event: str = "done"
    message_id: str

class WSErrorEvent(BaseModel):
    """Error event."""
    event: str = "error"
    message: str
    code: Optional[str] = None
