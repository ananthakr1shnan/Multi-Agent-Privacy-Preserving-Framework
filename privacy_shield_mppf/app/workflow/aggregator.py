"""
Response Aggregator Node.
Synthesizes outputs from multiple agents into a coherent final response.
"""
from typing import List, Dict
from app.schemas.models import AgentResponse, AggregatedResult, PrivacyAnalysis


class ResponseAggregator:
    """
    Combines agent responses using weighted synthesis.
    Adapts weights based on query characteristics.
    """
    
    def __init__(self):
        # Default weights for each agent type
        self.default_weights = {
            "productivity_agent": 0.5,
            "ethics_agent": 0.25,
            "creativity_agent": 0.25
        }
    
    def synthesize(
        self,
        agent_responses: List[AgentResponse],
        privacy_analysis: PrivacyAnalysis,
        total_processing_time_ms: float
    ) -> AggregatedResult:
        """
        Synthesize multiple agent responses into a final result.
        
        Args:
            agent_responses: List of responses from all agents
            privacy_analysis: Privacy shield analysis result
            total_processing_time_ms: Total workflow execution time
            
        Returns:
            AggregatedResult with final response and metadata
        """
        # Calculate weights based on agent confidence
        weights = self._calculate_weights(agent_responses)
        
        # Build the final response
        final_response = self._build_final_response(agent_responses, weights)
        
        return AggregatedResult(
            final_response=final_response,
            agent_contributions=weights,
            total_processing_time_ms=total_processing_time_ms,
            privacy_analysis=privacy_analysis,
            agent_responses=agent_responses
        )
    
    def _calculate_weights(self, agent_responses: List[AgentResponse]) -> Dict[str, float]:
        """
        Calculate contribution weights for each agent.
        Adjusts based on confidence scores and response quality.
        """
        weights = {}
        total_confidence = sum(resp.confidence for resp in agent_responses)
        
        if total_confidence == 0:
            # Fallback to default weights
            return {resp.agent_type.value: self.default_weights.get(resp.agent_type.value, 0.33)
                    for resp in agent_responses}
        
        # Weight by confidence
        for resp in agent_responses:
            weights[resp.agent_type.value] = resp.confidence / total_confidence
        
        return weights
    
    def _build_final_response(
        self,
        agent_responses: List[AgentResponse],
        weights: Dict[str, float]
    ) -> str:
        """
        Build the final synthesized response.
        
        For simplicity, we create a structured response showing each agent's contribution.
        In a production system, you might use another LLM call to synthesize these into
        a single coherent narrative.
        """
        # Sort agents by weight (highest first)
        sorted_agents = sorted(
            agent_responses,
            key=lambda x: weights.get(x.agent_type.value, 0),
            reverse=True
        )
        
        # Build structured response
        sections = []
        
        # Primary response (highest weighted agent)
        primary = sorted_agents[0]
        sections.append(f"**Primary Response ({primary.agent_type.value.replace('_', ' ').title()})**\n")
        sections.append(primary.response)
        sections.append("\n")
        
        # Additional perspectives
        if len(sorted_agents) > 1:
            sections.append("\n**Additional Perspectives**\n")
            
            for agent in sorted_agents[1:]:
                agent_name = agent.agent_type.value.replace('_', ' ').title()
                contribution_pct = int(weights.get(agent.agent_type.value, 0) * 100)
                
                sections.append(f"\n*{agent_name} ({contribution_pct}% contribution):*\n")
                sections.append(agent.response)
        
        return "\n".join(sections)


# Global aggregator instance
aggregator = ResponseAggregator()
