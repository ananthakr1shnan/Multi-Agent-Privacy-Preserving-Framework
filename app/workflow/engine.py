"""
Workflow Engine — Sequential Multi-Agent DAG Orchestrator.

Pipeline (per request):
  1. [Parallel] Privacy Shield + Domain Expert
  2. [Parallel] KB Retrieval
  3. Creativity Agent  (DuckDuckGo web search if domain allows)
       ↓ Creative Brief
  4. Productivity Agent  (draft response)
       ↓ Draft Response
  5. Ethics Agent  (PASS / FAIL verdict)
       ↓ Verdict
  6. Aggregator / Judge  (ACCEPT / RETRY / FORCE_ACCEPT)
       ↓ if RETRY → back to step 4 (max settings.max_ethics_retries times)
  7. Audit Logger + SSE stream
"""
import asyncio
import time
from typing import Callable, Any, Optional
from datetime import datetime

from app.schemas.models import (
    TraceEvent, NodeType, AggregatedResult,
)
from app.workflow.privacy_node import privacy_shield
from app.workflow.domain_expert_node import domain_expert
from app.workflow.retriever_node import retriever as context_retriever
from app.workflow.web_search import web_search_tool
from app.workflow.creativity_agent import creativity_agent
from app.workflow.productivity_agent import productivity_agent
from app.workflow.ethics_agent import ethics_agent
from app.workflow.aggregator import aggregator
from app.core.database import log_event
from app.core.config import settings


