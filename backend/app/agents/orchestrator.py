"""
DocIntel AI — LangGraph Orchestrator.

Multi-agent orchestration: Planner → Router → Retriever/Extractor → Synthesizer → Verifier.
"""

import json
import logging
import time
from typing import Any, TypedDict, Optional, Annotated
from operator import add

from langgraph.graph import StateGraph, END

from app.agents.planner import planner_agent
from app.agents.router import route_from_plan, route_from_verification
from app.agents.retriever import retrieval_agent
from app.agents.synthesizer import synthesizer_agent
from app.agents.verifier import verifier_agent
from app.agents.table_agent import table_agent
from app.agents.extractor import extraction_agent
from app.agents.confidence import compute_confidence, should_refuse
from app.agents.refusal import refusal_handler
from app.schemas.query import (
    AgentTrace,
    AgentTraceStep,
    Citation,
    ConfidenceScore,
    Plan,
    QueryResponse,
    SynthesizerOutput,
    VerificationResult,
)

logger = logging.getLogger(__name__)

class OrchestratorState(TypedDict):
    """State passed between agents in the LangGraph."""
    query: str
    session_id: str
    document_ids: list[str]
    history: list[dict]
    document_summaries: list[dict]

    # Agent outputs
    plan: Optional[Plan]
    retrieved_chunks: list[dict]
    draft_answer: Optional[SynthesizerOutput]
    verification: Optional[VerificationResult]
    final_answer: Optional[str]
    citations: list[Citation]
    confidence: Optional[ConfidenceScore]

    # Control flow
    retry_count: int
    trace: list[AgentTraceStep]
    error: Optional[str]

# Agent Node Functions

async def planner_node(state: OrchestratorState) -> dict:
    """Planner agent: analyze query intent and strategy."""
    start = time.time()

    plan = await planner_agent.plan(
        query=state["query"],
        document_summaries=state.get("document_summaries"),
        history=state.get("history"),
    )

    duration = int((time.time() - start) * 1000)

    trace_step = AgentTraceStep(
        agent="planner",
        action=f"intent={plan.intent}, strategy={plan.strategy}",
        result_summary=plan.reasoning,
        duration_ms=duration,
    )

    return {
        "plan": plan,
        "trace": state.get("trace", []) + [trace_step],
    }

async def retriever_node(state: OrchestratorState) -> dict:
    """Retriever agent: hybrid search + reranking."""
    start = time.time()

    # Use sub-queries from planner if available
    plan = state.get("plan")
    queries = [state["query"]]
    if plan and plan.sub_queries:
        queries = plan.sub_queries

    all_chunks = []
    seen_ids = set()

    for q in queries:
        chunks = await retrieval_agent.retrieve(
            query=q,
            document_ids=state["document_ids"],
        )
        for chunk in chunks:
            cid = chunk.get("id", "")
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_chunks.append(chunk)

    duration = int((time.time() - start) * 1000)

    # Check if table lookup needed
    if plan and plan.strategy == "table_lookup":
        all_chunks = await table_agent.process_table_query(state["query"], all_chunks)

    trace_step = AgentTraceStep(
        agent="retriever",
        action=f"Retrieved {len(all_chunks)} chunks",
        result_summary=f"Top score: {all_chunks[0]['score']:.3f}" if all_chunks else "No results",
        duration_ms=duration,
    )

    return {
        "retrieved_chunks": all_chunks,
        "trace": state.get("trace", []) + [trace_step],
    }

