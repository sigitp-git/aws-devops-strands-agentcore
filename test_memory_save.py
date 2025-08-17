#!/usr/bin/env python3
"""
Test script to verify memory_client.create_event() is working
"""
import os
from bedrock_agentcore.memory import MemoryClient
from utils import get_ssm_parameter

# Set region
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
REGION = 'us-east-1'

def test_memory_save():
    """Test if memory interactions are being saved"""
    print("🔍 Testing Memory Save Functionality")
    print("=" * 50)
    
    # Get memory ID
    try:
        memory_id = get_ssm_parameter("/app/devopsagent/agentcore/memory_id")
        if not memory_id:
            print("❌ No memory ID found in SSM")
            return
        
        print(f"✅ Found memory ID: {memory_id}")
        
        # Initialize memory client
        memory_client = MemoryClient(region_name=REGION)
        
        # Test creating an event (simulating what the agent does)
        print("\n📝 Testing create_event functionality...")
        
        test_session_id = "test_session_123"
        test_actor_id = "devops_001"
        
        try:
            # Create a test event
            memory_client.create_event(
                memory_id=memory_id,
                actor_id=test_actor_id,
                session_id=test_session_id,
                messages=[
                    ("What is AWS Lambda?", "USER"),
                    ("AWS Lambda is a serverless compute service...", "ASSISTANT"),
                ],
            )
            print("✅ Successfully created test event in memory")
            
            # Try to retrieve memories to verify it was saved
            print("\n🔍 Testing memory retrieval...")
            memories = memory_client.retrieve_memories(
                memory_id=memory_id,
                namespace=f"agent/devops/{test_actor_id}/semantic",
                query="AWS Lambda",
                top_k=5,
            )
            
            print(f"✅ Retrieved {len(memories)} memories")
            for i, memory in enumerate(memories):
                if isinstance(memory, dict):
                    content = memory.get("content", {})
                    if isinstance(content, dict):
                        text = content.get("text", "").strip()
                        if text:
                            print(f"  Memory {i+1}: {text[:100]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing memory functionality: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting memory ID: {e}")
        return False

if __name__ == "__main__":
    success = test_memory_save()
    if success:
        print("\n🎉 Memory save functionality is working correctly!")
    else:
        print("\n❌ Memory save functionality has issues")