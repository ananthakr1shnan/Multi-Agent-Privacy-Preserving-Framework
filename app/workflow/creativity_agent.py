"""
Creativity Agent — llama-3.3-70b-versatile @ temp=0.9
Performs DuckDuckGo web search (when domain allows) and synthesises
a Creative Brief that the Productivity Agent uses to draft the response.
"""
import time
import json
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.schemas.models import CreativeBrief, SearchResult, DomainAnalysis
from app.workflow.web_search import web_search_tool
from app.core.config import settings


_SEARCH_QUERY_PROMPT = (
    "You are a search-query optimizer. "
    "Given a user question and its domain, output ONE precise web-search query "
    "that will find the most relevant and up-to-date information. "
    "Respond with ONLY the search query — no explanation, no quotes."
)

_SYNTHESIZE_PROMPT = """\
You are a Creative Research Agent. Synthesise the provided web-search results
and knowledge-base context into a Creative Brief for another agent.

Your output MUST be valid JSON with this exact structure:
{
  "ideas":      ["idea 1", "idea 2", "idea 3"],
  "key_angles": ["angle 1", "angle 2"],
  "synthesis":  "One paragraph summarising the most important insights."
}

Be creative, insightful, and divergent. Prefer concrete, actionable ideas.
"""


class CreativityAgent:
    """
    Creativity Agent: optionally searches the web with DuckDuckGo,
    then uses llama-3.3-70b-versatile to produce a Creative Brief.
    """

    def __init__(self):
        # Primary LLM — large, creative
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.creativity_model,
            temperature=0.9,
        )
        # Small/fast model just for generating search queries
        self.query_llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.3,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────────

    async def process(
        self,
        anonymized_query: str,
        domain_analysis: DomainAnalysis,
        retrieved_context: List[str],
    ) -> CreativeBrief:
        """
        Run web search (if allowed) then synthesise a Creative Brief.

        Args:
            anonymized_query:   PII-redacted user query
            domain_analysis:    Output from the Domain Expert node
            retrieved_context:  KB chunks from ChromaDB

        Returns:
            CreativeBrief consumed by the Productivity Agent
        """
        start = time.time()
        search_results: List[SearchResult] = []
        search_performed = False
        search_query_used: Optional[str] = None

        # ── Step 1: Web search (domain-gated) ─────────────────────────────────
        if web_search_tool.is_search_allowed(domain_analysis.predicted_domain):
            search_query_used = await self._generate_search_query(
                anonymized_query, domain_analysis.predicted_domain
            )
            raw_results = web_search_tool.search(
                search_query_used,
                max_results=settings.web_search_max_results,
            )
            search_results = [
                SearchResult(
                    title=r["title"],
                    snippet=r["snippet"],
                    url=r["url"],
                )
                for r in raw_results
            ]
            search_performed = bool(search_results)

        # ── Step 2: Synthesise Creative Brief ─────────────────────────────────
        ideas, key_angles, synthesis = await self._synthesize(
            anonymized_query,
            search_results,
            retrieved_context,
            domain_analysis.predicted_domain,
        )

        return CreativeBrief(
            ideas=ideas,
            key_angles=key_angles,
            synthesis=synthesis,
            search_results=search_results,
            search_performed=search_performed,
            search_query_used=search_query_used,
            processing_time_ms=(time.time() - start) * 1000,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _generate_search_query(self, query: str, domain: str) -> str:
        """Use a fast LLM to craft an optimised search query."""
        try:
            resp = await self.query_llm.ainvoke([
                SystemMessage(content=_SEARCH_QUERY_PROMPT),
                HumanMessage(content=f"Domain: {domain}\nUser question: {query}\nSearch query:"),
            ])
            return resp.content.strip().strip('"').strip("'")
        except Exception as e:
            print(f"[CreativityAgent] Search-query generation failed: {e}")
            return query  # Fall back to raw query

    async def _synthesize(
        self,
        query: str,
        search_results: List[SearchResult],
        kb_context: List[str],
        domain: str,
    ):
        """Synthesise search + KB context into structured Creative Brief."""
        # Build prompt sections
        search_block = ""
        if search_results:
            lines = ["\nWEB SEARCH RESULTS:"]
            for i, r in enumerate(search_results, 1):
                lines.append(f"{i}. {r.title}\n   {r.snippet}\n   Source: {r.url}")
            search_block = "\n".join(lines)

        kb_block = ""
        if kb_context:
            kb_block = "\nKNOWLEDGE BASE CONTEXT:\n" + "\n".join(
                f"- {c}" for c in kb_context
            )

        user_prompt = (
            f"Domain: {domain}\n"
            f"User question: {query}"
            f"{search_block}"
            f"{kb_block}\n\n"
            "Generate the Creative Brief JSON:"
        )

        try:
            resp = await self.llm.ainvoke([
                SystemMessage(content=_SYNTHESIZE_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            content = resp.content.strip()

            # Strip markdown fences if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            return (
                parsed.get("ideas", ["Provide a comprehensive response"]),
                parsed.get("key_angles", ["Practical", "Informative"]),
                parsed.get("synthesis", ""),
            )
        except Exception as e:
            print(f"[CreativityAgent] Synthesis failed: {e}")
            return (
                ["Provide a comprehensive and helpful response"],
                ["Practical", "Informative"],
                "",
            )


# Global singleton
creativity_agent = CreativityAgent()
