"""
Productivity Agent — llama-3.1-8b-instant @ temp=0.5
Receives the Creative Brief from the Creativity Agent and generates
a structured draft response. On retries, incorporates Aggregator feedback.
"""
import time
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.schemas.models import AgentResponse, CreativeBrief, NodeType
from app.core.config import settings


_SYSTEM_PROMPT = """\
You are a Productivity Agent. Your job is to write a clear, accurate, and
well-structured response to the user's query.

You will receive:
- A Creative Brief with ideas, research angles, and web search results
- (Optionally) Knowledge base context
- (On retries) Specific feedback from the Aggregator that you MUST address

Guidelines:
1. Directly answer the user's query — be concrete and practical.
2. Incorporate the best ideas from the Creative Brief.
3. When web sources are provided, cite them inline as [Title](URL).
4. If Aggregator feedback is present, explicitly address every point raised.
5. Use clear structure: short paragraphs or bullet points where appropriate.
"""


class ProductivityAgent:
    """
    Productivity Agent: drafts the main response using the Creative Brief.
    Uses llama-3.1-8b-instant for speed and focused output.
    """

    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.productivity_model,
            temperature=0.5,
        )

    async def process(
        self,
        anonymized_query: str,
        creative_brief: CreativeBrief,
        retrieved_context: List[str],
        domain_context: Optional[str] = None,
        aggregator_feedback: Optional[str] = None,
    ) -> AgentResponse:
        """
        Generate a draft response.

        Args:
            anonymized_query:    PII-redacted user query
            creative_brief:      Output from the Creativity Agent
            retrieved_context:   KB chunks from ChromaDB
            domain_context:      Domain persona directive
            aggregator_feedback: On retry — specific issues to fix

        Returns:
            AgentResponse with the draft text
        """
        start = time.time()

        try:
            system_prompt = _SYSTEM_PROMPT
            if domain_context:
                system_prompt = f"{domain_context}\n\n{system_prompt}"

            user_prompt = (
                f"User Query: {anonymized_query}\n\n"
                f"{self._format_brief(creative_brief)}"
                f"{self._format_feedback(aggregator_feedback)}"
                "\n\nWrite your response:"
            )

            resp = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])

            return AgentResponse(
                agent_type=NodeType.PRODUCTIVITY_AGENT,
                response=resp.content,
                confidence=0.85,
                processing_time_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return AgentResponse(
                agent_type=NodeType.PRODUCTIVITY_AGENT,
                response=f"Error generating draft: {str(e)}",
                confidence=0.0,
                processing_time_ms=(time.time() - start) * 1000,
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _format_brief(self, brief: CreativeBrief) -> str:
        parts = []

        if brief.ideas:
            parts.append(
                "CREATIVE IDEAS:\n" + "\n".join(f"• {i}" for i in brief.ideas)
            )
        if brief.key_angles:
            parts.append(
                "KEY ANGLES:\n" + "\n".join(f"• {a}" for a in brief.key_angles)
            )
        if brief.synthesis:
            parts.append(f"RESEARCH SYNTHESIS:\n{brief.synthesis}")

        if brief.search_results:
            lines = ["WEB SOURCES (cite relevant URLs inline):"]
            for r in brief.search_results:
                lines.append(f"• [{r.title}]({r.url})\n  {r.snippet}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts) if parts else "No creative brief provided."

    def _format_feedback(self, feedback: Optional[str]) -> str:
        if not feedback:
            return ""
        return (
            "\n\n⚠️  AGGREGATOR FEEDBACK — you MUST address these issues:\n"
            + feedback
        )


# Global singleton
productivity_agent = ProductivityAgent()