async def synthesizer_node(state: OrchestratorState) -> dict:
    """Synthesizer agent: generate grounded answer."""
    start = time.time()

    chunks = state.get("retrieved_chunks", [])

    if not chunks:
        return {
            "draft_answer": SynthesizerOutput(
                answer="Tidak ada informasi relevan yang ditemukan di dokumen.",
                statements=[],
                not_found_reason="No relevant chunks retrieved.",
            ),
            "trace": state.get("trace", []) + [AgentTraceStep(
                agent="synthesizer",
                action="No chunks available",
                result_summary="Refusal due to empty retrieval",
                duration_ms=0,
            )],
        }

    output = await synthesizer_agent.synthesize(
        query=state["query"],
        chunks=chunks,
        history=state.get("history"),
    )

    duration = int((time.time() - start) * 1000)

    trace_step = AgentTraceStep(
        agent="synthesizer",
        action=f"Generated answer ({len(output.statements)} statements)",
        result_summary=output.answer[:200] if output.answer else "No answer",
        duration_ms=duration,
    )

    return {
        "draft_answer": output,
        "trace": state.get("trace", []) + [trace_step],
    }

async def verifier_node(state: OrchestratorState) -> dict:
    """Verifier agent: check groundedness."""
    start = time.time()

    draft = state.get("draft_answer")
    chunks = state.get("retrieved_chunks", [])

    if not draft or not draft.statements:
        return {
            "verification": VerificationResult(
                verdicts=[], overall_groundedness=0.0, should_accept=False,
            ),
            "trace": state.get("trace", []) + [AgentTraceStep(
                agent="verifier",
                action="No statements to verify",
                result_summary="Skipped",
                duration_ms=0,
            )],
        }

    statements = [s.model_dump() for s in draft.statements]
    result = await verifier_agent.verify_statements(statements, chunks)

    duration = int((time.time() - start) * 1000)

    # Compute confidence
    retrieval_score = chunks[0]["score"] if chunks else 0.0
    citation_coverage = (
        sum(1 for s in draft.statements if s.citation_chunk_ids) / len(draft.statements)
        if draft.statements else 0.0
    )

    confidence = compute_confidence(
        retrieval_score=retrieval_score,
        groundedness_score=result.overall_groundedness,
        citation_coverage=citation_coverage,
    )

    trace_step = AgentTraceStep(
        agent="verifier",
        action=f"Groundedness: {result.overall_groundedness:.2f}, Confidence: {confidence.score:.2f}",
        result_summary=f"{'✅ Accept' if result.should_accept else '❌ Reject'}",
        duration_ms=duration,
    )

    return {
        "verification": result,
        "confidence": confidence,
        "trace": state.get("trace", []) + [trace_step],
    }

async def refusal_node(state: OrchestratorState) -> dict:
    """Generate refusal response."""
    plan = state.get("plan")
    chunks = state.get("retrieved_chunks", [])
    confidence = state.get("confidence")

    if plan and plan.requires_clarification:
        reason = "ambiguous"
        message = refusal_handler.generate_refusal(
            reason, clarification_question=plan.clarification_question,
        )
    elif not chunks:
        reason = "low_retrieval"
        message = refusal_handler.generate_refusal(reason)
    elif confidence and should_refuse(confidence):
        reason = "low_confidence"
        message = refusal_handler.generate_refusal(reason)
    else:
        reason = "not_supported"
        message = refusal_handler.generate_refusal(reason)

    return {
        "final_answer": message,
        "trace": state.get("trace", []) + [AgentTraceStep(
            agent="refusal",
            action=f"Reason: {reason}",
            result_summary=message[:100],
            duration_ms=0,
        )],
    }

async def extractor_node(state: OrchestratorState) -> dict:
    """Extraction agent node."""
    start = time.time()

    result = await extraction_agent.extract(
        document_id=state["document_ids"][0] if state["document_ids"] else "",
        schema={},  # Will be populated from the request
        document_ids=state["document_ids"],
    )

    duration = int((time.time() - start) * 1000)

    return {
        "final_answer": json.dumps(result, ensure_ascii=False, indent=2),
        "trace": state.get("trace", []) + [AgentTraceStep(
            agent="extractor",
            action="Structured extraction",
            result_summary=f"Extracted {len(result)} fields",
            duration_ms=duration,
        )],
    }

# Routing Functions

