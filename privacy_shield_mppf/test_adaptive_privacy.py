"""
Test Adaptive Privacy Shield with aggressive mode
"""
import sys
sys.path.insert(0, 'D:\\multi\\privacy_shield_mppf')

from app.workflow.privacy_node import privacy_shield

# Test queries for different domains
test_cases = [
    {
        "query": "How do i enter my bank account pin in atm, the pin is 1234",
        "domain": "Financial & Business",
        "aggressive": True
    },
    {
        "query": "My account number is 1234567890 and CVV is 123",
        "domain": "Privacy & Data Security",
        "aggressive": True
    },
    {
        "query": "The OTP code is 567890 for login",
        "domain": "Privacy & Data Security",
        "aggressive": True
    },
    {
        "query": "What is the weather today?",
        "domain": "General",
        "aggressive": False
    },
]

print("=" * 80)
print("ADAPTIVE PRIVACY SHIELD TEST")
print("=" * 80)

for test in test_cases:
    print(f"\nQuery: {test['query']}")
    print(f"Domain: {test['domain']}")
    print(f"Aggressive Mode: {test['aggressive']}")
    
    # Test with aggressive mode
    result = privacy_shield.analyze_and_redact(
        test['query'],
        aggressive_mode=test['aggressive'],
        domain_context=test['domain']
    )
    
    print(f"\nOriginal: {result.original_text}")
    print(f"Anonymized: {result.anonymized_text}")
    print(f"Redactions: {result.redaction_count}")
    print(f"Strategy: {result.redaction_strategy}")
    print(f"Aggressive Triggered: {result.aggressive_mode_triggered}")
    
    if result.entities_found:
        print("Entities Found:")
        for entity in result.entities_found:
            print(f"  - {entity['type']}: '{entity['text']}' (score: {entity['score']:.2f})")
    
    print("-" * 80)

print("\nTest complete!")
