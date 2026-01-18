"""
Pydantic models for request/response schemas and trace events.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    """Types of workflow nodes"""
    PRIVACY_SHIELD = "privacy_shield"
    PRODUCTIVITY_AGENT = "productivity_agent"
    ETHICS_AGENT = "ethics_agent"
    CREATIVITY_AGENT = "creativity_agent"
    AGGREGATOR = "aggregator"


class QueryRequest(BaseModel):
    """User query request"""
    query: str = Field(..., min_length=1, description="User's input query")


class PrivacyAnalysis(BaseModel):
    """Privacy analysis result showing PII detection"""
    original_text: str
    anonymized_text: str
    entities_found: List[Dict[str, Any]]
    redaction_count: int


class AgentResponse(BaseModel):
    """Individual agent's response"""
    agent_type: NodeType
    response: str
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float


class TraceEvent(BaseModel):
    """Real-time trace event for SSE streaming"""
    node_type: NodeType
    status: str  # "started", "processing", "completed", "error"
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None


class AggregatedResult(BaseModel):
    """Final aggregated response"""
    final_response: str
    agent_contributions: Dict[str, float]  # agent -> weight
    total_processing_time_ms: float
    privacy_analysis: PrivacyAnalysis
    agent_responses: List[AgentResponse]


class FinalResponse(BaseModel):
    """Complete response to the user"""
    success: bool
    result: Optional[AggregatedResult] = None
    error: Optional[str] = None
