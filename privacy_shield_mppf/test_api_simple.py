import requests
import json

# Test the MPPF API with a privacy-related query
url = "http://localhost:8000/api/query"
payload = {
    "query": "How should I handle customer credit card data and personal information?"
}

print("Testing MPPF Domain Expert Integration...")
print(f"Sending query: {payload['query']}\n")

try:
    response = requests.post(url, json=payload, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        
        print("Response received successfully!\n")
        print("=" * 80)
        
        # Check if domain_analysis exists in the result
        if result.get("success") and "result" in result:
            data = result["result"]
            
            # Domain Analysis
            if "domain_analysis" in data and data["domain_analysis"]:
                domain = data["domain_analysis"]
                print("\nDOMAIN EXPERT ANALYSIS:")
                print(f"   Domain: {domain.get('predicted_domain', 'N/A')}")
                print(f"   Confidence: {domain.get('confidence', 0):.0%}")
                print(f"   High Sensitivity: {'Yes (WARNING)' if domain.get('is_high_sensitivity') else 'No'}")
                print(f"   Processing Time: {domain.get('processing_time_ms', 0):.0f}ms")
                if 'persona_directive' in domain:
                    print(f"   Persona Directive: {domain['persona_directive'][:100]}...")
            else:
                print("\nWARNING: No domain_analysis found in response")
            
            # Privacy Analysis
            if "privacy_analysis" in data:
                privacy = data["privacy_analysis"]
                print(f"\nPRIVACY SHIELD:")
                print(f"   Redactions: {privacy.get('redaction_count', 0)}")
                print(f"   Anonymized Query: {privacy.get('anonymized_text', 'N/A')[:80]}...")
            
            # Agent Contributions
            if "agent_contributions" in data:
                print(f"\nAGENT CONTRIBUTIONS:")
                for agent, weight in data["agent_contributions"].items():
                    print(f"   {agent}: {weight:.0%}")
            
            # Total time
            print(f"\nTotal Processing Time: {data.get('total_processing_time_ms', 0):.0f}ms")
            print("=" * 80)
            print("\nSUCCESS: Domain Expert integration is working correctly!")
            
    else:
        print(f"ERROR: HTTP {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to server. Is it running on http://localhost:8000?")
except Exception as e:
    print(f"ERROR: {e}")
