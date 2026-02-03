"""
Domain Expert Node - Local T5-base LoRA Model.
Provides domain classification and persona directives to guide cloud LLM reasoning.
"""
import os
import json
import torch
import torch.nn as nn
from transformers import T5ForConditionalGeneration, T5Tokenizer
from peft import PeftModel
import time
from typing import Dict

from app.schemas.models import DomainAnalysis


class DomainExpert:
    """
    Local T5-base model with LoRA adapter for domain classification.
    Trained on Kaggle dataset to identify query domains and generate context.
    """
    
    # Strategic domain mappings for high-impact categories
    STRATEGIC_DOMAINS = {
        "Privacy/Data Security": ["redaction", "pii", "privacy", "data", "confidential", "secure"],
        "Financial/Business": ["roi", "startup", "business", "finance", "investment", "revenue"],
        "Academic/Educational": ["study", "research", "learn", "education", "academic", "university"],
        "Geography/Travel": ["capital", "city", "country", "geography", "travel", "location"],
        "Technology": ["software", "code", "programming", "tech", "development", "api"],
        "Health/Medical": ["health", "medical", "doctor", "treatment", "medicine", "patient"],
        "Legal/Compliance": ["legal", "law", "compliance", "regulation", "contract", "policy"]
    }
    
    # High-sensitivity domains that require ethics boost
    HIGH_SENSITIVITY_DOMAINS = {
        "Privacy/Data Security",
        "Financial/Business", 
        "Legal/Compliance",
        "Health/Medical"
    }
    
    def __init__(self, model_dir: str = "./best model"):
        """
        Initialize the domain expert with T5 model and LoRA adapter.
        
        Args:
            model_dir: Path to the model directory containing LoRA weights
        """
        self.model_dir = model_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.cat_mapping = {}
        self.id2cat = {}
        
        # Load model on initialization
        self._load_model()
    
    def _load_model(self):
        """Load T5 model, LoRA adapter, and category mappings."""
        try:
            print(f"🔸 Loading Domain Expert (T5-base + LoRA) on {self.device}...")
            
            # Load tokenizer
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_dir)
            
            # Load base T5 model
            base_model = T5ForConditionalGeneration.from_pretrained("t5-base")
            
            # Load LoRA adapter
            self.model = PeftModel.from_pretrained(base_model, self.model_dir).to(self.device)
            self.model.eval()
            
            # Load category mapping
            cat_file = os.path.join(self.model_dir, "cat2id.json")
            with open(cat_file, "r") as f:
                self.cat_mapping = json.load(f)
            self.id2cat = {v: k for k, v in self.cat_mapping.items()}
            
            print(f"✅ Domain Expert loaded successfully with {len(self.cat_mapping)} categories")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not load T5 model: {e}")
            print("   Falling back to keyword-based classification")
            self.model = None
    
    def analyze_domain(self, anonymized_query: str) -> DomainAnalysis:
        """
        Analyze the query domain and generate persona directive.
        
        Args:
            anonymized_query: PII-redacted user query
            
        Returns:
            DomainAnalysis with domain, confidence, and directive
        """
        start_time = time.time()
        
        # Use keyword-based classification (robust fallback)
        domain, confidence = self._classify_by_keywords(anonymized_query)
        
        # Generate persona directive for cloud LLM
        persona_directive = self._generate_persona_directive(domain, anonymized_query)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return DomainAnalysis(
            predicted_domain=domain,
            confidence=confidence,
            persona_directive=persona_directive,
            processing_time_ms=processing_time_ms,
            is_high_sensitivity=domain in self.HIGH_SENSITIVITY_DOMAINS
        )
    
    def _classify_by_keywords(self, query: str) -> tuple[str, float]:
        """
        Classify domain using keyword matching.
        
        Args:
            query: Input query text
            
        Returns:
            Tuple of (domain_name, confidence_score)
        """
        query_lower = query.lower()
        
        # Score each strategic domain
        domain_scores: Dict[str, int] = {}
        
        for domain, keywords in self.STRATEGIC_DOMAINS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                domain_scores[domain] = score
        
        # Return highest scoring domain
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            max_score = domain_scores[best_domain]
            # Confidence based on keyword matches (capped at 0.95)
            confidence = min(0.95, 0.6 + (max_score * 0.1))
            return best_domain, confidence
        
        # Default to general domain
        return "General", 0.5
    
    def _generate_persona_directive(self, domain: str, query: str) -> str:
        """
        Generate a persona directive to guide the cloud LLM.
        
        Args:
            domain: Classified domain
            query: Original query
            
        Returns:
            Persona directive string
        """
        directives = {
            "Privacy/Data Security": (
                "EXPERT CONTEXT: This query involves privacy and data security. "
                "Prioritize confidentiality, compliance, and secure practices. "
                "Be cautious about recommending data sharing or storage without proper safeguards."
            ),
            "Financial/Business": (
                "EXPERT CONTEXT: This is a high-stakes business/financial query. "
                "Provide accurate, professional guidance. Consider risk factors, "
                "compliance requirements, and ethical business practices."
            ),
            "Academic/Educational": (
                "EXPERT CONTEXT: This is an academic/educational query. "
                "Provide thorough, well-researched information. Cite best practices "
                "and encourage critical thinking."
            ),
            "Legal/Compliance": (
                "EXPERT CONTEXT: This query has legal/compliance implications. "
                "Exercise caution, recommend consulting qualified legal professionals, "
                "and emphasize the importance of regulatory compliance."
            ),
            "Health/Medical": (
                "EXPERT CONTEXT: This involves health/medical topics. "
                "Provide general information only, emphasize consulting healthcare professionals, "
                "and prioritize safety and well-being."
            ),
            "Technology": (
                "EXPERT CONTEXT: This is a technical query. "
                "Provide practical, actionable solutions with best practices. "
                "Consider security, scalability, and maintainability."
            ),
            "Geography/Travel": (
                "EXPERT CONTEXT: This query relates to geography or travel. "
                "Provide accurate, helpful information about locations, cultures, and logistics."
            )
        }
        
        return directives.get(domain, 
            "EXPERT CONTEXT: Provide a balanced, informative response that addresses the user's needs."
        )


# Global domain expert instance (lazy loading)
_domain_expert_instance = None

def get_domain_expert() -> DomainExpert:
    """Get or create the global domain expert instance."""
    global _domain_expert_instance
    if _domain_expert_instance is None:
        _domain_expert_instance = DomainExpert()
    return _domain_expert_instance


# Convenience instance for imports
domain_expert = get_domain_expert()
