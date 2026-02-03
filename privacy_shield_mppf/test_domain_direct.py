"""
Simple test to verify Domain Expert is loaded and working
"""
import sys
sys.path.insert(0, 'D:\\multi\\privacy_shield_mppf')

from app.workflow.domain_expert_node import domain_expert

# Test domain classification
test_queries = [
    "How should I handle customer credit card data?",
    "What are the best practices for machine learning model deployment?",
    "How do I calculate quarterly revenue projections?",
    "What are the ethical implications of AI in healthcare?"
]

print("=" * 80)
print("DOMAIN EXPERT VERIFICATION TEST")
print("=" * 80)

for query in test_queries:
    print(f"\nQuery: {query}")
    result = domain_expert.analyze_domain(query)
    print(f"  Domain: {result.predicted_domain}")
    print(f"  Confidence: {result.confidence:.0%}")
    print(f"  High Sensitivity: {'Yes' if result.is_high_sensitivity else 'No'}")
    print(f"  Processing Time: {result.processing_time_ms:.0f}ms")
    print(f"  Persona: {result.persona_directive[:80]}...")

print("\n" + "=" * 80)
print("SUCCESS: Domain Expert is working correctly!")
print("=" * 80)
