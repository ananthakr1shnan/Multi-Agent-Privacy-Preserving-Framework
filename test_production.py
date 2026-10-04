"""
Production End-to-End Test for MPPF System.
Tests complete workflow including ChromaDB context retrieval.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.workflow.engine import workflow_engine
from app.core.database import SessionLocal, AuditLogTrace

async def test_production_workflow():
    """Test the complete production workflow."""
    print("=" * 60)
    print("🚀 MPPF PRODUCTION SYSTEM TEST")
    print("=" * 60)
    
    test_queries = [
        "What is the role of the Ethics Agent in MPPF?",
        "How does differential privacy protect user data?",
        "What are the privacy mechanisms used in this system?"
    ]
    
    all_passed = True
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_queries)}: {query}")
        print(f"{'='*60}")
        
        try:
            # Execute workflow
            result = await workflow_engine.execute(user_query=query)
            
            # Check 1: Retrieved Context
            print("\n✓ Context Retrieval:")
            if result.retrieved_context and len(result.retrieved_context) > 0:
                print(f"  ✅ {len(result.retrieved_context)} chunks retrieved")
                for j, ctx in enumerate(result.retrieved_context[:2], 1):
                    print(f"  {j}. {ctx[:80]}...")
            else:
                print("  ❌ NO CONTEXT RETRIEVED")
                all_passed = False
            
            # Check 2: Agent Responses
            print("\n✓ Agent Processing:")
            if result.agent_responses and len(result.agent_responses) == 3:
                print(f"  ✅ All 3 agents responded")
                for agent in result.agent_responses:
                    print(f"  - {agent.agent_type.value}: {len(agent.response)} chars")
            else:
                print(f"  ❌ Expected 3 agents, got {len(result.agent_responses)}")
                all_passed = False
            
            # Check 3: Final Response
            print("\n✓ Final Response:")
            if result.final_response and len(result.final_response) > 50:
                print(f"  ✅ Generated ({len(result.final_response)} chars)")
                print(f"  Preview: {result.final_response[:100]}...")
            else:
                print("  ❌ Response too short or missing")
                all_passed = False
            
            # Check 4: Audit Log
            print("\n✓ Audit Logging:")
            if result.audit_id:
                print(f"  ✅ Audit ID: {result.audit_id}")
                
                # Verify in database
                db = SessionLocal()
                log = db.query(AuditLogTrace).filter_by(id=result.audit_id).first()
                db.close()
                
                if log:
                    print(f"  ✅ Verified in database")
                else:
                    print(f"  ❌ Not found in database")
                    all_passed = False
            else:
                print("  ❌ No Audit ID")
                all_passed = False
            
            # Check 5: Privacy Analysis
            print("\n✓ Privacy Shield:")
            if result.privacy_analysis:
                print(f"  ✅ Redactions: {result.privacy_analysis.redaction_count}")
                print(f"  ✅ Strategy: {result.privacy_analysis.redaction_strategy}")
            else:
                print("  ❌ No privacy analysis")
                all_passed = False
                
            # Check 6: Differential Privacy
            print("\n✓ Differential Privacy:")
            if result.dp_metrics:
                print(f"  ✅ Budget Used: {result.dp_metrics.budget_used:.2f}")
                print(f"  ✅ Guarantee: {result.dp_metrics.privacy_guarantee}")
            else:
                print("  ⚠️ DP metrics not present (may be optional)")
            
            print(f"\n⏱️ Total Time: {result.total_processing_time_ms:.0f}ms")
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - PRODUCTION READY!")
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(test_production_workflow())