def route_after_planner(state: OrchestratorState) -> str:
    """Route based on planner output."""
    plan = state.get("plan")
    if not plan:
        return "retriever"
    return route_from_plan(plan)

def route_after_verifier(state: OrchestratorState) -> str:
    """Route based on verifier output."""
    verification = state.get("verification")
    confidence = state.get("confidence")
    retry_count = state.get("retry_count", 0)
    chunks = state.get("retrieved_chunks", [])

    if not chunks:
        return "reject"

    if verification and verification.should_accept and confidence and not should_refuse(confidence):
        return "accept"

    action = route_from_verification(
        should_accept=verification.should_accept if verification else False,
        retry_count=retry_count,
    )
    return action

# Build Graph

def build_orchestrator_graph() -> StateGraph:
    """Build the LangGraph orchestrator."""
    graph = StateGraph(OrchestratorState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("refusal", refusal_node)

    # Set entry point
    graph.set_entry_point("planner")

    # Planner → conditional edges
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "retriever": "retriever",
            "extractor": "extractor",
            "clarify": "refusal",
        },
    )

    # Retriever → Synthesizer
    graph.add_edge("retriever", "synthesizer")

    # Synthesizer → Verifier
    graph.add_edge("synthesizer", "verifier")

    # Extractor → Verifier
    graph.add_edge("extractor", "verifier")

    # Verifier → conditional edges
    graph.add_conditional_edges(
        "verifier",
        route_after_verifier,
        {
            "accept": END,
            "reject": "refusal",
            "retry": "retriever",
        },
    )

    # Refusal → END
    graph.add_edge("refusal", END)

    return graph

# Compile the graph
orchestrator_graph = build_orchestrator_graph().compile()

async def run_orchestrator(
    query: str,
    document_ids: list[str],
    session_id: str = "",
    history: list[dict] | None = None,
    document_summaries: list[dict] | None = None,
) -> QueryResponse:
    """
    Run the full orchestrator pipeline.

    Returns a complete QueryResponse with answer, citations, confidence, and trace.
    """
    initial_state: OrchestratorState = {
        "query": query,
        "session_id": session_id,
        "document_ids": document_ids,
        "history": history or [],
        "document_summaries": document_summaries or [],
        "plan": None,
        "retrieved_chunks": [],
        "draft_answer": None,
        "verification": None,
        "final_answer": None,
        "citations": [],
        "confidence": None,
        "retry_count": 0,
        "trace": [],
        "error": None,
    }

    # Run the graph
    final_state = await orchestrator_graph.ainvoke(initial_state)

    # Build citations from retrieved chunks
    citations = []
    for chunk in final_state.get("retrieved_chunks", []):
        payload = chunk.get("payload", {})
        citations.append(Citation(
            doc_id=payload.get("document_id", ""),
            doc_name="",
            page_number=payload.get("page_number", 0) or 0,
            chunk_id=payload.get("chunk_id", chunk.get("id", "")),
            section_path=payload.get("section_path"),
            text_snippet=payload.get("content", "")[:200],
            bbox=payload.get("bbox"),
            relevance_score=chunk.get("rerank_score", chunk.get("score", 0)),
        ))

    # Build final response
    draft = final_state.get("draft_answer")
    confidence = final_state.get("confidence")
    final_answer = final_state.get("final_answer")

    answer = final_answer or (draft.answer if draft else "Tidak dapat memproses pertanyaan.")

    trace = AgentTrace(
        steps=final_state.get("trace", []),
        total_duration_ms=sum(s.duration_ms for s in final_state.get("trace", [])),
    )

    return QueryResponse(
        message_id="",  # Will be set by API layer
        answer=answer,
        statements=draft.statements if draft else [],
        citations=citations,
        confidence=confidence or ConfidenceScore(
            score=0.0, level="low",
            retrieval_score=0.0, groundedness_score=0.0,
            llm_confidence=0.0, citation_coverage=0.0,
        ),
        trace=trace,
        not_found_reason=draft.not_found_reason if draft else None,
    )
