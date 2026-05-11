"""
Pydantic models for request/response schemas and trace events.
Updated for the sequential multi-agent pipeline.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    """Types of workflow nodes"""
    PRIVACY_SHIELD = "privacy_shield"
    DOMAIN_EXPERT = "domain_expert"
    CREATIVITY_AGENT = "creativity_agent"
    WEB_SEARCH = "web_search"
    PRODUCTIVITY_AGENT = "productivity_agent"
    ETHICS_AGENT = "ethics_agent"
    AGGREGATOR = "aggregator"


# ── Request / Response ─────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """User query request"""
    query: str = Field(..., min_length=1, description="User's input query")


# ── Privacy ────────────────────────────────────────────────────────────────────

class PrivacyAnalysis(BaseModel):
    """Privacy analysis result showing PII detection"""
    original_text: str
    anonymized_text: str
    entities_found: List[Dict[str, Any]]
    redaction_count: int
    aggressive_mode_triggered: bool = False
    redaction_strategy: str = "standard"


# ── Domain ─────────────────────────────────────────────────────────────────────

class DomainAnalysis(BaseModel):
    """Domain expert analysis result"""
    predicted_domain: str
    confidence: float = Field(ge=0.0, le=1.0)
    persona_directive: str
    processing_time_ms: float
    is_high_sensitivity: bool = False


# ── Differential Privacy ───────────────────────────────────────────────────────

class DifferentialPrivacyMetrics(BaseModel):
    """Differential Privacy metrics for transparency"""
    epsilon_budget: float
    budget_used: float
    budget_remaining: float
    noise_scale: float
    privacy_guarantee: str
    queries_processed: int


# ── Creative Brief (Creativity Agent output) ───────────────────────────────────

class SearchResult(BaseModel):
    """A single web search result"""
    title: str
    snippet: str
    url: str


class CreativeBrief(BaseModel):
    """Output of the Creativity Agent — passed to Productivity Agent"""
    ideas: List[str]
    key_angles: List[str]
    synthesis: str = ""
    search_results: List[SearchResult] = []
    search_performed: bool = False
    search_query_used: Optional[str] = None
    processing_time_ms: float = 0.0


# ── Ethics Verdict (Ethics Agent output) ──────────────────────────────────────

class EthicsVerdict(BaseModel):
    """Structured verdict from the Ethics Agent"""
    verdict: str  # "PASS" or "FAIL"
    reason: str
    suggestions: List[str] = []
    processing_time_ms: float = 0.0


# ── Aggregator Decision ────────────────────────────────────────────────────────

class AggregatorDecision(BaseModel):
    """Decision from the Aggregator / Judge"""
    action: str  # "ACCEPT", "RETRY", "FORCE_ACCEPT"
    reasoning: str = ""
    feedback: Optional[str] = None   # Specific feedback for Productivity Agent on RETRY
    retry_count: int = 0


# ── Agent Response ─────────────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    """Individual agent's response (kept for audit compatibility)"""
    agent_type: NodeType
    response: str
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float


# ── Trace Event ────────────────────────────────────────────────────────────────

class TraceEvent(BaseModel):
    """Real-time trace event for SSE streaming"""
    node_type: NodeType
    status: str  # "started", "processing", "completed", "error"
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None


# ── Final Aggregated Result ────────────────────────────────────────────────────

class AggregatedResult(BaseModel):
    """Final result from the complete pipeline"""
    final_response: str

    # Pipeline outputs
    creative_brief: Optional[CreativeBrief] = None
    ethics_verdict: Optional[EthicsVerdict] = None
    aggregator_decision: Optional[AggregatorDecision] = None
    retry_count: int = 0

    # Metadata
    total_processing_time_ms: float
    privacy_analysis: PrivacyAnalysis
    domain_analysis: Optional[DomainAnalysis] = None
    retrieved_context: Optional[List[str]] = None
    audit_id: Optional[int] = None
    dp_metrics: Optional[DifferentialPrivacyMetrics] = None

    # Legacy fields — kept for audit log / API compatibility
    agent_responses: List[AgentResponse] = []
    agent_contributions: Dict[str, float] = {}


# ── HTTP Envelope ──────────────────────────────────────────────────────────────

class FinalResponse(BaseModel):
    """Complete HTTP response to the user"""
    success: bool
    result: Optional[AggregatedResult] = None
    error: Optional[str] = None
