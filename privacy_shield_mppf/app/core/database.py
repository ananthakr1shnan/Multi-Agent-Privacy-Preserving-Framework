"""
Database definitions for MPPF Audit Log.
Stores complete provenance of user interactions for accountability and traceability.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

# Indian Standard Time = UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist() -> datetime:
    """Return current datetime in IST (UTC+5:30)."""
    return datetime.now(IST)
import json
from app.schemas.models import AggregatedResult

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./audit.db"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class AuditLogTrace(Base):
    """
    Audit log entry representing a single user interaction cycle.
    Persists:
    - Original user query (anonymized for privacy if needed, but Audit Logs usually keep raw for compliance - specific implementation policy applies)
    - Privacy analysis results (what was redacted)
    - Domain classification
    - Retrieved context
    - Individual agent responses
    - Final aggregated response
    - Differential Privacy metrics
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=now_ist)
    
    # Inputs
    user_query_anonymized = Column(Text, nullable=False)
    
    # Metadata
    domain = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    
    # Privacy Details
    redaction_count = Column(Integer, default=0)
    entities_found = Column(JSON, nullable=True)
    privacy_budget_used = Column(Float, nullable=True)
    remaining_privacy_budget = Column(Float, nullable=True)
    
    # Context
    retrieved_context = Column(JSON, nullable=True)
    
    # Agent Outputs (JSON blobs)
    agent_responses = Column(JSON, nullable=True)
    agent_weights = Column(JSON, nullable=True)
    
    # Final Output
    final_response = Column(Text, nullable=False)


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_event(aggregated_result: AggregatedResult, original_query_anonymized: str):
    """
    Log a completed workflow event to the database.
    """
    db = SessionLocal()
    try:
        # Extract privacy metrics if available
        budget_used = 0.0
        budget_remaining = 0.0
        if aggregated_result.dp_metrics:
            budget_used = aggregated_result.dp_metrics.budget_used
            budget_remaining = aggregated_result.dp_metrics.budget_remaining
            
        # Extract agent responses as simple dict list
        agent_data = [
            {
                "agent": r.agent_type.value,
                "response": r.response,
                "confidence": r.confidence
            }
            for r in aggregated_result.agent_responses
        ]
        
        # Create log entry
        log_entry = AuditLogTrace(
            user_query_anonymized=original_query_anonymized,
            domain=aggregated_result.domain_analysis.predicted_domain if aggregated_result.domain_analysis else "Unknown",
            confidence=aggregated_result.domain_analysis.confidence if aggregated_result.domain_analysis else 0.0,
            processing_time_ms=aggregated_result.total_processing_time_ms,
            
            redaction_count=aggregated_result.privacy_analysis.redaction_count,
            entities_found=aggregated_result.privacy_analysis.entities_found,
            privacy_budget_used=budget_used,
            remaining_privacy_budget=budget_remaining,
            
            retrieved_context=aggregated_result.retrieved_context if hasattr(aggregated_result, 'retrieved_context') else [],
            agent_responses=agent_data,
            agent_weights=aggregated_result.agent_contributions,
            
            final_response=aggregated_result.final_response
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry.id
        
    except Exception as e:
        print(f"Error logging to audit database: {e}")
        return -1
    finally:
        db.close()
