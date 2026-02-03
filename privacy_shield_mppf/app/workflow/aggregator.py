"""
Response Aggregator Node.
Synthesizes outputs from multiple agents into a coherent final response.
"""
from typing import List, Dict
from app.schemas.models import AgentResponse, AggregatedResult, PrivacyAnalysis, DomainAnalysis, DifferentialPrivacyMetrics
from app.privacy import dp_layer


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
        domain_analysis: 'DomainAnalysis' = None,
        total_processing_time_ms: float = 0
    ) -> AggregatedResult:
        """
        Synthesize multiple agent responses into a final result.
        
        Args:
            agent_responses: List of responses from all agents
            privacy_analysis: Privacy shield analysis result
            domain_analysis: Optional domain expert analysis for dynamic weighting
            total_processing_time_ms: Total workflow execution time
            
        Returns:
            AggregatedResult with final response and metadata
        """
        # Calculate weights based on agent confidence and domain context
        weights = self._calculate_weights(agent_responses, domain_analysis)
        
        # Apply Differential Privacy noise to weights
        noisy_weights = dp_layer.apply_noise_to_scores(weights, sensitivity=0.1)
        
        # Increment query count for DP tracking
        dp_layer.increment_query_count()
        
        # Get DP metrics for transparency
        dp_metrics_data = dp_layer.get_metrics()
        dp_metrics = DifferentialPrivacyMetrics(
            epsilon_budget=dp_metrics_data.epsilon_budget,
            budget_used=dp_metrics_data.budget_used,
            budget_remaining=dp_metrics_data.budget_remaining,
            noise_scale=dp_metrics_data.noise_scale,
            privacy_guarantee=dp_metrics_data.privacy_guarantee,
            queries_processed=dp_metrics_data.queries_processed
        )
        
        # Build the final response with noisy weights
        final_response = self._build_final_response(agent_responses, noisy_weights, domain_analysis)
        
        return AggregatedResult(
            final_response=final_response,
            agent_contributions=noisy_weights,
            total_processing_time_ms=total_processing_time_ms,
            privacy_analysis=privacy_analysis,
            domain_analysis=domain_analysis,
            agent_responses=agent_responses,
            dp_metrics=dp_metrics
        )
    
    def _calculate_weights(self, agent_responses: List[AgentResponse], domain_analysis: 'DomainAnalysis' = None) -> Dict[str, float]:
        """
        Calculate contribution weights for each agent.
        Implements Expert-Informed Dynamic Weighting:
        - For high-sensitivity domains (Privacy, Finance, Legal, Health), boost Ethics agent
        - Otherwise, use confidence-based weighting
        
        Args:
            agent_responses: List of agent responses
            domain_analysis: Optional domain expert analysis
            
        Returns:
            Dictionary mapping agent type to weight
        """
        weights = {}
        
        # Expert-Informed Weighting: Boost ethics for high-sensitivity domains
        if domain_analysis and domain_analysis.is_high_sensitivity:
            # High-sensitivity domain detected - prioritize ethics and safety
            for resp in agent_responses:
                if resp.agent_type.value == "ethics_agent":
                    weights["ethics_agent"] = 0.5  # 50% weight for ethics
                elif resp.agent_type.value == "productivity_agent":
                    weights["productivity_agent"] = 0.35  # 35% for productivity
                elif resp.agent_type.value == "creativity_agent":
                    weights["creativity_agent"] = 0.15  # 15% for creativity
        else:
            # Standard confidence-based weighting
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
        weights: Dict[str, float],
        domain_analysis: 'DomainAnalysis' = None
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
        
        # Add subtle domain context badge if available
        if domain_analysis:
            sections.append(f"*Contextualized for {domain_analysis.predicted_domain} query*\n")
        
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
