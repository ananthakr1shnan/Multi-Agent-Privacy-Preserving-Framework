"""
Response Aggregator / Judge — llama-3.3-70b-versatile @ temp=0.2
(Official Groq replacement for deepseek-r1-distill-llama-70b)
Decides ACCEPT, RETRY, or FORCE_ACCEPT based on the Ethics Agent verdict.
On RETRY, produces specific feedback for the Productivity Agent.
"""
import time
import json
import re
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.schemas.models import (
    AgentResponse, EthicsVerdict, AggregatorDecision,
    AggregatedResult, PrivacyAnalysis, DomainAnalysis,
    DifferentialPrivacyMetrics, CreativeBrief,
)
from app.privacy import dp_layer
from app.core.config import settings


_JUDGE_PROMPT = """\
You are the Lead Aggregator and Judge for a Privacy-Preserving AI Framework.

A Productivity Agent has written a draft response, and an Ethics Agent has
reviewed it. Your job is to make a final decision.

Decision options:
- ACCEPT       : Ethics passed, or issues are minor. Use the draft as-is.
- RETRY        : Ethics failed significantly. Send the draft back with specific
                 feedback so the Productivity Agent can fix it.
- FORCE_ACCEPT : Maximum retries reached — accept despite ethics concerns,
                 and note the caveats.

Respond ONLY with valid JSON (no extra text):
{
  "action":    "ACCEPT" | "RETRY" | "FORCE_ACCEPT",
  "reasoning": "Your chain-of-thought reasoning (2–4 sentences).",
  "feedback":  "Specific, actionable instructions for the Productivity Agent.
                Required when action is RETRY; null otherwise."
}
"""


