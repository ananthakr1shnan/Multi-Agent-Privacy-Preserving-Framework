"""
Workflow Engine - Custom DAG Orchestrator.
Manages the parallel execution of privacy shield, agents, and aggregation.
"""
import asyncio
import time
from typing import List, Callable, Any, AsyncGenerator
from datetime import datetime
from app.schemas.models import (
    TraceEvent, NodeType, AggregatedResult, PrivacyAnalysis, DomainAnalysis
)
from app.workflow.privacy_node import privacy_shield
from app.workflow.domain_expert_node import domain_expert
from app.workflow.retriever_node import retriever as context_retriever
from app.core.database import log_event
from app.workflow.agent_nodes import productivity_agent, ethics_agent, creativity_agent
from app.workflow.aggregator import aggregator


class WorkflowEngine:
    """
    Orchestrates the DAG execution: [Shield + Domain Expert] → [Agents] → Aggregator.
    Privacy Shield and Domain Expert run in parallel for efficiency.
    Emits trace events for real-time monitoring.
    """
    
    def __init__(self):
        self.trace_events: List[TraceEvent] = []
    
    async def execute(
        self,
        user_query: str,
        event_callback: Callable[[TraceEvent], Any] = None
    ) -> AggregatedResult:
        """
        Execute the complete workflow DAG.
        
        Args:
            user_query: Raw user input
            event_callback: Optional callback for real-time trace events
            
        Returns:
            AggregatedResult with final synthesized response
        """
        workflow_start = time.time()
        
        # Step 1: Privacy Shield + Domain Expert (Parallel Root Nodes)
        await self._emit_event(
            NodeType.PRIVACY_SHIELD,
            "started",
            "Analyzing query for PII...",
            event_callback
        )
        
        await self._emit_event(
            NodeType.DOMAIN_EXPERT,
            "started",
            "Domain Expert analyzing query context...",
            event_callback
        )
        
        # Execute Privacy Shield and Domain Expert in parallel
        async def run_privacy():
            privacy_start = time.time()
            result = privacy_shield.analyze_and_redact(user_query)
            privacy_time = (time.time() - privacy_start) * 1000
            await self._emit_event(
                NodeType.PRIVACY_SHIELD,
                "completed",
                f"Privacy analysis complete. {result.redaction_count} entities redacted.",
                event_callback,
                data={
                    "redaction_count": result.redaction_count,
                    "anonymized_query": result.anonymized_text,
                    "processing_time_ms": privacy_time
                }
            )
            return result
        
        async def run_domain_expert():
            # Domain expert analyzes the original query (before PII redaction)
            # This is safe because it runs locally
            domain_start = time.time()
            result = domain_expert.analyze_domain(user_query)
            await self._emit_event(
                NodeType.DOMAIN_EXPERT,
                "completed",
                f"Domain classified as '{result.predicted_domain}' (confidence: {result.confidence:.0%})",
                event_callback,
                data={
                    "predicted_domain": result.predicted_domain,
                    "confidence": result.confidence,
                    "is_high_sensitivity": result.is_high_sensitivity,
                    "processing_time_ms": result.processing_time_ms
                }
            )
            return result
        
        # Run both in parallel
        privacy_analysis, domain_analysis = await asyncio.gather(
            run_privacy(),
            run_domain_expert()
        )
        
        # Step 1.2: Context Retrieval (New)
        # We can run this in parallel with privacy/domain analysis or after
        # For simplicity, let's run it now to have it ready for agents
        await self._emit_event(
            NodeType.DOMAIN_EXPERT, # Using Domain Expert type as proxy since we don't have a specific retrieval node type enum yet
            "processing",
            "Retrieving relevant context...",
            event_callback
        )
        
        retrieved_context = []
        if context_retriever:
            # Retrieve based on the original query (or anonymized if stricter privacy needed)
            # Using original query for better context matching, as this is local only
            retrieved_context = context_retriever.retrieve(user_query)
            
        await self._emit_event(
            NodeType.DOMAIN_EXPERT,
            "completed",
            f"Retrieved {len(retrieved_context)} relevant context items.",
            event_callback,
            data={"retrieved_context": retrieved_context}
        )
        
        # Step 1.5: Adaptive Re-Redaction for High-Sensitivity Domains
        if domain_analysis.is_high_sensitivity and not privacy_analysis.aggressive_mode_triggered:
            await self._emit_event(
                NodeType.PRIVACY_SHIELD,
                "processing",
                f"Triggering aggressive mode for {domain_analysis.predicted_domain} domain...",
                event_callback
            )
            
            # Re-run privacy analysis with aggressive mode
            privacy_analysis = privacy_shield.analyze_and_redact(
                user_query,
                aggressive_mode=True,
                domain_context=domain_analysis.predicted_domain
            )
            
            await self._emit_event(
                NodeType.PRIVACY_SHIELD,
                "completed",
                f"Aggressive redaction complete ({privacy_analysis.redaction_count} redactions)",
                event_callback,
                data={
                    "redaction_count": privacy_analysis.redaction_count,
                    "anonymized_query": privacy_analysis.anonymized_text,
                    "redaction_strategy": privacy_analysis.redaction_strategy,
                    "aggressive_mode": True
                }
            )
        
        # Step 2: Parallel Agent Execution with Domain Context AND Retrieved Context
        anonymized_query = privacy_analysis.anonymized_text
        domain_context = domain_analysis.persona_directive
        
        await self._emit_event(
            NodeType.PRODUCTIVITY_AGENT,
            "started",
            "Productivity agent analyzing...",
            event_callback
        )
        
        await self._emit_event(
            NodeType.ETHICS_AGENT,
            "started",
            "Ethics agent evaluating...",
            event_callback
        )
        
        await self._emit_event(
            NodeType.CREATIVITY_AGENT,
            "started",
            "Creativity agent exploring...",
            event_callback
        )
        
        # Execute all agents in parallel with domain context
        agent_results = await asyncio.gather(
            productivity_agent.process(anonymized_query, domain_context, retrieved_context),
            ethics_agent.process(anonymized_query, domain_context, retrieved_context),
            creativity_agent.process(anonymized_query, domain_context, retrieved_context),
            return_exceptions=True
        )
        
        # Emit completion events for each agent
        for result in agent_results:
            if isinstance(result, Exception):
                continue
            
            await self._emit_event(
                result.agent_type,
                "completed",
                f"{result.agent_type.value.replace('_', ' ').title()} completed in {result.processing_time_ms:.0f}ms",
                event_callback,
                data={
                    "processing_time_ms": result.processing_time_ms,
                    "confidence": result.confidence,
                    "response_length": len(result.response)
                }
            )
        
        # Step 3: Aggregation (Sink Node)
        await self._emit_event(
            NodeType.AGGREGATOR,
            "started",
            "Synthesizing agent responses...",
            event_callback
        )
        
        total_time = (time.time() - workflow_start) * 1000
        
        final_result = await aggregator.synthesize(
            agent_responses=[r for r in agent_results if not isinstance(r, Exception)],
            privacy_analysis=privacy_analysis,
            domain_analysis=domain_analysis,
            total_processing_time_ms=total_time
        )
        
        # Add retrieved context to final result
        final_result.retrieved_context = retrieved_context
        
        # Audit Logging (New)
        audit_id = log_event(final_result, user_query) # Log the full event
        final_result.audit_id = audit_id
        
        await self._emit_event(
            NodeType.AGGREGATOR,
            "completed",
            f"Final response generated in {total_time:.0f}ms. Audit ID: {audit_id}",
            event_callback,
            data={
                "total_processing_time_ms": total_time,
                "agent_contributions": final_result.agent_contributions,
                "audit_id": audit_id
            }
        )
        
        return final_result
    
    async def _emit_event(
        self,
        node_type: NodeType,
        status: str,
        message: str,
        callback: Callable = None,
        data: dict = None
    ):
        """Emit a trace event and optionally invoke callback"""
        event = TraceEvent(
            node_type=node_type,
            status=status,
            message=message,
            timestamp=datetime.now(),
            data=data
        )
        
        self.trace_events.append(event)
        
        if callback:
            await callback(event)


# Global workflow engine instance
workflow_engine = WorkflowEngine()