class WorkflowEngine:
    """
    Orchestrates the sequential multi-agent pipeline.
    Emits SSE TraceEvents at every phase transition.
    """

    def __init__(self):
        self.trace_events = []

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────────────────────────────────

    async def execute(
        self,
        user_query: str,
        event_callback: Optional[Callable[[TraceEvent], Any]] = None,
    ) -> AggregatedResult:
        """
        Execute the full pipeline for a single user query.

        Args:
            user_query:      Raw user input (may contain PII)
            event_callback:  Optional async callback for SSE events

        Returns:
            AggregatedResult with final response and all metadata
        """
        workflow_start = time.time()

        # ── Phase 1: Privacy Shield + Domain Expert (parallel, local) ─────────
        await self._emit(NodeType.PRIVACY_SHIELD, "started",
                         "Analyzing query for PII...", event_callback)
        await self._emit(NodeType.DOMAIN_EXPERT, "started",
                         "Classifying query domain...", event_callback)

        privacy_analysis, domain_analysis = await asyncio.gather(
            self._run_privacy(user_query, event_callback),
            self._run_domain_expert(user_query, event_callback),
        )

        # Adaptive re-redaction for high-sensitivity domains
        if domain_analysis.is_high_sensitivity and not privacy_analysis.aggressive_mode_triggered:
            await self._emit(NodeType.PRIVACY_SHIELD, "processing",
                             f"High-sensitivity domain — triggering aggressive redaction...",
                             event_callback)
            privacy_analysis = privacy_shield.analyze_and_redact(
                user_query,
                aggressive_mode=True,
                domain_context=domain_analysis.predicted_domain,
            )
            await self._emit(NodeType.PRIVACY_SHIELD, "completed",
                             f"Aggressive redaction: {privacy_analysis.redaction_count} entities redacted.",
                             event_callback,
                             data={"redaction_count": privacy_analysis.redaction_count,
                                   "anonymized_query": privacy_analysis.anonymized_text,
                                   "aggressive_mode": True})

        anonymized_query = privacy_analysis.anonymized_text
        domain_context = domain_analysis.persona_directive

        # ── Phase 2: KB Retrieval ─────────────────────────────────────────────
        await self._emit(NodeType.DOMAIN_EXPERT, "processing",
                         "Retrieving relevant context from knowledge base...",
                         event_callback)

        retrieved_context = []
        if context_retriever:
            retrieved_context = context_retriever.retrieve(user_query)

        await self._emit(NodeType.DOMAIN_EXPERT, "completed",
                         f"Retrieved {len(retrieved_context)} context chunk(s).",
                         event_callback,
                         data={"retrieved_context": retrieved_context})

        # ── Phase 3: Creativity Agent (web search + brief) ────────────────────
        await self._emit(NodeType.CREATIVITY_AGENT, "started",
                         "Creativity Agent starting...", event_callback)

        if domain_analysis.is_high_sensitivity or \
                not web_search_tool.is_search_allowed(domain_analysis.predicted_domain):
            await self._emit(NodeType.WEB_SEARCH, "processing",
                             f"Web search skipped for {domain_analysis.predicted_domain} domain.",
                             event_callback)
        else:
            await self._emit(NodeType.WEB_SEARCH, "started",
                             "Searching the web for fresh ideas...", event_callback)

        creative_brief = await creativity_agent.process(
            anonymized_query, domain_analysis, retrieved_context
        )

        if creative_brief.search_performed:
            await self._emit(NodeType.WEB_SEARCH, "completed",
                             f"Web search complete — {len(creative_brief.search_results)} result(s) retrieved.",
                             event_callback,
                             data={"search_query": creative_brief.search_query_used,
                                   "results_count": len(creative_brief.search_results)})

        await self._emit(NodeType.CREATIVITY_AGENT, "completed",
                         f"Creative brief ready ({len(creative_brief.ideas)} idea(s)).",
                         event_callback,
                         data={"ideas_count": len(creative_brief.ideas),
                               "search_performed": creative_brief.search_performed,
                               "processing_time_ms": creative_brief.processing_time_ms})

        # ── Phase 4-6: Productivity → Ethics → Judge (retry loop) ────────────
        retry_count = 0
        aggregator_feedback = None
        draft = None
        ethics_verdict = None
        decision = None

        while retry_count <= settings.max_ethics_retries:
            # ── Productivity Agent ─────────────────────────────────────────────
            retry_label = f" (retry {retry_count}/{settings.max_ethics_retries})" \
                          if retry_count > 0 else ""
            await self._emit(NodeType.PRODUCTIVITY_AGENT, "started",
                             f"Productivity Agent drafting response{retry_label}...",
                             event_callback)

            draft = await productivity_agent.process(
                anonymized_query,
                creative_brief,
                retrieved_context,
                domain_context=domain_context,
                aggregator_feedback=aggregator_feedback,
            )

            await self._emit(NodeType.PRODUCTIVITY_AGENT, "completed",
                             f"Draft generated in {draft.processing_time_ms:.0f}ms.",
                             event_callback,
                             data={"processing_time_ms": draft.processing_time_ms,
                                   "response_length": len(draft.response),
                                   "retry_count": retry_count})

            # ── Ethics Agent ───────────────────────────────────────────────────
            await self._emit(NodeType.ETHICS_AGENT, "started",
                             "Ethics Agent reviewing draft...", event_callback)

            ethics_verdict = await ethics_agent.evaluate(draft, anonymized_query)

            await self._emit(NodeType.ETHICS_AGENT, "completed",
                             f"Ethics verdict: {ethics_verdict.verdict} — {ethics_verdict.reason}",
                             event_callback,
                             data={"verdict": ethics_verdict.verdict,
                                   "reason": ethics_verdict.reason,
                                   "suggestions": ethics_verdict.suggestions,
                                   "processing_time_ms": ethics_verdict.processing_time_ms})

            # ── Aggregator / Judge ─────────────────────────────────────────────
            await self._emit(NodeType.AGGREGATOR, "started",
                             "Aggregator judging response...", event_callback)

            decision = await aggregator.judge(
                draft, ethics_verdict, retry_count, domain_analysis
            )

            await self._emit(NodeType.AGGREGATOR, "completed",
                             f"Decision: {decision.action}{retry_label}",
                             event_callback,
                             data={"action": decision.action,
                                   "reasoning": decision.reasoning,
                                   "retry_count": retry_count})

            if decision.action in ("ACCEPT", "FORCE_ACCEPT"):
                break   # Pipeline complete

            # RETRY — pass feedback back to Productivity Agent
            aggregator_feedback = decision.feedback
            retry_count += 1

        # ── Phase 7: Build final result + audit log ───────────────────────────
        total_time = (time.time() - workflow_start) * 1000

        final_result = await aggregator.build_final_result(
            draft=draft,
            creative_brief=creative_brief,
            ethics_verdict=ethics_verdict,
            decision=decision,
            privacy_analysis=privacy_analysis,
            domain_analysis=domain_analysis,
            retrieved_context=retrieved_context,
            total_time_ms=total_time,
            retry_count=retry_count,
        )

        audit_id = log_event(final_result, user_query)
        final_result.audit_id = audit_id

        await self._emit(NodeType.AGGREGATOR, "completed",
                         f"Pipeline complete in {total_time:.0f}ms. Audit ID: {audit_id}",
                         event_callback,
                         data={"total_processing_time_ms": total_time,
                               "audit_id": audit_id,
                               "retry_count": retry_count,
                               "final_action": decision.action})

        return final_result

    # ──────────────────────────────────────────────────────────────────────────
    # Phase runners (used for parallel gather calls)
    # ──────────────────────────────────────────────────────────────────────────

    async def _run_privacy(self, user_query: str, callback):
        result = privacy_shield.analyze_and_redact(user_query)
        await self._emit(NodeType.PRIVACY_SHIELD, "completed",
                         f"Privacy shield: {result.redaction_count} entity/entities redacted.",
                         callback,
                         data={"redaction_count": result.redaction_count,
                               "anonymized_query": result.anonymized_text})
        return result

    async def _run_domain_expert(self, user_query: str, callback):
        result = domain_expert.analyze_domain(user_query)
        await self._emit(NodeType.DOMAIN_EXPERT, "completed",
                         f"Domain: '{result.predicted_domain}' "
                         f"(confidence: {result.confidence:.0%}, "
                         f"high-sensitivity: {result.is_high_sensitivity})",
                         callback,
                         data={"predicted_domain": result.predicted_domain,
                               "confidence": result.confidence,
                               "is_high_sensitivity": result.is_high_sensitivity,
                               "processing_time_ms": result.processing_time_ms})
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # SSE event emitter
    # ──────────────────────────────────────────────────────────────────────────

    async def _emit(
        self,
        node_type: NodeType,
        status: str,
        message: str,
        callback: Optional[Callable] = None,
        data: dict = None,
    ):
        event = TraceEvent(
            node_type=node_type,
            status=status,
            message=message,
            timestamp=datetime.now(),
            data=data,
        )
        self.trace_events.append(event)
        if callback:
            await callback(event)


# Global singleton
workflow_engine = WorkflowEngine()
