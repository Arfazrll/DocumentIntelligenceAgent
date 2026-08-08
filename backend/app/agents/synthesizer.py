"""
DocIntel AI — Synthesizer Agent.

Generates grounded answers from retrieved context with mandatory citations.
"""

import json
import logging
from typing import Any, AsyncGenerator

from app.llm.groq_client import groq_client
from app.schemas.query import SynthesizerOutput

logger = logging.getLogger(__name__)

SYNTHESIZER_SYSTEM_PROMPT = """Anda adalah asisten Q&A untuk dokumen asuransi.
Jawab HANYA berdasarkan CONTEXT di bawah.

ATURAN KETAT:
1. Jangan gunakan pengetahuan umum. Hanya dari CONTEXT.
2. Setiap fakta HARUS punya citation ke chunk_id.
3. Jika informasi TIDAK ADA di context, katakan tegas: "Informasi tersebut tidak ditemukan di dokumen."
4. Jangan menebak, jangan menyimpulkan di luar teks.
5. Untuk nilai numerik, kutip persis seperti di dokumen.
6. Untuk kalkulasi, tampilkan formula (bukan langsung hasil).
7. Jawab dalam bahasa yang sama dengan pertanyaan.

CONTEXT:
{context}

CONVERSATION HISTORY:
{history}

Output HARUS valid JSON:
{{
    "answer": "jawaban lengkap dengan referensi [chunk_id]",
    "statements": [
        {{"claim": "pernyataan fakta", "citation_chunk_ids": ["chunk_id_1"]}}
    ],
    "not_found_reason": null
}}

Jika tidak menemukan jawaban di CONTEXT, set answer ke pesan penolakan dan isi not_found_reason."""

class SynthesizerAgent:
    """Generates answers from retrieved context."""

    async def synthesize(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        history: list[dict] | None = None,
    ) -> SynthesizerOutput:
        """
        Generate answer from retrieved chunks.

        Each chunk dict should contain: id, content, section_path, page_number.
        """
        # Format context
        context_parts = []
        for chunk in chunks:
            chunk_id = chunk.get("id", chunk.get("payload", {}).get("chunk_id", "unknown"))
            content = chunk.get("payload", {}).get("content", chunk.get("content", ""))
            section = chunk.get("payload", {}).get("section_path", "")
            page = chunk.get("payload", {}).get("page_number", "?")

            context_parts.append(
                f"[chunk_id: {chunk_id}] (Page {page}, Section: {section})\n{content}"
            )

        context_str = "\n\n---\n\n".join(context_parts)

        history_str = "Tidak ada history."
        if history:
            history_str = "\n".join(
                f"{'User' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')[:300]}"
                for m in history[-5:]
            )

        system_prompt = SYNTHESIZER_SYSTEM_PROMPT.format(
            context=context_str,
            history=history_str,
        )

        try:
            response = await groq_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
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
            if "answer" in data:
                return SynthesizerOutput(
                    answer=data.get("answer", "Terjadi kesalahan saat memproses jawaban."),
                    statements=data.get("statements", []),
                    not_found_reason=data.get("not_found_reason"),
                )
            return SynthesizerOutput(
                answer=text or "Jawaban dihasilkan dari dokumen.",
                statements=[],
                not_found_reason=None,
            )

        except Exception as e:
            logger.error(f"Synthesizer failed: {e}")
            return SynthesizerOutput(
                answer="Terjadi kesalahan saat memproses jawaban.",
                statements=[],
                not_found_reason=f"Error: {str(e)}",
            )

    async def synthesize_stream(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream synthesized answer tokens."""
        context_parts = []
        for chunk in chunks:
            chunk_id = chunk.get("id", chunk.get("payload", {}).get("chunk_id", "unknown"))
            content = chunk.get("payload", {}).get("content", chunk.get("content", ""))
            section = chunk.get("payload", {}).get("section_path", "")
            page = chunk.get("payload", {}).get("page_number", "?")
            context_parts.append(
                f"[chunk_id: {chunk_id}] (Page {page}, Section: {section})\n{content}"
            )

        context_str = "\n\n---\n\n".join(context_parts)
        history_str = "Tidak ada history."
        if history:
            history_str = "\n".join(
                f"{'User' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')[:300]}"
                for m in history[-5:]
            )

        system_prompt = SYNTHESIZER_SYSTEM_PROMPT.format(
            context=context_str, history=history_str,
        )

        async for token in groq_client.chat_stream(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0.0,
        ):
            yield token

# Singleton instance
synthesizer_agent = SynthesizerAgent()
