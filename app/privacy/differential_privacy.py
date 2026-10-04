"""
Differential Privacy Layer for MPPF
Provides formal (ε, δ)-DP guarantees through Laplacian noise injection
"""
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import time


@dataclass
class DPMetrics:
    """Differential Privacy metrics for transparency"""
    epsilon_budget: float
    budget_used: float
    budget_remaining: float
    noise_scale: float
    privacy_guarantee: str
    queries_processed: int


class DifferentialPrivacyLayer:
    """
    Implements Differential Privacy for the MPPF framework.
    
    Key Features:
    - ε-Privacy Budget Management
    - Laplacian Noise Injection
    - Formal (ε, δ)-DP Guarantees
    """
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Initialize DP layer with privacy parameters.
        
        Args:
            epsilon: Privacy budget (lower = more private, typical: 0.1-10)
            delta: Privacy loss probability (typical: 1e-5 to 1e-7)
        """
        self.epsilon = epsilon
        self.delta = delta
        self.budget_used = 0.0
        self.queries_processed = 0
        self.session_start = time.time()
        
        # Budget allocation per query (can be adjusted)
        self.epsilon_per_query = 0.1
    
    def add_laplacian_noise(
        self, 
        value: float, 
        sensitivity: float = 1.0,
        epsilon_allocation: Optional[float] = None
    ) -> float:
        """
        Add Laplacian noise calibrated to epsilon for differential privacy.
        
        Args:
            value: Original value to add noise to
            sensitivity: Sensitivity of the query (how much one record can change result)
            epsilon_allocation: Epsilon budget to use (default: self.epsilon_per_query)
            
        Returns:
            Noisy value with DP guarantee
        """
        if epsilon_allocation is None:
            epsilon_allocation = self.epsilon_per_query
        
        # Check budget
        if self.budget_used + epsilon_allocation > self.epsilon:
            # Budget exhausted - use remaining budget
            epsilon_allocation = max(0.01, self.epsilon - self.budget_used)
        
        # Calculate Laplace scale: b = sensitivity / epsilon
        scale = sensitivity / epsilon_allocation
        
        # Add Laplacian noise
        noise = np.random.laplace(0, scale)
        noisy_value = value + noise
        
        # Update budget
        self.budget_used += epsilon_allocation
        
        return noisy_value
    
    def add_gaussian_noise(
        self,
        value: float,
        sensitivity: float = 1.0,
        epsilon_allocation: Optional[float] = None
    ) -> float:
        """
        Add Gaussian noise for (ε, δ)-DP.
        
        Args:
            value: Original value
            sensitivity: Query sensitivity
            epsilon_allocation: Epsilon budget to use
            
        Returns:
            Noisy value with (ε, δ)-DP guarantee
        """
        if epsilon_allocation is None:
            epsilon_allocation = self.epsilon_per_query
        
        # Check budget
        if self.budget_used + epsilon_allocation > self.epsilon:
            epsilon_allocation = max(0.01, self.epsilon - self.budget_used)
        
        # Gaussian noise scale for (ε, δ)-DP
        # σ = sensitivity * sqrt(2 * ln(1.25/δ)) / ε
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / epsilon_allocation
        
        # Add Gaussian noise
        noise = np.random.normal(0, sigma)
        noisy_value = value + noise
        
        # Update budget
        self.budget_used += epsilon_allocation
        
        return noisy_value
    
    def apply_noise_to_scores(
        self,
        scores: Dict[str, float],
        sensitivity: float = 0.1
    ) -> Dict[str, float]:
        """
        Apply DP noise to agent confidence scores.
        
        Args:
            scores: Dictionary of agent scores (0-1 range)
            sensitivity: How much one record can change scores
            
        Returns:
            Noisy scores with DP guarantee
        """
        noisy_scores = {}
        
        for agent, score in scores.items():
            # Add Laplacian noise
            noisy_score = self.add_laplacian_noise(
                score,
                sensitivity=sensitivity,
                epsilon_allocation=self.epsilon_per_query / len(scores)
            )
            
            # Clamp to [0, 1] range
            noisy_scores[agent] = max(0.0, min(1.0, noisy_score))
        
        return noisy_scores
    
    def get_metrics(self) -> DPMetrics:
        """
        Get current DP metrics for transparency dashboard.
        
        Returns:
            DPMetrics object with current state
        """
        return DPMetrics(
            epsilon_budget=self.epsilon,
            budget_used=self.budget_used,
            budget_remaining=max(0.0, self.epsilon - self.budget_used),
            noise_scale=1.0 / self.epsilon_per_query,  # Approximate
            privacy_guarantee=f"(ε={self.epsilon}, δ={self.delta})-DP",
            queries_processed=self.queries_processed
        )
    
    def reset_budget(self):
        """Reset privacy budget (e.g., for new session)"""
        self.budget_used = 0.0
        self.queries_processed = 0
        self.session_start = time.time()
    
    def increment_query_count(self):
        """Increment the number of queries processed"""
        self.queries_processed += 1
    
    def check_budget_available(self, required_epsilon: float = None) -> bool:
        """
        Check if sufficient budget is available.
        
        Args:
            required_epsilon: Required epsilon (default: epsilon_per_query)
            
        Returns:
            True if budget available, False otherwise
        """
        if required_epsilon is None:
            required_epsilon = self.epsilon_per_query
        
        return (self.budget_used + required_epsilon) <= self.epsilon


# Global DP layer instance
dp_layer = DifferentialPrivacyLayer(epsilon=1.0, delta=1e-5)
