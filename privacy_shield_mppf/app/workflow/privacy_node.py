"""
Privacy Shield Node - Local PII Detection and Redaction.
Uses Microsoft Presidio to anonymize sensitive data before cloud processing.
"""
from typing import Dict, List, Tuple, Any
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from app.schemas.models import PrivacyAnalysis
import spacy


class PrivacyShield:
    """
    Local privacy gateway that redacts PII before cloud processing.
    Maintains mapping for potential de-anonymization (stored locally only).
    """
    
    def __init__(self):
        """Initialize Presidio analyzer and anonymizer"""
        try:
            # Load spacy model - using smaller model for compatibility
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: en_core_web_sm not found. Please run: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Initialize Presidio components
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Entities to detect
        self.pii_entities = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "LOCATION",
            "ORGANIZATION",
            "CREDIT_CARD",
            "IBAN_CODE",
            "IP_ADDRESS",
            "DATE_TIME"
        ]
        
        # Mapping for de-anonymization (kept local)
        self.anonymization_map: Dict[str, str] = {}
    
    def analyze_and_redact(self, text: str, language: str = "en") -> PrivacyAnalysis:
        """
        Analyze text for PII and redact sensitive information.
        
        Args:
            text: Input text to analyze
            language: Language code (default: "en")
            
        Returns:
            PrivacyAnalysis object with original, anonymized text and metadata
        """
        # Analyze text to find PII entities
        analyzer_results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=self.pii_entities
        )
        
        # Anonymize the text
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
                "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
                "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
                "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
                "ORGANIZATION": OperatorConfig("replace", {"new_value": "<ORGANIZATION>"}),
                "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
                "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<IP_ADDRESS>"}),
                "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE_TIME>"}),
            }
        )
        
        # Build entity details for logging
        entities_found = [
            {
                "type": result.entity_type,
                "text": text[result.start:result.end],
                "start": result.start,
                "end": result.end,
                "score": result.score
            }
            for result in analyzer_results
        ]
        
        # Store mappings for potential de-anonymization
        for entity in entities_found:
            placeholder = f"<{entity['type']}>"
            self.anonymization_map[placeholder] = entity['text']
        
        return PrivacyAnalysis(
            original_text=text,
            anonymized_text=anonymized_result.text,
            entities_found=entities_found,
            redaction_count=len(analyzer_results)
        )
    
    def get_differential_comparison(self, analysis: PrivacyAnalysis) -> Dict[str, Any]:
        """
        Generate a side-by-side comparison of original vs anonymized text.
        
        Args:
            analysis: PrivacyAnalysis result
            
        Returns:
            Dict with comparison data for UI display
        """
        return {
            "original": analysis.original_text,
            "anonymized": analysis.anonymized_text,
            "diff_stats": {
                "total_redactions": analysis.redaction_count,
                "entity_types": list(set(e["type"] for e in analysis.entities_found)),
                "privacy_preserved": analysis.redaction_count > 0
            },
            "entities": analysis.entities_found
        }


# Global privacy shield instance
privacy_shield = PrivacyShield()
