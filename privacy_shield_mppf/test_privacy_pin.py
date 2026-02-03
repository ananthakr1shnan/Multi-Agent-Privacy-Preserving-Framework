"""
Test Privacy Shield PIN detection
"""
import sys
sys.path.insert(0, 'D:\\multi\\privacy_shield_mppf')

from app.workflow.privacy_node import privacy_shield

# Test queries with PINs
test_queries = [
    "How do i enter my bank account pin in atm, the pin is 1234",
    "My ATM PIN is 5678",
    "The password is abc123",
    "My card PIN: 9999",
]

print("=" * 80)
print("PRIVACY SHIELD PIN DETECTION TEST")
print("=" * 80)

for query in test_queries:
    print(f"\nOriginal: {query}")
    result = privacy_shield.analyze_and_redact(query)
    print(f"Anonymized: {result.anonymized_text}")
    print(f"Redactions: {result.redaction_count}")
    if result.entities_found:
        for entity in result.entities_found:
            print(f"  - {entity['type']}: '{entity['text']}' (score: {entity['score']:.2f})")
    print("-" * 80)

print("\nTest complete!")
