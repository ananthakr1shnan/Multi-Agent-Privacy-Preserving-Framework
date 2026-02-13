"""
Specialized LLM Agent Nodes.
Each agent has a distinct persona and evaluation criteria.
"""
import time
from app.core.llm_client import groq_client
from app.schemas.models import AgentResponse, NodeType


class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(self, node_type: NodeType, system_prompt: str):
        self.node_type = node_type
        self.system_prompt = system_prompt
    
    async def process(self, anonymized_query: str, domain_context: str = None, retrieved_context: list[str] = None) -> AgentResponse:
        """
        Process the anonymized query and generate a response.
        
        Args:
            anonymized_query: PII-redacted user query
            domain_context: Optional domain expert context to guide reasoning
            retrieved_context: Optional list of retrieved context strings
            
        Returns:
            AgentResponse with the agent's output
        """
        start_time = time.time()
        
        try:
            # Prepend domain context to system prompt if provided
            system_prompt = self.system_prompt
            if domain_context:
                system_prompt = f"{domain_context}\n\n{self.system_prompt}"
            
            # Append retrieved context if provided
            if retrieved_context:
                context_str = "\n".join([f"- {c}" for c in retrieved_context])
                system_prompt += f"\n\nRETRIEVED CONTEXT:\n{context_str}"
            
            result = await groq_client.generate(
                prompt=anonymized_query,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return AgentResponse(
                agent_type=self.node_type,
                response=result["content"],
                confidence=0.85,  # Could be computed based on finish_reason and coherence
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            return AgentResponse(
                agent_type=self.node_type,
                response=f"Error: {str(e)}",
                confidence=0.0,
                processing_time_ms=processing_time_ms
            )


class ProductivityAgent(BaseAgent):
    """
    Focuses on actionable, direct, and practical responses.
    Optimized for efficiency and task completion.
    """
    
    SYSTEM_PROMPT = """You are a Productivity Agent. Your role is to provide clear, actionable, and efficient responses.
Focus on:
- Direct answers that solve the user's immediate need
- Step-by-step instructions when appropriate
- Time-saving tips and best practices
- Practical solutions over theoretical discussions

Be concise, professional, and results-oriented."""
    
    def __init__(self):
        super().__init__(NodeType.PRODUCTIVITY_AGENT, self.SYSTEM_PROMPT)


class EthicsAgent(BaseAgent):
    """
    Evaluates responses for safety, bias, and ethical concerns.
    Acts as a quality control layer.
    """
    
    SYSTEM_PROMPT = """You are an Ethics and Safety Agent. Your role is to evaluate requests for potential issues.
Consider:
- Ethical implications and potential harms
- Bias or fairness concerns
- Safety and security considerations
- Privacy implications
- Legal and compliance aspects

Provide a balanced perspective that highlights both benefits and risks. If the request is problematic, suggest safer alternatives."""
    
    def __init__(self):
        super().__init__(NodeType.ETHICS_AGENT, self.SYSTEM_PROMPT)


class CreativityAgent(BaseAgent):
    """
    Provides diverse perspectives and creative angles.
    Explores unconventional approaches and innovative solutions.
    """
    
    SYSTEM_PROMPT = """You are a Creativity Agent. Your role is to provide innovative and diverse perspectives.
Focus on:
- Creative and unconventional solutions
- Multiple viewpoints and alternative approaches
- Out-of-the-box thinking
- Connecting ideas from different domains
- Inspiring and thought-provoking insights

Be imaginative, explore possibilities, and challenge conventional thinking."""
    
    def __init__(self):
        super().__init__(NodeType.CREATIVITY_AGENT, self.SYSTEM_PROMPT)


# Agent instances
productivity_agent = ProductivityAgent()
ethics_agent = EthicsAgent()
creativity_agent = CreativityAgent()
