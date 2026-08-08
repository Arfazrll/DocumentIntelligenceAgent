"""
DocIntel AI — Refusal Handler.

Generates informative refusal messages when confidence is too low.
"""

import logging

logger = logging.getLogger(__name__)

class RefusalHandler:
    """Handles refusal responses when system cannot confidently answer."""

    REFUSAL_TEMPLATES = {
        "low_retrieval": (
            "Tidak ada informasi relevan yang ditemukan di dokumen untuk pertanyaan ini. "
            "Silakan pastikan pertanyaan Anda terkait dengan isi dokumen yang telah diunggah."
        ),
        "not_supported": (
            "Tidak dapat memverifikasi jawaban dari dokumen yang tersedia. "
            "Informasi yang dibutuhkan mungkin tidak ada di dokumen ini."
        ),
        "low_confidence": (
            "Tingkat kepercayaan terlalu rendah untuk memberikan jawaban yang akurat. "
            "Silakan spesifikkan pertanyaan Anda atau berikan konteks tambahan."
        ),
        "ambiguous": (
            "Pertanyaan ini ambigu. {clarification_question}"
        ),
        "out_of_scope": (
            "Pertanyaan ini di luar cakupan dokumen yang tersedia. "
            "Sistem ini hanya menjawab berdasarkan dokumen yang telah diunggah."
        ),
    }

    def generate_refusal(
        self,
        reason: str,
        available_topics: list[str] | None = None,
        clarification_question: str | None = None,
    ) -> str:
        """
        Generate an informative refusal message.

        Args:
            reason: Refusal reason key.
            available_topics: Topics that ARE available in the documents.
            clarification_question: Specific clarification to ask.
        """
        message = self.REFUSAL_TEMPLATES.get(reason, self.REFUSAL_TEMPLATES["low_confidence"])

        if reason == "ambiguous" and clarification_question:
            message = message.format(clarification_question=clarification_question)

        # Add available topic suggestions
        if available_topics:
            topics_str = ", ".join(available_topics[:5])
            message += f"\n\nTopik yang tersedia di dokumen: {topics_str}."

        return message

# Singleton instance
refusal_handler = RefusalHandler()
