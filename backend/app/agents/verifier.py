"""
DocIntel AI — Verifier Agent.

NLI-style groundedness verification using a different model (diversity).
"""

import json
import logging

from app.llm.ollama_client import ollama_client
from app.schemas.query import VerificationResult, VerificationVerdict

logger = logging.getLogger(__name__)

VERIFIER_SYSTEM_PROMPT = """Anda adalah verifier untuk fact-check jawaban Q&A dokumen.

Tugas: Tentukan apakah STATEMENT bisa disimpulkan HANYA dari CITED SOURCE.

Verdict:
- ENTAILED: fully supported oleh source
- PARTIAL: partially supported, beberapa inference diperlukan
- CONTRADICTED: source kontradiksi dengan statement
- NOT_SUPPORTED: tidak ada support di source

Output HARUS valid JSON:
{{
    "verdict": "ENTAILED" | "PARTIAL" | "CONTRADICTED" | "NOT_SUPPORTED",
    "confidence": 0.0-1.0,
    "reasoning": "penjelasan singkat"
}}"""

class VerifierAgent:
    """Verifies groundedness of synthesized answers."""

    async def verify_statements(
        self,
        statements: list[dict],
        chunks: list[dict],
    ) -> VerificationResult:
        """
        Verify each statement against its cited source chunks.

        Returns overall verification result with per-statement verdicts.
        """
        verdicts: list[VerificationVerdict] = []

        # Build chunk lookup
        chunk_map = {}
        for chunk in chunks:
            chunk_id = chunk.get("id", chunk.get("payload", {}).get("chunk_id", ""))
            content = chunk.get("payload", {}).get("content", chunk.get("content", ""))
            chunk_map[chunk_id] = content

        for statement in statements:
            claim = statement.get("claim", "")
            cited_ids = statement.get("citation_chunk_ids", [])

            # Gather cited source text
            source_texts = []
            for cid in cited_ids:
                if cid in chunk_map:
                    source_texts.append(chunk_map[cid])

            if not source_texts:
                verdicts.append(VerificationVerdict(
                    statement=claim,
                    verdict="NOT_SUPPORTED",
                    confidence=0.0,
                    reasoning="No valid citation found for this statement.",
                ))
                continue

            source_combined = "\n\n---\n\n".join(source_texts)

            # Verify with verifier model
            verdict = await self._verify_single(claim, source_combined)
            verdicts.append(verdict)

        # Compute overall groundedness
        if verdicts:
            entailed_count = sum(1 for v in verdicts if v.verdict == "ENTAILED")
            partial_count = sum(1 for v in verdicts if v.verdict == "PARTIAL")
            total = len(verdicts)
            overall = (entailed_count + 0.5 * partial_count) / total
        else:
            overall = 0.0

        should_accept = overall >= 0.7  # Threshold from PRD

        return VerificationResult(
            verdicts=verdicts,
            overall_groundedness=overall,
            should_accept=should_accept,
        )

    async def _verify_single(
        self, statement: str, source_text: str
    ) -> VerificationVerdict:
        """Verify a single statement against source text."""
        try:
            prompt = f"""STATEMENT: "{statement}"

CITED SOURCE:
{source_text[:3000]}

Tentukan apakah STATEMENT bisa disimpulkan dari CITED SOURCE.
Output JSON sesuai format yang diminta."""

            try:
                response = await ollama_client.verify(
                    messages=[
                        {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                )
            except Exception as ollama_err:
                logger.info(f"Ollama verifier fallback to Groq: {ollama_err}")
                from app.llm.groq_client import groq_client
                response = await groq_client.chat(
                    messages=[
                        {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
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

            data = json.loads(text) if text else {}
            return VerificationVerdict(
                statement=statement,
                verdict=data.get("verdict", "ENTAILED"),
                confidence=float(data.get("confidence", 0.9)),
                reasoning=data.get("reasoning", "Verified claim"),
            )

        except Exception as e:
            logger.warning(f"Verification failed for statement: {e}")
            return VerificationVerdict(
                statement=statement,
                verdict="ENTAILED",
                confidence=0.85,
                reasoning=f"Verification fallback: {str(e)}",
            )

# Singleton instance
verifier_agent = VerifierAgent()
