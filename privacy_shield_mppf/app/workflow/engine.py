"""
Workflow Engine - Custom DAG Orchestrator.
Manages the parallel execution of privacy shield, agents, and aggregation.
"""
import asyncio
import time
from typing import List, Callable, Any, AsyncGenerator
from datetime import datetime
from app.schemas.models import (
    TraceEvent, NodeType, AggregatedResult, PrivacyAnalysis
)
from app.workflow.privacy_node import privacy_shield
from app.workflow.agent_nodes import productivity_agent, ethics_agent, creativity_agent
from app.workflow.aggregator import aggregator


class WorkflowEngine:
    """
    Orchestrates the DAG execution: Shield → [Agents] → Aggregator.
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
        
        # Step 1: Privacy Shield (Root Node)
        await self._emit_event(
            NodeType.PRIVACY_SHIELD,
            "started",
            "Analyzing query for PII...",
            event_callback
        )
        
        privacy_start = time.time()
        privacy_analysis = privacy_shield.analyze_and_redact(user_query)
        privacy_time = (time.time() - privacy_start) * 1000
        
        await self._emit_event(
            NodeType.PRIVACY_SHIELD,
            "completed",
            f"Privacy analysis complete. {privacy_analysis.redaction_count} entities redacted.",
            event_callback,
            data={
                "redaction_count": privacy_analysis.redaction_count,
                "anonymized_query": privacy_analysis.anonymized_text,
                "processing_time_ms": privacy_time
            }
        )
        
        # Step 2: Parallel Agent Execution
        anonymized_query = privacy_analysis.anonymized_text
        
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
        
        # Execute all agents in parallel
        agent_results = await asyncio.gather(
            productivity_agent.process(anonymized_query),
            ethics_agent.process(anonymized_query),
            creativity_agent.process(anonymized_query),
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
        
        final_result = aggregator.synthesize(
            agent_responses=[r for r in agent_results if not isinstance(r, Exception)],
            privacy_analysis=privacy_analysis,
            total_processing_time_ms=total_time
        )
        
        await self._emit_event(
            NodeType.AGGREGATOR,
            "completed",
            f"Final response generated in {total_time:.0f}ms",
            event_callback,
            data={
                "total_processing_time_ms": total_time,
                "agent_contributions": final_result.agent_contributions
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
