"""
DocIntel AI — WebSocket API.

Streaming Q&A via WebSocket with real-time agent trace updates.
"""

import json
import logging
import uuid
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.orchestrator import run_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """
    WebSocket endpoint for streaming Q&A.

    Events (server → client):
    - agent_step: Real-time agent execution step
    - token: Streaming answer token
    - citation: Citations for the answer
    - confidence: Final confidence score
    - done: Stream complete
    - error: Error occurred
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive query
            data = await websocket.receive_text()
            request = json.loads(data)

            query = request.get("query", "")
            document_ids = request.get("document_ids", [])
            session_id = request.get("session_id", "")

            if not query or not document_ids:
                await websocket.send_json({
                    "event": "error",
                    "message": "Missing 'query' or 'document_ids'",
                })
                continue

            try:
                # Send agent step: starting
                await websocket.send_json({
                    "event": "agent_step",
                    "step": {
                        "agent": "orchestrator",
                        "action": "Starting query processing",
                        "result_summary": f"Query: {query[:100]}",
                        "duration_ms": 0,
                    },
                })

                # Run orchestrator (non-streaming for now)
                response = await run_orchestrator(
                    query=query,
                    document_ids=document_ids,
                    session_id=session_id,
                )

                # Send agent trace steps
                if response.trace:
                    for step in response.trace.steps:
                        await websocket.send_json({
                            "event": "agent_step",
                            "step": step.model_dump(),
                        })

                # Stream answer tokens (simulate for non-streaming response)
                answer = response.answer
                chunk_size = 10  # characters per token event
                for i in range(0, len(answer), chunk_size):
                    token = answer[i:i + chunk_size]
                    await websocket.send_json({
                        "event": "token",
                        "content": token,
                    })

                # Send citations
                if response.citations:
                    await websocket.send_json({
                        "event": "citation",
                        "citations": [c.model_dump() for c in response.citations],
                    })

                # Send confidence
                if response.confidence:
                    await websocket.send_json({
                        "event": "confidence",
                        "score": response.confidence.score,
                        "level": response.confidence.level,
                    })

                # Done
                msg_id = str(uuid.uuid4())
                await websocket.send_json({
                    "event": "done",
                    "message_id": msg_id,
                })

            except Exception as e:
                logger.error(f"Query processing error: {e}")
                await websocket.send_json({
                    "event": "error",
                    "message": str(e),
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