class ResponseAggregator:
    """
    Judge Aggregator using deepseek-r1-distill-llama-70b.
    Also applies Differential Privacy metrics for audit transparency.
    """

    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.aggregator_model,
            temperature=0.2,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Judge interface
    # ──────────────────────────────────────────────────────────────────────────

    async def judge(
        self,
        draft: AgentResponse,
        ethics_verdict: EthicsVerdict,
        retry_count: int,
        domain_analysis: Optional[DomainAnalysis] = None,
    ) -> AggregatorDecision:
        """
        Decide whether to ACCEPT, RETRY, or FORCE_ACCEPT the draft.

        Args:
            draft:           Productivity Agent's draft response
            ethics_verdict:  Ethics Agent's structured verdict
            retry_count:     Current number of retries so far
            domain_analysis: Domain context (affects sensitivity weighting)

        Returns:
            AggregatorDecision with action + optional feedback
        """
        # Fast-path: Ethics passed → always ACCEPT
        if ethics_verdict.verdict == "PASS":
            return AggregatorDecision(
                action="ACCEPT",
                reasoning="Ethics Agent approved the response.",
                feedback=None,
                retry_count=retry_count,
            )

        # Fast-path: Max retries exhausted → FORCE_ACCEPT
        if retry_count >= settings.max_ethics_retries:
            return AggregatorDecision(
                action="FORCE_ACCEPT",
                reasoning=(
                    f"Maximum retries ({settings.max_ethics_retries}) reached. "
                    "Force-accepting with an ethics warning."
                ),
                feedback=None,
                retry_count=retry_count,
            )

        # Ethics failed and retries remain → ask DeepSeek to judge
        return await self._llm_judge(draft, ethics_verdict, retry_count, domain_analysis)

    # ──────────────────────────────────────────────────────────────────────────
    # Synthesise final output (called by engine after ACCEPT/FORCE_ACCEPT)
    # ──────────────────────────────────────────────────────────────────────────

    async def build_final_result(
        self,
        draft: AgentResponse,
        creative_brief: CreativeBrief,
        ethics_verdict: EthicsVerdict,
        decision: AggregatorDecision,
        privacy_analysis: PrivacyAnalysis,
        domain_analysis: Optional[DomainAnalysis],
        retrieved_context: list,
        total_time_ms: float,
        retry_count: int,
    ) -> AggregatedResult:
        """Assemble the AggregatedResult from all pipeline outputs."""
        # Apply DP noise for audit transparency
        base_weights = {"creativity_agent": 0.5, "productivity_agent": 0.3, "ethics_agent": 0.2}
        noisy_weights = dp_layer.apply_noise_to_scores(base_weights, sensitivity=0.01)

        # Enforce a minimum floor (5%) so no agent vanishes from the chart,
        # then renormalize so weights always sum to 1.0
        min_floor = 0.05
        floored = {k: max(min_floor, v) for k, v in noisy_weights.items()}
        total = sum(floored.values())
        noisy_weights = {k: round(v / total, 4) for k, v in floored.items()}

        dp_layer.increment_query_count()
        dp_raw = dp_layer.get_metrics()
        dp_metrics = DifferentialPrivacyMetrics(
            epsilon_budget=dp_raw.epsilon_budget,
            budget_used=dp_raw.budget_used,
            budget_remaining=dp_raw.budget_remaining,
            noise_scale=dp_raw.noise_scale,
            privacy_guarantee=dp_raw.privacy_guarantee,
            queries_processed=dp_raw.queries_processed,
        )

        # Append ethics warning if force-accepted
        final_text = draft.response
        if decision.action == "FORCE_ACCEPT":
            final_text += (
                "\n\n---\n⚠️ **Ethics Notice**: This response was accepted after "
                f"{retry_count} revision attempt(s). "
                f"Ethics concern: {ethics_verdict.reason}"
            )

        return AggregatedResult(
            final_response=final_text,
            creative_brief=creative_brief,
            ethics_verdict=ethics_verdict,
            aggregator_decision=decision,
            retry_count=retry_count,
            total_processing_time_ms=total_time_ms,
            privacy_analysis=privacy_analysis,
            domain_analysis=domain_analysis,
            retrieved_context=retrieved_context,
            dp_metrics=dp_metrics,
            agent_responses=[draft],
            agent_contributions=noisy_weights,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _llm_judge(
        self,
        draft: AgentResponse,
        ethics_verdict: EthicsVerdict,
        retry_count: int,
        domain_analysis: Optional[DomainAnalysis],
    ) -> AggregatorDecision:
        """Call DeepSeek to decide RETRY vs a borderline ACCEPT."""
        sensitivity_note = ""
        if domain_analysis and domain_analysis.is_high_sensitivity:
            sensitivity_note = (
                f"\nNote: This is a HIGH-SENSITIVITY domain "
                f"({domain_analysis.predicted_domain}). "
                "Apply stricter standards."
            )

        user_prompt = (
            f"Retry attempt: {retry_count}/{settings.max_ethics_retries}"
            f"{sensitivity_note}\n\n"
            f"Draft Response:\n{draft.response}\n\n"
            f"Ethics Verdict: {ethics_verdict.verdict}\n"
            f"Ethics Reason: {ethics_verdict.reason}\n"
            f"Suggestions: {', '.join(ethics_verdict.suggestions) if ethics_verdict.suggestions else 'None'}\n\n"
            "Make your decision as JSON:"
        )

        try:
            resp = await self.llm.ainvoke([
                SystemMessage(content=_JUDGE_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            parsed = self._parse_decision(resp.content)
            return AggregatorDecision(
                action=parsed.get("action", "RETRY"),
                reasoning=parsed.get("reasoning", ""),
                feedback=parsed.get("feedback"),
                retry_count=retry_count,
            )
        except Exception as e:
            print(f"[Aggregator] LLM judge error: {e}")
            # Safe fallback: retry with the ethics suggestions as feedback
            return AggregatorDecision(
                action="RETRY",
                reasoning="Aggregator encountered an error; defaulting to RETRY.",
                feedback="; ".join(ethics_verdict.suggestions) or ethics_verdict.reason,
                retry_count=retry_count,
            )

    def _parse_decision(self, content: str) -> dict:
        """Robustly parse the JSON decision from the LLM's raw output."""
        content = content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

        # Text fallback
        action = "ACCEPT" if "accept" in content.lower() else "RETRY"
        return {"action": action, "reasoning": content[:300], "feedback": None}


# Global singleton
aggregator = ResponseAggregator()
