"""
Example usage of MPPF SDK
"""
from mppf_sdk import MPPFClient

def main():
    # Initialize client
    client = MPPFClient(base_url="http://localhost:8000")
    
    print("🚀 MPPF SDK Demo\n" + "="*50)
    
    # 1. Check server health
    print("\n1. Checking server health...")
    health = client.health_check()
    print(f"   ✅ Server status: {health['status']}")
    
    # 2. Get knowledge base stats
    print("\n2. Knowledge base stats...")
    stats = client.get_knowledge_base_stats()
    print(f"   📚 Total chunks: {stats['total_chunks']}")
    print(f"   📊 Status: {stats['status']}")
    
    # 3. Submit a query
    print("\n3. Submitting query...")
    result = client.query("What is the role of the Ethics Agent in MPPF?")
    
    print(f"   📝 Response: {result.final_response[:100]}...")
    print(f"   🛡️ Privacy: {result.privacy_analysis.redaction_count} redactions")
    print(f"   📚 Context: {len(result.retrieved_context)} chunks retrieved")
    print(f"   🧾 Audit ID: {result.audit_id}")
    print(f"   ⏱️ Time: {result.total_processing_time_ms:.0f}ms")
    
    # 4. View agent contributions
    print("\n4. Agent contributions:")
    for agent, weight in result.agent_contributions.items():
        print(f"   - {agent}: {weight*100:.1f}%")
    
    # 5. List documents
    print("\n5. Documents in knowledge base:")
    docs = client.list_documents()
    for doc in docs[:3]:  # Show first 3
        print(f"   - {doc['filename']} ({doc['size_bytes'] / 1024:.1f} KB)")
    
    print("\n" + "="*50)
    print("✅ SDK Demo Complete!")


if __name__ == "__main__":
    main()
