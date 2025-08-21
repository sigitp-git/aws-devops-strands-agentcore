#!/usr/bin/env python3
"""
Debug script to investigate AgentCore Memory issues
"""
import os
import boto3
from bedrock_agentcore.memory import MemoryClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_ssm_parameter, put_ssm_parameter

# Set region
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
REGION = 'us-east-1'

def debug_memory_resource():
    """Debug the memory resource retrieval"""
    print("🔍 Debugging AgentCore Memory Resource")
    print("=" * 50)
    
    memory_client = MemoryClient(region_name=REGION)
    memory_name = "DevOpsAgentMemory"
    
    # Step 1: Check SSM parameter
    print("\n1. Checking SSM parameter...")
    try:
        memory_id_from_ssm = get_ssm_parameter("/app/devopsagent/agentcore/memory_id")
        print(f"   SSM parameter value: {memory_id_from_ssm}")
        
        if memory_id_from_ssm:
            # Verify this memory exists
            try:
                memory_details = memory_client.gmcp_client.get_memory(memoryId=memory_id_from_ssm)
                print(f"   ✅ Memory exists and is valid")
                print(f"   Memory name: {memory_details.get('name')}")
                print(f"   Memory status: {memory_details.get('status')}")
                return memory_id_from_ssm
            except Exception as e:
                print(f"   ❌ Memory ID from SSM is invalid: {e}")
    except Exception as e:
        print(f"   ⚠️  No SSM parameter found: {e}")
    
    # Step 2: List all memories
    print("\n2. Listing all existing memories...")
    try:
        memories_response = memory_client.gmcp_client.list_memories()
        memories = memories_response.get('memories', [])
        print(f"   Found {len(memories)} total memories")
        
        for i, memory in enumerate(memories):
            print(f"   Memory {i+1}:")
            print(f"     ID: {memory.get('id')}")
            print(f"     Name: {memory.get('name')}")
            print(f"     Status: {memory.get('status')}")
            print(f"     Created: {memory.get('createdAt')}")
            
            # Check if this is our target memory
            if memory.get('name') == memory_name:
                print(f"   🎯 Found target memory: {memory.get('id')}")
                target_memory_id = memory.get('id')
                
                # Get detailed info
                try:
                    detailed_memory = memory_client.gmcp_client.get_memory(memoryId=target_memory_id)
                    print(f"   📋 Memory details:")
                    print(f"     Description: {detailed_memory.get('description')}")
                    print(f"     Status: {detailed_memory.get('status')}")
                    
                    # Check strategies
                    try:
                        strategies = memory_client.get_memory_strategies(target_memory_id)
                        print(f"     Strategies: {len(strategies)} found")
                        for strategy in strategies:
                            print(f"       - Type: {strategy.get('type')}")
                            print(f"         Namespaces: {strategy.get('namespaces')}")
                    except Exception as e:
                        print(f"     ❌ Error getting strategies: {e}")
                    
                    # Save to SSM if not already there
                    if not memory_id_from_ssm:
                        print(f"   💾 Saving memory ID to SSM...")
                        try:
                            put_ssm_parameter("/app/devopsagent/agentcore/memory_id", target_memory_id)
                            print(f"   ✅ Saved to SSM successfully")
                        except Exception as e:
                            print(f"   ❌ Failed to save to SSM: {e}")
                    
                    return target_memory_id
                    
                except Exception as e:
                    print(f"   ❌ Error getting memory details: {e}")
        
        if not any(memory.get('name') == memory_name for memory in memories):
            print(f"   ⚠️  No memory found with name '{memory_name}'")
            
    except Exception as e:
        print(f"   ❌ Error listing memories: {e}")
    
    # Step 3: Check memory status and creation capability
    print("\n3. Checking memory creation capability...")
    try:
        # Try to get memory creation limits/status
        print("   Testing memory creation permissions...")
        
        # We won't actually create a memory here, just test the error
        from bedrock_agentcore.memory.constants import StrategyType
        strategies = [
            {
                StrategyType.SEMANTIC.value: {
                    "name": "TestStrategy",
                    "description": "Test strategy",
                    "namespaces": ["test/namespace"],
                }
            }
        ]
        
        try:
            # This should fail with ValidationException if memory already exists
            response = memory_client.create_memory_and_wait(
                name=memory_name,
                description="Test memory creation",
                strategies=strategies,
                event_expiry_days=90,
            )
            print(f"   ⚠️  Unexpectedly created new memory: {response.get('id')}")
            return response.get('id')
        except Exception as e:
            if "already exists" in str(e):
                print(f"   ✅ Memory creation blocked - memory already exists (expected)")
                print(f"   This confirms the memory exists but we couldn't retrieve it properly")
            else:
                print(f"   ❌ Memory creation failed: {e}")
    
    except Exception as e:
        print(f"   ❌ Error testing memory creation: {e}")
    
    return None

def test_memory_functionality(memory_id):
    """Test memory functionality with a given memory ID"""
    if not memory_id:
        print("\n❌ No memory ID to test")
        return False
    
    print(f"\n4. Testing memory functionality with ID: {memory_id}")
    print("-" * 30)
    
    memory_client = MemoryClient(region_name=REGION)
    
    try:
        # Test retrieving memories
        print("   Testing memory retrieval...")
        memories = memory_client.retrieve_memories(
            memory_id=memory_id,
            namespace="agent/devops/test_devops/semantic",
            query="test query",
            top_k=3,
        )
        print(f"   ✅ Memory retrieval works - found {len(memories)} memories")
        
        # Test creating an event
        print("   Testing event creation...")
        memory_client.create_event(
            memory_id=memory_id,
            actor_id="test_devops",
            session_id="test_session",
            messages=[
                ("Test user message", "USER"),
                ("Test assistant response", "ASSISTANT"),
            ],
        )
        print("   ✅ Event creation works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Memory functionality test failed: {e}")
        return False

if __name__ == "__main__":
    memory_id = debug_memory_resource()
    
    if memory_id:
        print(f"\n🎉 Successfully retrieved memory ID: {memory_id}")
        test_memory_functionality(memory_id)
    else:
        print(f"\n❌ Failed to retrieve memory resource")
        print("   The agent will need to create a new memory or fix the existing one")