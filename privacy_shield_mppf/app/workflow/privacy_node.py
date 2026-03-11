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
        """Initialize Presidio analyzer and anonymizer with permanent registries."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: en_core_web_sm not found. Please run: python -m spacy download en_core_web_sm")
            self.nlp = None

        # ── Standard registry (always active) ────────────────────────────────
        std_registry = RecognizerRegistry()
        std_registry.load_predefined_recognizers()
        self._add_custom_recognizers(std_registry)
        self.analyzer = AnalyzerEngine(registry=std_registry)

        # ── Aggressive registries (built once per domain, reused every call) ─
        # Key: domain_context string  →  Value: pre-built AnalyzerEngine
        self._aggressive_analyzers: Dict[str, "AnalyzerEngine"] = {}

        self.anonymizer = AnonymizerEngine()

        # Entities for standard mode
        self.pii_entities = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS",
            "PIN_NUMBER", "PASSWORD",
        ]

        # Extra entities unlocked in aggressive mode
        self.aggressive_entities = [
            "ACCOUNT_NUMBER", "CVV", "OTP", "SSN", "MEDICAL_ID", "SENSITIVE_ID",
        ]

        self.anonymization_map: Dict[str, str] = {}
    
    def _add_custom_recognizers(self, registry: RecognizerRegistry):
        """Standard recognizers always loaded into every registry."""
        from presidio_analyzer import Pattern, PatternRecognizer

        # ── PIN / passcode ────────────────────────────────────────────────────
        pin_recognizer = PatternRecognizer(
            supported_entity="PIN_NUMBER",
            patterns=[
                Pattern("pin_with_context",
                        r"\b(?:pin|PIN|password|passcode|code)\s+(?:is|:)?\s*(\d{4,6})\b",
                        score=0.9),
                Pattern("standalone_pin",
                        r"\b(\d{4})\b(?=.*(?:pin|PIN|atm|ATM|bank|card))",
                        score=0.7),
            ],
            context=["pin", "PIN", "password", "passcode", "atm", "ATM",
                     "bank", "card", "code"],
        )

        # ── Password ──────────────────────────────────────────────────────────
        password_recognizer = PatternRecognizer(
            supported_entity="PASSWORD",
            patterns=[
                Pattern("password_with_context",
                        r"\b(?:password|passwd|pwd)\s+(?:is|:)?\s*([^\s]{4,})\b",
                        score=0.85),
            ],
            context=["password", "passwd", "pwd", "pass", "credentials"],
        )

        registry.add_recognizer(pin_recognizer)
        registry.add_recognizer(password_recognizer)

    # ── Safe-term deny-list ───────────────────────────────────────────────────
    # These words are NEVER PII regardless of NER output.
    # Prevents acronyms like "mppf", "ai", "api" from being labelled as PERSON.
    _SAFE_TERMS = frozenset({
        "mppf", "ai", "ml", "nlp", "dp", "llm", "api", "rag",
        "framework", "model", "system", "agent", "ner", "bert",
        "lora", "t5", "gpt", "privacy", "data", "query", "node",
        "pipeline", "workflow", "engine", "database", "cloud",
    })

    def _filter_safe_terms(self, text: str, results: list) -> list:
        """Remove any result whose matched text is a known safe term."""
        return [
            r for r in results
            if text[r.start:r.end].lower().strip() not in self._SAFE_TERMS
        ]


    def _build_aggressive_analyzer(self, domain_context: str) -> "AnalyzerEngine":
        """
        Build (once) and cache a domain-specific aggressive AnalyzerEngine.
        Uses context-embedded regex so bare numbers like 987654321 are caught
        even without explicit keyword neighbours in the text.
        """
        from presidio_analyzer import Pattern, PatternRecognizer

        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()
        self._add_custom_recognizers(registry)

        # ── Finance / Privacy ─────────────────────────────────────────────────
        if domain_context in ["Privacy & Data Security", "Financial & Business",
                               "Finance", "Privacy/Data Security"]:

            finance_context = ["account", "bank", "loan", "sbi", "account number",
                               "acc no", "ibanking", "finance", "transfer"]

            account_recognizer = PatternRecognizer(
                supported_entity="ACCOUNT_NUMBER",
                patterns=[
                    # HIGH score: number immediately follows an account keyword
                    Pattern("strict_account_number",
                            r"(?i)(?:acc(?:ount)?\s*(?:no|number|#)?\s*[:\-]?\s*)(\d{9,18})\b",
                            score=0.95),
                    # MEDIUM score: bare 9-18 digit sequence; boosted by context words nearby
                    Pattern("generic_account_digits",
                            r"\b(\d{9,18})\b",
                            score=0.5),
                ],
                context=finance_context,
            )

            cvv_recognizer = PatternRecognizer(
                supported_entity="CVV",
                patterns=[Pattern("cvv_code", r"\b(\d{3,4})\b", score=0.75)],
                context=["cvv", "cvc", "security code", "card"],
            )

            aggressive_pin_recognizer = PatternRecognizer(
                supported_entity="PIN_NUMBER",
                patterns=[Pattern("any_4_6_digits", r"\b(\d{4,6})\b", score=0.85)],
                context=["bank", "atm", "card", "pin", "account"],
            )

            registry.add_recognizer(account_recognizer)
            registry.add_recognizer(cvv_recognizer)
            registry.add_recognizer(aggressive_pin_recognizer)

        # ── Auth / Technical ──────────────────────────────────────────────────
        if domain_context in ["Privacy & Data Security", "Technical & Development",
                               "Privacy/Data Security"]:
            registry.add_recognizer(PatternRecognizer(
                supported_entity="PASSWORD",
                # Require at least one digit to avoid false-positives on plain English words
                patterns=[Pattern("alphanumeric_with_digit",
                                  r"(?=\S*\d)\b([a-zA-Z0-9!@#$%^&*]{6,})\b", score=0.7)],
                context=["password", "login", "auth", "credential", "access", "secret"],
            ))
            registry.add_recognizer(PatternRecognizer(
                supported_entity="OTP",
                patterns=[Pattern("otp_code", r"\b(\d{4,8})\b", score=0.8)],
                context=["otp", "code", "verification", "2fa", "mfa"],
            ))

        # ── Healthcare ────────────────────────────────────────────────────────
        if domain_context in ["Healthcare & Medical"]:
            registry.add_recognizer(PatternRecognizer(
                supported_entity="SSN",
                patterns=[
                    Pattern("ssn_number",    r"\b(\d{9})\b",           score=0.9),
                    Pattern("ssn_formatted", r"\b(\d{3}-\d{2}-\d{4})\b", score=0.95),
                ],
                context=["ssn", "social security", "medical", "patient"],
            ))
            registry.add_recognizer(PatternRecognizer(
                supported_entity="MEDICAL_ID",
                patterns=[Pattern("medical_id", r"\b([A-Z]{2}\d{6,10})\b", score=0.85)],
                context=["patient", "medical", "health", "record"],
            ))

        # ── Universal numeric ID shield (ALL high-sensitivity domains) ────────
        # Any 9-digit number is a potential national ID, account, or reference.
        registry.add_recognizer(PatternRecognizer(
            supported_entity="SENSITIVE_ID",
            patterns=[Pattern("9_digit_id", r"\b(\d{9})\b", score=0.6)],
            context=["id", "number", "patient", "account", "reference",
                     "policy", "employee", "national", "aadhaar", "pan"],
        ))

        return AnalyzerEngine(registry=registry)

    def _get_aggressive_analyzer(self, domain_context: str) -> "AnalyzerEngine":
        """Return cached aggressive analyzer, building it on first use."""
        if domain_context not in self._aggressive_analyzers:
            self._aggressive_analyzers[domain_context] = \
                self._build_aggressive_analyzer(domain_context)
        return self._aggressive_analyzers[domain_context]


    
    # ──────────────────────────────────────────────────────────────────────────
    # Keyword-based domain pre-detector (runs BEFORE T5 domain expert)
    # Lets the shield self-activate aggressive mode on the first pass so
    # account numbers, SSNs, etc. are caught even in the parallel race.
    # ──────────────────────────────────────────────────────────────────────────
    _DOMAIN_KEYWORDS = {
        "Privacy/Data Security": [
            "account", "bank", "sbi", "hdfc", "icici", "loan", "transfer",
            "iban", "acc no", "account no", "account number", "ibanking",
            "finance", "interest", "credit", "debit", "upi", "ifsc",
        ],
        "Healthcare & Medical": [
            "patient", "ssn", "social security", "aadhaar", "medical",
            "diagnosis", "prescription", "health", "hospital", "doctor",
            "insurance", "policy no", "policy number",
        ],
        "Technical & Development": [
            "password", "passwd", "token", "api key", "secret", "otp",
            "2fa", "mfa", "auth", "credential", "login",
        ],
    }

    def _detect_domain_from_keywords(self, text: str) -> str | None:
        """
        Lightweight O(n) scan for domain-specific trigger words.
        Returns a domain string (matching the aggressive-registry keys) or None.
        Prioritised: Finance > Healthcare > Auth.
        """
        lower = text.lower()
        for domain, keywords in self._DOMAIN_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return domain
        return None

    def analyze_and_redact(
        self,
        text: str,
        language: str = "en",
        aggressive_mode: bool = False,
        domain_context: str = None
    ) -> PrivacyAnalysis:
        """
        Analyze text for PII and redact sensitive information.
        Uses a pre-built permanent registry -- no per-call construction overhead.

        Self-activation: if no domain_context is supplied but the text itself
        contains finance/medical/auth keywords, aggressive mode is enabled
        automatically without waiting for the T5 domain expert.
        """
        # ------------------------------------------------------------------
        # Self-activate aggressive mode from keywords (first-pass safety net)
        # ------------------------------------------------------------------
        if not (aggressive_mode and domain_context):
            inferred_domain = self._detect_domain_from_keywords(text)
            if inferred_domain:
                aggressive_mode = True
                domain_context = inferred_domain

        if aggressive_mode and domain_context:
            analyzer = self._get_aggressive_analyzer(domain_context)
            entities = self.pii_entities + self.aggressive_entities
        else:
            analyzer = self.analyzer
            entities = self.pii_entities

        analyzer_results = analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
        )

        # Remove false positives — known safe terms that should never be redacted
        analyzer_results = self._filter_safe_terms(text, analyzer_results)


        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators={
                "DEFAULT":         OperatorConfig("replace", {"new_value": "<REDACTED>"}),
                "PERSON":          OperatorConfig("replace", {"new_value": "<PERSON>"}),
                "EMAIL_ADDRESS":   OperatorConfig("replace", {"new_value": "<EMAIL>"}),
                "PHONE_NUMBER":    OperatorConfig("replace", {"new_value": "<PHONE>"}),
                "LOCATION":        OperatorConfig("replace", {"new_value": "<LOCATION>"}),
                "ORGANIZATION":    OperatorConfig("replace", {"new_value": "<ORGANIZATION>"}),
                "CREDIT_CARD":     OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
                "IP_ADDRESS":      OperatorConfig("replace", {"new_value": "<IP_ADDRESS>"}),
                "DATE_TIME":       OperatorConfig("replace", {"new_value": "<DATE_TIME>"}),
                "PIN_NUMBER":      OperatorConfig("replace", {"new_value": "<PIN>"}),
                "PASSWORD":        OperatorConfig("replace", {"new_value": "<PASSWORD>"}),
                "ACCOUNT_NUMBER":  OperatorConfig("replace", {"new_value": "<ACCOUNT_NUMBER>"}),
                "CVV":             OperatorConfig("replace", {"new_value": "<CVV>"}),
                "OTP":             OperatorConfig("replace", {"new_value": "<OTP>"}),
                "SSN":             OperatorConfig("replace", {"new_value": "<SSN>"}),
                "MEDICAL_ID":      OperatorConfig("replace", {"new_value": "<MEDICAL_ID>"}),
                "SENSITIVE_ID":    OperatorConfig("replace", {"new_value": "<SENSITIVE_ID>"}),
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
