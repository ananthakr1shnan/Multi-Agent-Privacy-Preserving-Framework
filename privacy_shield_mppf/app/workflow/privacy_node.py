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
        
        # Initialize Presidio components with custom recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()
        
        # Add custom recognizers for PINs and passwords
        self._add_custom_recognizers(registry)
        
        self.analyzer = AnalyzerEngine(registry=registry)
        self.anonymizer = AnonymizerEngine()
        
        # Entities to detect (including custom ones)
        self.pii_entities = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "LOCATION",
            "ORGANIZATION",
            "CREDIT_CARD",
            "IBAN_CODE",
            "IP_ADDRESS",
            "DATE_TIME",
            "PIN_NUMBER",      # Custom
            "PASSWORD"         # Custom
        ]
        
        # Mapping for de-anonymization (kept local)
        self.anonymization_map: Dict[str, str] = {}
    
    def _add_custom_recognizers(self, registry: RecognizerRegistry):
        """Add custom pattern recognizers for PINs and passwords"""
        from presidio_analyzer import Pattern, PatternRecognizer
        
        # PIN Number Recognizer (4-6 digit numbers in context of PIN/password)
        pin_patterns = [
            Pattern(
                name="pin_with_context",
                regex=r"\b(?:pin|PIN|password|passcode|code)\s+(?:is|:)?\s*(\d{4,6})\b",
                score=0.9
            ),
            Pattern(
                name="standalone_pin",
                regex=r"\b(\d{4})\b(?=.*(?:pin|PIN|atm|ATM|bank|card))",
                score=0.7
            ),
        ]
        
        pin_recognizer = PatternRecognizer(
            supported_entity="PIN_NUMBER",
            patterns=pin_patterns,
            context=["pin", "PIN", "password", "passcode", "atm", "ATM", "bank", "card", "code"]
        )
        
        # Password Recognizer (catches password-related patterns)
        password_patterns = [
            Pattern(
                name="password_with_context",
                regex=r"\b(?:password|passwd|pwd)\s+(?:is|:)?\s*([^\s]{4,})\b",
                score=0.85
            ),
        ]
        
        password_recognizer = PatternRecognizer(
            supported_entity="PASSWORD",
            patterns=password_patterns,
            context=["password", "passwd", "pwd", "pass", "credentials"]
        )
        
        registry.add_recognizer(pin_recognizer)
        registry.add_recognizer(password_recognizer)
    
    def _add_aggressive_recognizers(self, registry: RecognizerRegistry, domain_context: str):
        """Add aggressive pattern recognizers based on domain context"""
        from presidio_analyzer import Pattern, PatternRecognizer
        
        # Finance/Banking Domain - Aggressive Mode
        if domain_context in ["Privacy & Data Security", "Financial & Business"]:
            # Account Number Recognizer (9-16 digits)
            account_patterns = [
                Pattern(
                    name="account_number",
                    regex=r"\b(\d{9,16})\b",
                    score=0.8
                ),
            ]
            
            account_recognizer = PatternRecognizer(
                supported_entity="ACCOUNT_NUMBER",
                patterns=account_patterns,
                context=["account", "bank", "banking", "finance", "card"]
            )
            
            # CVV Recognizer (3-4 digits)
            cvv_patterns = [
                Pattern(
                    name="cvv_code",
                    regex=r"\b(\d{3,4})\b",
                    score=0.75
                ),
            ]
            
            cvv_recognizer = PatternRecognizer(
                supported_entity="CVV",
                patterns=cvv_patterns,
                context=["cvv", "cvc", "security code", "card"]
            )
            
            # All 4-6 digit sequences (aggressive PIN detection)
            aggressive_pin_patterns = [
                Pattern(
                    name="any_4_6_digits",
                    regex=r"\b(\d{4,6})\b",
                    score=0.85
                ),
            ]
            
            aggressive_pin_recognizer = PatternRecognizer(
                supported_entity="PIN_NUMBER",
                patterns=aggressive_pin_patterns,
                context=["bank", "atm", "card", "pin", "account"]
            )
            
            registry.add_recognizer(account_recognizer)
            registry.add_recognizer(cvv_recognizer)
            registry.add_recognizer(aggressive_pin_recognizer)
        
        # Authentication Domain - Aggressive Mode
        if domain_context in ["Privacy & Data Security", "Technical & Development"]:
            # Aggressive Password Recognizer (all alphanumeric 6+ chars)
            aggressive_password_patterns = [
                Pattern(
                    name="any_alphanumeric",
                    regex=r"\b([a-zA-Z0-9]{6,})\b",
                    score=0.7
                ),
            ]
            
            aggressive_password_recognizer = PatternRecognizer(
                supported_entity="PASSWORD",
                patterns=aggressive_password_patterns,
                context=["password", "login", "auth", "credential", "access"]
            )
            
            # OTP Recognizer (4-8 digits)
            otp_patterns = [
                Pattern(
                    name="otp_code",
                    regex=r"\b(\d{4,8})\b",
                    score=0.8
                ),
            ]
            
            otp_recognizer = PatternRecognizer(
                supported_entity="OTP",
                patterns=otp_patterns,
                context=["otp", "code", "verification", "2fa", "mfa"]
            )
            
            registry.add_recognizer(aggressive_password_recognizer)
            registry.add_recognizer(otp_recognizer)
        
        # Healthcare Domain - Aggressive Mode
        if domain_context in ["Healthcare & Medical"]:
            # SSN Recognizer (9 digits)
            ssn_patterns = [
                Pattern(
                    name="ssn_number",
                    regex=r"\b(\d{9})\b",
                    score=0.9
                ),
                Pattern(
                    name="ssn_formatted",
                    regex=r"\b(\d{3}-\d{2}-\d{4})\b",
                    score=0.95
                ),
            ]
            
            ssn_recognizer = PatternRecognizer(
                supported_entity="SSN",
                patterns=ssn_patterns,
                context=["ssn", "social security", "medical", "patient"]
            )
            
            # Medical ID Recognizer
            medical_id_patterns = [
                Pattern(
                    name="medical_id",
                    regex=r"\b([A-Z]{2}\d{6,10})\b",
                    score=0.85
                ),
            ]
            
            medical_id_recognizer = PatternRecognizer(
                supported_entity="MEDICAL_ID",
                patterns=medical_id_patterns,
                context=["patient", "medical", "health", "record"]
            )
            
            registry.add_recognizer(ssn_recognizer)
            registry.add_recognizer(medical_id_recognizer)


    
    def analyze_and_redact(
        self, 
        text: str, 
        language: str = "en",
        aggressive_mode: bool = False,
        domain_context: str = None
    ) -> PrivacyAnalysis:
        """
        Analyze text for PII and redact sensitive information.
        
        Args:
            text: Input text to analyze
            language: Language code (default: "en")
            aggressive_mode: Enable aggressive redaction for high-sensitivity domains
            domain_context: Domain context from Domain Expert (for aggressive mode)
            
        Returns:
            PrivacyAnalysis object with original, anonymized text and metadata
        """
        # If aggressive mode is enabled, add domain-specific recognizers
        if aggressive_mode and domain_context:
            registry = RecognizerRegistry()
            registry.load_predefined_recognizers()
            self._add_custom_recognizers(registry)
            self._add_aggressive_recognizers(registry, domain_context)
            analyzer = AnalyzerEngine(registry=registry)
        else:
            analyzer = self.analyzer
        
        # Analyze text to find PII entities
        analyzer_results = analyzer.analyze(
            text=text,
            language=language,
            entities=self.pii_entities + (
                ["ACCOUNT_NUMBER", "CVV", "OTP", "SSN", "MEDICAL_ID"] 
                if aggressive_mode else []
            )
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
                "PIN_NUMBER": OperatorConfig("replace", {"new_value": "<PIN>"}),
                "PASSWORD": OperatorConfig("replace", {"new_value": "<PASSWORD>"}),
                "ACCOUNT_NUMBER": OperatorConfig("replace", {"new_value": "<ACCOUNT_NUMBER>"}),
                "CVV": OperatorConfig("replace", {"new_value": "<CVV>"}),
                "OTP": OperatorConfig("replace", {"new_value": "<OTP>"}),
                "SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
                "MEDICAL_ID": OperatorConfig("replace", {"new_value": "<MEDICAL_ID>"}),
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
            redaction_count=len(analyzer_results),
            aggressive_mode_triggered=aggressive_mode,
            redaction_strategy="aggressive" if aggressive_mode else "standard"
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
