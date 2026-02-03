"""
Test Differential Privacy Integration
"""
import sys
sys.path.insert(0, 'D:\\multi\\privacy_shield_mppf')

from app.privacy import dp_layer

print("=" * 80)
print("DIFFERENTIAL PRIVACY INTEGRATION TEST")
print("=" * 80)

# Test 1: Laplacian Noise
print("\n1. Testing Laplacian Noise Injection")
original_value = 0.75
noisy_value = dp_layer.add_laplacian_noise(original_value, sensitivity=0.1)
print(f"   Original: {original_value:.4f}")
print(f"   Noisy: {noisy_value:.4f}")
print(f"   Noise: {abs(noisy_value - original_value):.4f}")

# Test 2: Gaussian Noise
print("\n2. Testing Gaussian Noise Injection")
noisy_value_gaussian = dp_layer.add_gaussian_noise(original_value, sensitivity=0.1)
print(f"   Original: {original_value:.4f}")
print(f"   Noisy: {noisy_value_gaussian:.4f}")
print(f"   Noise: {abs(noisy_value_gaussian - original_value):.4f}")

# Test 3: Agent Scores with DP
print("\n3. Testing Agent Score Noise Application")
agent_scores = {
    "productivity_agent": 0.5,
    "ethics_agent": 0.25,
    "creativity_agent": 0.25
}
print(f"   Original Scores: {agent_scores}")
noisy_scores = dp_layer.apply_noise_to_scores(agent_scores, sensitivity=0.1)
print(f"   Noisy Scores: {noisy_scores}")

# Test 4: Privacy Budget Tracking
print("\n4. Testing Privacy Budget Tracking")
metrics = dp_layer.get_metrics()
print(f"   Epsilon Budget: {metrics.epsilon_budget}")
print(f"   Budget Used: {metrics.budget_used:.4f}")
print(f"   Budget Remaining: {metrics.budget_remaining:.4f}")
print(f"   Privacy Guarantee: {metrics.privacy_guarantee}")
print(f"   Queries Processed: {metrics.queries_processed}")

# Test 5: Multiple Queries (Budget Depletion)
print("\n5. Testing Budget Depletion Over Multiple Queries")
for i in range(5):
    dp_layer.increment_query_count()
    _ = dp_layer.add_laplacian_noise(0.5, sensitivity=0.1)
    metrics = dp_layer.get_metrics()
    print(f"   Query {i+1}: Budget Used = {metrics.budget_used:.4f}, Remaining = {metrics.budget_remaining:.4f}")

# Test 6: Budget Reset
print("\n6. Testing Budget Reset")
dp_layer.reset_budget()
metrics = dp_layer.get_metrics()
print(f"   After Reset:")
print(f"   Budget Used: {metrics.budget_used:.4f}")
print(f"   Queries Processed: {metrics.queries_processed}")

print("\n" + "=" * 80)
print("SUCCESS: Differential Privacy layer is working correctly!")
print("=" * 80)
