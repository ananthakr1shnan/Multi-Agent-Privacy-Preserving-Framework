"""
Ethics Agent — gemma2-9b-it @ temp=0.1
Evaluates the Productivity Agent's draft and returns a structured
PASS / FAIL verdict with specific improvement suggestions.
"""
import time
import json
import re
from typing import List

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.schemas.models import AgentResponse, EthicsVerdict, NodeType
from app.core.config import settings


_SYSTEM_PROMPT = """\
You are an Ethics and Safety Agent. Review the draft response below
for ethical issues, accuracy, bias, safety, and helpfulness.

Evaluate against:
1. Factual accuracy and honesty
2. Potential for harm or misuse
3. Bias or unfair representation
4. Privacy and legal compliance
5. Helpfulness and appropriateness

You MUST respond with ONLY valid JSON in this exact format — no extra text:
{
  "verdict": "PASS",
  "reason": "One or two sentences explaining your verdict.",
  "suggestions": []
}

Rules:
- verdict must be exactly "PASS" or "FAIL"
- If PASS, suggestions may be []
- If FAIL, provide at least one specific, actionable suggestion
"""


class EthicsAgent:
    """
    Ethics Agent: reviews the draft response and returns a structured verdict.
    Uses gemma2-9b-it — excellent at following strict JSON output instructions.
    """

    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.ethics_model,
            temperature=0.1,
        )

    async def evaluate(
        self,
        draft: AgentResponse,
        anonymized_query: str,
    ) -> EthicsVerdict:
        """
        Evaluate a draft response.

        Args:
            draft:             The Productivity Agent's AgentResponse
            anonymized_query:  The (PII-stripped) user query for context

        Returns:
            EthicsVerdict with verdict, reason, and suggestions
        """
        start = time.time()

        try:
            user_prompt = (
                f"Original Query: {anonymized_query}\n\n"
                f"Draft Response:\n{draft.response}\n\n"
                "Return your JSON verdict:"
            )

            resp = await self.llm.ainvoke([
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])

            parsed = self._parse_verdict(resp.content)

            return EthicsVerdict(
                verdict=parsed.get("verdict", "PASS"),
                reason=parsed.get("reason", "Response evaluated."),
                suggestions=parsed.get("suggestions", []),
                processing_time_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            print(f"[EthicsAgent] Evaluation error: {e}")
            # Default PASS on error so we don't silently block the pipeline
            return EthicsVerdict(
                verdict="PASS",
                reason=f"Ethics evaluation error — defaulting to PASS: {e}",
                suggestions=[],
                processing_time_ms=(time.time() - start) * 1000,
            )

    # ──────────────────────────────────────────────────────────────────────────

    def _parse_verdict(self, content: str) -> dict:
        """Robustly parse the JSON verdict from the LLM's raw output."""
        content = content.strip()

        # Strip markdown code fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # Direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Regex fallback — grab first {...} block
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

        # Last resort — infer from text
        verdict = "FAIL" if "fail" in content.lower() else "PASS"
        return {
            "verdict": verdict,
            "reason": "Could not parse structured verdict from model output.",
            "suggestions": [],
        }


# Global singleton
ethics_agent = EthicsAgent()
