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
from typing import List, Dict, Any, Tuple, NamedTuple
from bedrock_agentcore.memory import MemoryClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_ssm_parameter

class TestResult(NamedTuple):
    """Test result container."""
    success: bool
    memory_count: int
    error_message: str = ""

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestConfig:
    """Configuration constants for memory testing."""
    REGION = 'us-east-1'
    MEMORY_ID_PARAMETER = "/app/devopsagent/agentcore/memory_id"
    TEST_SESSION_ID = "test_session_123"
    TEST_ACTOR_ID = "devops_001"
    TEST_QUERY = "AWS Lambda"
    MAX_MEMORIES = 5
    MEMORY_PREVIEW_LENGTH = 100

# Backward compatibility
REGION = TestConfig.REGION
MEMORY_ID_PARAMETER = TestConfig.MEMORY_ID_PARAMETER
TEST_SESSION_ID = TestConfig.TEST_SESSION_ID
TEST_ACTOR_ID = TestConfig.TEST_ACTOR_ID
TEST_QUERY = TestConfig.TEST_QUERY
MAX_MEMORIES = TestConfig.MAX_MEMORIES
MEMORY_PREVIEW_LENGTH = TestConfig.MEMORY_PREVIEW_LENGTH

# Set region
os.environ['AWS_DEFAULT_REGION'] = REGION

def setup_memory_client() -> Tuple[MemoryClient, str]:
    """
    Initialize memory client and get memory ID from SSM.
    
    Returns:
        Tuple of (MemoryClient instance, memory_id string)
        
    Raises:
        ValueError: If memory ID is not found in SSM Parameter Store
        Exception: If memory client initialization fails
    """
    try:
        memory_id = get_ssm_parameter(MEMORY_ID_PARAMETER)
        if not memory_id:
            raise ValueError(f"No memory ID found in SSM parameter: {TestConfig.MEMORY_ID_PARAMETER}")
        
        if not memory_id.strip():
            raise ValueError("Memory ID is empty or contains only whitespace")
            
        memory_client = MemoryClient(region_name=REGION)
        return memory_client, memory_id
        
    except Exception as e:
        logging.error(f"Failed to setup memory client: {e}")
        raise

def create_test_event(memory_client: MemoryClient, memory_id: str, session_id: str, actor_id: str) -> None:
    """
    Create a test event in memory with sample AWS conversation.
    
    Args:
        memory_client: Initialized MemoryClient instance
        memory_id: Memory resource identifier
        session_id: Session identifier for the test
        actor_id: Actor identifier for the test
        
    Raises:
        ValueError: If any required parameter is empty
        Exception: If memory event creation fails
    """
    # Validate inputs
    if not all([memory_id, session_id, actor_id]):
        raise ValueError("All parameters (memory_id, session_id, actor_id) must be non-empty")
    
    test_messages = [
        ("My name is Mushkush, devops_001. I want to explicitly tell you that my favorite AWS service is Amazon Bedrock. "
         "Please remember this preference for future conversations.", "USER"),
        ("I've noted that Amazon Bedrock is your favorite AWS service! That's a great choice - "
         "Bedrock is AWS's fully managed service for building and scaling generative AI applications "
         "with foundation models from leading AI companies like Anthropic, AI21 Labs, Amazon, "
         "Cohere, Meta, and Stability AI.", "ASSISTANT"),
    ]
    
    try:
        memory_client.create_event(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            messages=test_messages,
        )
    except Exception as e:
        logging.error(f"Failed to create memory event: {e}")
        raise

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
    if not memories:
        print("⚠️ No memories retrieved")
        return
        
    print(f"✅ Retrieved {len(memories)} memories")
    
    for i, memory in enumerate(memories, 1):
        if not isinstance(memory, dict):
            print(f"  Memory {i}: Invalid memory format (not a dictionary)")
            continue
            
        content = memory.get("content", {})
        if not isinstance(content, dict):
            print(f"  Memory {i}: Invalid content format")
            continue
            
        text = content.get("text", "").strip()
        if not text:
            print(f"  Memory {i}: Empty or missing text content")
            continue
            
        # Display with truncation if needed
        display_text = text if len(text) <= TestConfig.MEMORY_PREVIEW_LENGTH else f"{text[:TestConfig.MEMORY_PREVIEW_LENGTH]}..."
        print(f"  Memory {i}: {display_text}")
        
        # Show additional metadata if available
        if "metadata" in memory:
            metadata = memory["metadata"]
            if isinstance(metadata, dict) and metadata:
                print(f"    Metadata: {list(metadata.keys())}")

def run_memory_creation_test(memory_client: MemoryClient, memory_id: str) -> None:
    """Run the memory creation test."""
    print("\n📝 Testing create_event functionality...")
    create_test_event(memory_client, memory_id, TestConfig.TEST_SESSION_ID, TestConfig.TEST_ACTOR_ID)
    print("✅ Successfully created test event in memory")

def run_memory_retrieval_test(memory_client: MemoryClient, memory_id: str) -> List[Dict[str, Any]]:
    """Run the memory retrieval test and return memories."""
    print("\n🔍 Testing memory retrieval...")
    memories = retrieve_test_memories(memory_client, memory_id, TestConfig.TEST_ACTOR_ID)
    display_memories(memories)
    return memories

def test_memory_save() -> TestResult:
    """
    Test if memory interactions are being saved and can be retrieved.
    
    Returns:
        TestResult with success status, memory count, and error details
    """
    print("🔍 Testing Memory Save Functionality")
    print("=" * 50)
    
    try:
        # Setup
        memory_client, memory_id = setup_memory_client()
        print(f"✅ Found memory ID: {memory_id}")
        
        # Run tests
        run_memory_creation_test(memory_client, memory_id)
        memories = run_memory_retrieval_test(memory_client, memory_id)
        
        # Validate results
        memory_count = len(memories) if memories else 0
        if memory_count == 0:
            print("⚠️ Warning: No memories retrieved")
            
        return TestResult(success=True, memory_count=memory_count)
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error during memory testing: {error_msg}")
        logging.exception("Detailed error information")
        return TestResult(success=False, memory_count=0, error_message=error_msg)

def main() -> int:
    """
    Main entry point for the memory test script.
    
    Returns:
        0 if all tests pass, 1 if tests fail
    """
    try:
        result = test_memory_save()
        
        if result.success:
            print(f"\n🎉 Memory save functionality is working correctly!")
            print(f"   Retrieved {result.memory_count} memories from storage")
            return 0
        else:
            print(f"\n❌ Memory save functionality has issues")
            if result.error_message:
                print(f"   Error: {result.error_message}")
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