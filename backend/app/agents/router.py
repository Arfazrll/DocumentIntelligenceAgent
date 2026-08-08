"""
DocIntel AI — Agent Router.

Routes from planner output to the appropriate agent(s).
"""

import logging
from typing import Literal

from app.schemas.query import Plan

logger = logging.getLogger(__name__)

def route_from_plan(plan: Plan) -> str:
    """
    Determine next agent based on planner output.

    Returns: 'retriever', 'extractor', 'refusal', or 'clarify'
    """
    if plan.requires_clarification:
        return "clarify"

    strategy_routes = {
        "single_retrieval": "retriever",
        "multi_retrieval": "retriever",
        "table_lookup": "retriever",  # Goes through retriever first, then table agent
        "structured_extract": "extractor",
    }

    route = strategy_routes.get(plan.strategy, "retriever")
    logger.info(f"Router: intent={plan.intent}, strategy={plan.strategy} → {route}")
    return route

def route_from_verification(
    should_accept: bool,
    retry_count: int = 0,
    max_retries: int = 1,
) -> str:
    """
    Determine action after verification.

    Returns: 'accept', 'reject', or 'retry'
    """
    if should_accept:
        return "accept"

    if retry_count < max_retries:
        return "retry"

    return "reject"
