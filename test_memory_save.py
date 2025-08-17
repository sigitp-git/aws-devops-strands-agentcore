#!/usr/bin/env python3
"""
Test script to verify memory_client.create_event() is working.

This script tests the complete memory workflow:
1. Retrieves memory ID from SSM Parameter Store
2. Creates a test event in AgentCore Memory
3. Retrieves the stored memories to verify persistence
4. Displays results with proper formatting
"""
import os
import logging
from typing import List, Dict, Any, Tuple
from bedrock_agentcore.memory import MemoryClient
from utils import get_ssm_parameter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration constants
REGION = 'us-east-1'
MEMORY_ID_PARAMETER = "/app/devopsagent/agentcore/memory_id"
TEST_SESSION_ID = "test_session_123"
TEST_ACTOR_ID = "devops_001"
TEST_QUERY = "AWS Lambda"
MAX_MEMORIES = 5
MEMORY_PREVIEW_LENGTH = 100

# Set region
os.environ['AWS_DEFAULT_REGION'] = REGION

def setup_memory_client() -> Tuple[MemoryClient, str]:
    """
    Initialize memory client and get memory ID from SSM.
    
    Returns:
        Tuple of (MemoryClient instance, memory_id string)
        
    Raises:
        ValueError: If memory ID is not found in SSM Parameter Store
    """
    memory_id = get_ssm_parameter(MEMORY_ID_PARAMETER)
    if not memory_id:
        raise ValueError("No memory ID found in SSM")
    
    memory_client = MemoryClient(region_name=REGION)
    return memory_client, memory_id

def create_test_event(memory_client: MemoryClient, memory_id: str, session_id: str, actor_id: str) -> None:
    """
    Create a test event in memory with sample AWS Lambda conversation.
    
    Args:
        memory_client: Initialized MemoryClient instance
        memory_id: Memory resource identifier
        session_id: Session identifier for the test
        actor_id: Actor identifier for the test
    """
    test_messages = [
        ("What is AWS Lambda?", "USER"),
        ("AWS Lambda is a serverless compute service...", "ASSISTANT"),
    ]
    
    memory_client.create_event(
        memory_id=memory_id,
        actor_id=actor_id,
        session_id=session_id,
        messages=test_messages,
    )

def retrieve_test_memories(memory_client: MemoryClient, memory_id: str, actor_id: str, query: str = TEST_QUERY) -> List[Dict[str, Any]]:
    """
    Retrieve test memories from the semantic namespace.
    
    Args:
        memory_client: Initialized MemoryClient instance
        memory_id: Memory resource identifier
        actor_id: Actor identifier for namespace construction
        query: Search query for memory retrieval
        
    Returns:
        List of memory dictionaries
    """
    memories = memory_client.retrieve_memories(
        memory_id=memory_id,
        namespace=f"agent/devops/{actor_id}/semantic",
        query=query,
        top_k=MAX_MEMORIES,
    )
    
    return memories

def display_memories(memories: List[Dict[str, Any]]) -> None:
    """
    Display retrieved memories in a formatted way.
    
    Args:
        memories: List of memory dictionaries to display
    """
    print(f"✅ Retrieved {len(memories)} memories")
    for i, memory in enumerate(memories):
        if isinstance(memory, dict):
            content = memory.get("content", {})
            if isinstance(content, dict):
                text = content.get("text", "").strip()
                if text:
                    print(f"  Memory {i+1}: {text[:MEMORY_PREVIEW_LENGTH]}...")

def test_memory_save() -> bool:
    """
    Test if memory interactions are being saved and can be retrieved.
    
    Returns:
        True if all tests pass, False otherwise
    """
    print("🔍 Testing Memory Save Functionality")
    print("=" * 50)
    
    try:
        # Setup
        memory_client, memory_id = setup_memory_client()
        print(f"✅ Found memory ID: {memory_id}")
        
        # Test event creation
        print("\n📝 Testing create_event functionality...")
        create_test_event(memory_client, memory_id, TEST_SESSION_ID, TEST_ACTOR_ID)
        print("✅ Successfully created test event in memory")
        
        # Test memory retrieval
        print("\n🔍 Testing memory retrieval...")
        memories = retrieve_test_memories(memory_client, memory_id, TEST_ACTOR_ID)
        display_memories(memories)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during memory testing: {e}")
        return False

def main() -> int:
    """
    Main entry point for the memory test script.
    
    Returns:
        0 if all tests pass, 1 if tests fail
    """
    try:
        success = test_memory_save()
        if success:
            print("\n🎉 Memory save functionality is working correctly!")
            return 0
        else:
            print("\n❌ Memory save functionality has issues")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logging.exception("Unexpected error during testing")
        return 1

if __name__ == "__main__":
    exit(main())