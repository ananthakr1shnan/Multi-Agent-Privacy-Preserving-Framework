"""
Response Aggregator Node.
Synthesizes outputs from multiple agents into a coherent final response.
"""
from typing import List, Dict
from app.schemas.models import AgentResponse, AggregatedResult, PrivacyAnalysis, DomainAnalysis, DifferentialPrivacyMetrics
from app.privacy import dp_layer
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings


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
        
        # Initialize Llama 3 for synthesis
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.3
        )
    
    async def synthesize(
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
        # Use lower sensitivity (0.01) to preserve utility while providing privacy
        noisy_weights = dp_layer.apply_noise_to_scores(weights, sensitivity=0.01)
        
        # Normalize noisy weights — enforce minimum floors:
        #   ALL agents ≥ 5%  |  Ethics ≥ 10% in HIGH-sensitivity domains
        # This prevents Laplace noise from eliminating ethics monitoring entirely.
        noisy_weights = self._normalize_weights(noisy_weights, domain_analysis)
        
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
        final_response = await self._build_final_response(agent_responses, noisy_weights, domain_analysis)
        
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
    
    def _normalize_weights(
        self,
        weights: Dict[str, float],
        domain_analysis: 'DomainAnalysis' = None
    ) -> Dict[str, float]:
        """
        Normalize weights so they sum to 1.0, then enforce minimum floors:
        - ALL agents: ≥ 5% (prevents any agent being silenced by DP noise)
        - Ethics agent: ≥ 10% in HIGH-sensitivity domains (constant monitoring guarantee)
        """
        total = sum(weights.values())
        
        if total <= 0.001:
            # If all zero (or negative/too small), fallback to uniform
            count = len(weights)
            return {k: 1.0 / count for k in weights}
            
        # 1. Normalize initially
        normalized = {k: v / total for k, v in weights.items()}
        
        # 2. Determine per-agent floors
        is_high_sensitivity = (
            domain_analysis is not None and domain_analysis.is_high_sensitivity
        )
        base_floor = 0.05
        floors = {k: base_floor for k in normalized}
        if is_high_sensitivity and "ethics_agent" in floors:
            floors["ethics_agent"] = 0.10  # guaranteed ethics monitoring
        
        # 3. Identify agents below their floor
        below_floor = [k for k, v in normalized.items() if v < floors[k]]
        
        if not below_floor:
            return normalized
            
        # 4. Pin below-floor agents to their guaranteed minimum
        final_weights = {}
        pinned_total = 0.0
        
        for k in below_floor:
            final_weights[k] = floors[k]
            pinned_total += floors[k]
            
        # 5. Distribute remaining budget proportionally among above-floor agents
        remaining_budget = 1.0 - pinned_total
        above_floor_agents = [k for k in normalized if k not in below_floor]
        
        # Calculate total weight of above-floor agents to normalize against
        above_floor_total = sum(normalized[k] for k in above_floor_agents)
        
        if above_floor_total > 0:
            for k in above_floor_agents:
                share = normalized[k] / above_floor_total
                final_weights[k] = share * remaining_budget
        else:
            # Edge case: all were somehow at or below floor, distribute evenly
            remaining_per_agent = remaining_budget / len(above_floor_agents) if above_floor_agents else 0
            for k in above_floor_agents:
                final_weights[k] = remaining_per_agent
                
        return final_weights

    async def _build_final_response(
        self,
        agent_responses: List[AgentResponse],
        weights: Dict[str, float],
        domain_analysis: 'DomainAnalysis' = None
    ) -> str:
        """
        Synthesize final response using Llama 3 as Lead Aggregator.
        """
        # 1. format agent inputs
        agent_inputs = []
        for resp in agent_responses:
            agent_name = resp.agent_type.value.replace('_', ' ').title()
            weight_pct = int(weights.get(resp.agent_type.value, 0) * 100)
            agent_inputs.append(f"--- {agent_name} (Weight: {weight_pct}%) ---\n{resp.response}\n")
            
        agents_text = "\n".join(agent_inputs)
        
        # 2. Determine dominance strategy
        strategy = "Balance all perspectives."
        if domain_analysis and domain_analysis.is_high_sensitivity:
            strategy = "CRITICAL: High-sensitivity domain detected. Prioritize Ethics Agent warnings and safety guidelines above all else."
            
        # 3. Construct System Prompt
        system_prompt = (
            "You are the Lead Aggregator for a Privacy-Preserving Framework. "
            "You will receive drafts from three specialized agents: Productivity, Ethics, and Creativity.\n\n"
            "Your Task:\n"
            "1. Synthesize their insights into one cohesive, professional response.\n"
            f"2. Strategy: {strategy}\n"
            "3. Ensure the final output is De-identified: Never mention the specific placeholders or agent names (e.g. 'Productivity Agent says...'). "
            "make it sound like a single unified voice.\n"
            "4. Apply a professional, helpful tone while strictly maintaining the 'Privacy Shield' boundaries.\n"
            "5. If Ethics has a high weight, its safety warnings must be prominent."
        )
        
        # 4. Construct User Prompt
        user_prompt = (
            f"Query Context: {domain_analysis.predicted_domain if domain_analysis else 'General'}\n\n"
            f"Agent Drafts:\n{agents_text}\n\n"
            "Synthesize the final response:"
        )
        
        try:
            # Call Llama 3
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = await self.llm.ainvoke(messages)
            
            # Form final response with agent contributions appended
            final_text = response.content
            
            # Determine correct dominance strategy mention for header
            header_strategy = "Standard"
            if domain_analysis and domain_analysis.is_high_sensitivity:
                header_strategy = "High Sensitivity (Ethics Prioritized)"
            
            # Append detailed breakdown
            final_text += f"\n\n---\n\n### Agent Contributions ({header_strategy})\n"
            
            # Sort agents by weight for display if weights available
            display_order = agent_responses
            if weights:
                display_order = sorted(
                    agent_responses,
                    key=lambda x: weights.get(x.agent_type.value, 0),
                    reverse=True
                )
            
            for resp in display_order:
                agent_name = resp.agent_type.value.replace('_', ' ').title()
                weight_pct = int(weights.get(resp.agent_type.value, 0) * 100) if weights else 0
                final_text += f"\n**{agent_name}** ({weight_pct}%)\n{resp.response}\n"
                
            return final_text
            
        except Exception as e:
            print(f"Error in LLM synthesis: {e}")
            # Fallback to heuristic if LLM fails
            return self._build_final_response_fallback(agent_responses, weights)

    def _build_final_response_fallback(
        self,
        agent_responses: List[AgentResponse],
        weights: Dict[str, float]
    ) -> str:
        """Backup heuristic method"""
        # Sort agents by weight (highest first)
        sorted_agents = sorted(
            agent_responses,
            key=lambda x: weights.get(x.agent_type.value, 0),
            reverse=True
        )
        
        # Synthesize a basic response from the primary agent
        primary = sorted_agents[0]
        final_text = f"**Consolidated Response (Heuristic)**\n\n{primary.response}"
        
        # Append detailed breakdown
        final_text += "\n\n---\n\n### Agent Contributions (Heuristic)\n"
        
        for agent in sorted_agents:
            agent_name = agent.agent_type.value.replace('_', ' ').title()
            weight_pct = int(weights.get(agent.agent_type.value, 0) * 100) if weights else 0
            final_text += f"\n**{agent_name}** ({weight_pct}%)\n{agent.response}\n"
        
        return final_text


# Global aggregator instance
aggregator = ResponseAggregator()
