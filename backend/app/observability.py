"""
DocIntel AI — Observability (Langfuse Integration).

Tracks all LLM calls, agent traces, and performance metrics.
"""

import logging
from typing import Any, Optional
from functools import wraps

from app.config import settings

logger = logging.getLogger(__name__)

_langfuse = None

def get_langfuse():
    """Lazy-initialize Langfuse client."""
    global _langfuse
    if _langfuse is None:
        try:
            from langfuse import Langfuse
            _langfuse = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
            logger.info("Langfuse initialized successfully")
        except Exception as e:
            logger.warning(f"Langfuse initialization failed: {e}. Observability disabled.")
            _langfuse = None
    return _langfuse

def create_trace(
    name: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """Create a new Langfuse trace."""
    lf = get_langfuse()
    if not lf:
        return None

    try:
        return lf.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"Failed to create trace: {e}")
        return None

def log_llm_call(
    trace,
    name: str,
    model: str,
    input_text: str,
    output_text: str,
    duration_ms: int,
    metadata: Optional[dict] = None,
):
    """Log an LLM call to Langfuse."""
    if not trace:
        return

    try:
        trace.generation(
            name=name,
            model=model,
            input=input_text[:5000],  # Don't log full raw content
            output=output_text[:5000],
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"Failed to log LLM call: {e}")

def log_retrieval(
    trace,
    query: str,
    results_count: int,
    top_score: float,
    duration_ms: int,
):
    """Log a retrieval event to Langfuse."""
    if not trace:
        return

    try:
        trace.span(
            name="retrieval",
            input={"query": query},
            output={
                "results_count": results_count,
                "top_score": top_score,
            },
            metadata={"duration_ms": duration_ms},
        )
    except Exception as e:
        logger.warning(f"Failed to log retrieval: {e}")

def flush():
    """Flush Langfuse events."""
    lf = get_langfuse()
    if lf:
        try:
            lf.flush()
        except Exception:
            pass
