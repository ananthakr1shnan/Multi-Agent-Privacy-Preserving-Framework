"""
MPPF Python SDK - Client Library
Provides easy integration with MPPF API
"""
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PrivacyAnalysis:
    """Privacy analysis results."""
    redaction_count: int
    redaction_strategy: str
    aggressive_mode_triggered: bool
    entities_found: List[str]


@dataclass
class DifferentialPrivacyMetrics:
    """Differential privacy metrics."""
    privacy_guarantee: str
    budget_used: float
    epsilon_budget: float
    noise_scale: float


@dataclass
class QueryResponse:
    """Response from MPPF query."""
    final_response: str
    retrieved_context: List[str]
    audit_id: int
    privacy_analysis: PrivacyAnalysis
    agent_contributions: Dict[str, float]
    dp_metrics: Optional[DifferentialPrivacyMetrics]
    total_processing_time_ms: float


class MPPFClient:
    """
    High-level client for interacting with MPPF API.
    
    Example:
        >>> client = MPPFClient("http://localhost:8000")
        >>> result = client.query("What is GDPR?")
        >>> print(result.final_response)
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize MPPF client.
        
        Args:
            base_url: Base URL of MPPF server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def query(self, text: str) -> QueryResponse:
        """
        Submit a privacy-preserving query.
        
        Args:
            text: The query text
            
        Returns:
            QueryResponse object with results
            
        Raises:
            requests.HTTPError: If the request fails
        """
        response = self.session.post(
            f"{self.base_url}/api/query",
            json={"query": text},
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        if not data.get('success'):
            raise Exception(data.get('error', 'Unknown error'))
        
        result = data['result']
        
        return QueryResponse(
            final_response=result['final_response'],
            retrieved_context=result.get('retrieved_context', []),
            audit_id=result.get('audit_id'),
            privacy_analysis=PrivacyAnalysis(**result['privacy_analysis']),
            agent_contributions=result.get('agent_contributions', {}),
            dp_metrics=DifferentialPrivacyMetrics(**result['dp_metrics']) if result.get('dp_metrics') else None,
            total_processing_time_ms=result.get('total_processing_time_ms', 0)
        )
    
    def upload_document(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a document to the knowledge base.
        
        Args:
            file_path: Path to PDF or TXT file
            
        Returns:
            Upload response with chunk count
        """
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.split('/')[-1], f)}
            response = self.session.post(
                f"{self.base_url}/api/upload",
                files=files,
                timeout=120  # Longer timeout for uploads
            )
            response.raise_for_status()
            return response.json()
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the knowledge base.
        
        Returns:
            List of document metadata
        """
        response = self.session.get(f"{self.base_url}/api/knowledge-base")
        response.raise_for_status()
        return response.json()['documents']
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete a document from the knowledge base.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            Deletion response
        """
        response = self.session.delete(
            f"{self.base_url}/api/knowledge-base/{filename}"
        )
        response.raise_for_status()
        return response.json()
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Stats including chunk count and status
        """
        response = self.session.get(f"{self.base_url}/api/knowledge-base/stats")
        response.raise_for_status()
        return response.json()
    
    def get_audit_logs(
        self, 
        page: int = 1, 
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Retrieve audit logs.
        
        Args:
            page: Page number (1-indexed)
            limit: Number of logs per page
            
        Returns:
            Paginated audit logs
        """
        response = self.session.get(
            f"{self.base_url}/api/audit-logs",
            params={"page": page, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, str]:
        """
        Check if the server is healthy.
        
        Returns:
            Health status
        """
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


# Standalone functions for quick usage
def quick_query(text: str, server_url: str = "http://localhost:8000") -> str:
    """
    Quick one-liner to query MPPF.
    
    Example:
        >>> response = quick_query("What is privacy?")
        >>> print(response)
    """
    client = MPPFClient(server_url)
    result = client.query(text)
    return result.final_response
