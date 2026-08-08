"""
DocIntel AI — Planner Agent.

Analyzes query intent, decomposes complex queries, selects strategy.
"""

import json
import logging
from typing import Optional

from app.llm.groq_client import groq_client
from app.schemas.query import Plan

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """Anda adalah planner untuk sistem Q&A dokumen asuransi Indonesia.
Analisis query user, tentukan strategi optimal.

Available documents:
{document_summaries}

Conversation history (last 5 turns):
{history}

Tugas:
1. Klasifikasi intent: qa | extraction | comparison | clarification_needed
2. Jika query ambigu (mis. "premi Platinum" tanpa area) → clarification
3. Decompose ke sub-queries jika kompleks
4. Pilih retrieval strategy: single_retrieval | multi_retrieval | table_lookup | structured_extract

Constraint:
- Untuk pertanyaan umum seperti "dokumen ini tentang apa?", "ringkasan dokumen", "apa isi file ini?" → intent: "qa", strategy: "single_retrieval", sub_queries: ["ringkasan isi dokumen deskripsi umum"], requires_clarification: false.
- Jangan minta klarifikasi untuk pertanyaan ringkasan/gambaran umum dokumen.
- Hanya minta klarifikasi jika query benar-benar terpotong atau tidak jelas.
- Pertimbangkan konteks history
- Untuk query numerik spesifik (premi, age, dll) → table_lookup
- Untuk "extract semua..." → structured_extract

Output HARUS valid JSON sesuai schema berikut:
{{
    "intent": "qa" | "extraction" | "comparison" | "clarification_needed",
    "sub_queries": ["query1", "query2"],
    "strategy": "single_retrieval" | "multi_retrieval" | "table_lookup" | "structured_extract",
    "reasoning": "alasan pemilihan strategi",
    "requires_clarification": false,
    "clarification_question": null
}}"""

class PlannerAgent:
    """Analyzes queries and creates execution plans."""

    async def plan(
        self,
        query: str,
        document_summaries: list[dict] | None = None,
        history: list[dict] | None = None,
    ) -> Plan:
        """
        Analyze query and create execution plan.
        """
        doc_summary_str = "Tidak ada dokumen tersedia."
        if document_summaries:
            doc_summary_str = "\n".join(
                f"- {d.get('filename', 'unknown')} ({d.get('doc_type', 'unknown')}, "
                f"{d.get('page_count', '?')} halaman)"
                for d in document_summaries
            )

        history_str = "Tidak ada history."
        if history:
            history_str = "\n".join(
                f"{'User' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')[:200]}"
                for m in history[-5:]
            )

        system_prompt = PLANNER_SYSTEM_PROMPT.format(
            document_summaries=doc_summary_str,
            history=history_str,
        )

        try:
            response = await groq_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            text = (response or "").strip()
            if "```" in text:
                parts = text.split("```")
                for part in parts:
                    p = part.strip()
                    if p.startswith("json"):
                        p = p[4:].strip()
                    if p.startswith("{") and p.endswith("}"):
                        text = p
                        break
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]

            plan_data = json.loads(text) if text else {}
            return Plan(
                intent=plan_data.get("intent", "qa"),
                sub_queries=plan_data.get("sub_queries") or [query],
                strategy=plan_data.get("strategy", "single_retrieval"),
                reasoning=plan_data.get("reasoning", "Extracted plan"),
                requires_clarification=plan_data.get("requires_clarification", False),
                clarification_question=plan_data.get("clarification_question"),
            )

        except Exception as e:
            logger.error(f"Planner failed: {e}. Using default plan.")
            return Plan(
                intent="qa",
                sub_queries=[query],
                strategy="single_retrieval",
                reasoning=f"Fallback plan due to error: {str(e)}",
                requires_clarification=False,
            )

# Singleton instance
planner_agent = PlannerAgent()
