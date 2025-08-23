#!/usr/bin/env python3
"""
Test script to verify parameter handling in Prometheus Lambda functions.
Tests both MCP gateway format (direct parameters) and traditional Lambda format (nested body).
"""

import json
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_query import lambda_handler as query_handler
from lambda_range_query import lambda_handler as range_query_handler
from lambda_list_metrics import lambda_handler as list_metrics_handler
from lambda_server_info import lambda_handler as server_info_handler


def test_mcp_gateway_format():
    """Test direct parameter passing (MCP gateway format)."""
    print("🔍 Testing MCP Gateway Format (Direct Parameters)")
    
    # Test query function with direct parameters
    mcp_event = {
        "workspace_id": "ws-484afeca-566c-4932-8f04-828f652995c9",
        "query": "up",
        "region": "us-east-1"
    }
    
    print("   Testing query function...")
    try:
        result = query_handler(mcp_event, None)
        print(f"   ✅ Query function handled MCP format: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ Query function failed: {e}")
    
    # Test range query function
    range_event = {
        "workspace_id": "ws-484afeca-566c-4932-8f04-828f652995c9",
        "query": "rate(cpu_usage[5m])",
        "start": "2023-01-01T00:00:00Z",
        "end": "2023-01-01T01:00:00Z",
        "step": "5m",
        "region": "us-east-1"
    }
    
    print("   Testing range query function...")
    try:
        result = range_query_handler(range_event, None)
        print(f"   ✅ Range query function handled MCP format: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ Range query function failed: {e}")
    
    # Test list metrics function
    metrics_event = {
        "workspace_id": "ws-484afeca-566c-4932-8f04-828f652995c9",
        "region": "us-east-1"
    }
    
    print("   Testing list metrics function...")
    try:
        result = list_metrics_handler(metrics_event, None)
        print(f"   ✅ List metrics function handled MCP format: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ List metrics function failed: {e}")
    
    # Test server info function
    print("   Testing server info function...")
    try:
        result = server_info_handler(metrics_event, None)
        print(f"   ✅ Server info function handled MCP format: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ Server info function failed: {e}")


def test_traditional_lambda_format():
    """Test nested body format (traditional Lambda)."""
    print("\n🔍 Testing Traditional Lambda Format (Nested Body)")
    
    # Test query function with nested body
    lambda_event = {
        "body": json.dumps({
            "workspace_id": "ws-484afeca-566c-4932-8f04-828f652995c9",
            "query": "up",
            "region": "us-east-1"
        })
    }
    
    print("   Testing query function...")
    try:
        result = query_handler(lambda_event, None)
        print(f"   ✅ Query function handled Lambda format: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ Query function failed: {e}")
    
    # Test with object body (not string)
    lambda_event_obj = {
        "body": {
            "workspace_id": "ws-484afeca-566c-4932-8f04-828f652995c9",
            "query": "up",
            "region": "us-east-1"
        }
    }
    
    print("   Testing query function with object body...")
    try:
        result = query_handler(lambda_event_obj, None)
        print(f"   ✅ Query function handled object body: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ Query function failed: {e}")


def test_missing_parameters():
    """Test parameter validation."""
    print("\n🔍 Testing Parameter Validation")
    
    # Test missing required parameters
    incomplete_event = {
        "workspace_id": "ws-484afeca-566c-4932-8f04-828f652995c9"
        # Missing 'query' parameter
    }
    
    print("   Testing missing query parameter...")
    try:
        result = query_handler(incomplete_event, None)
        if result['statusCode'] == 400:
            print("   ✅ Correctly rejected missing parameter")
        else:
            print(f"   ❌ Unexpected response: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    # Test completely empty event
    empty_event = {}
    
    print("   Testing empty event...")
    try:
        result = query_handler(empty_event, None)
        if result['statusCode'] == 400:
            print("   ✅ Correctly rejected empty event")
        else:
            print(f"   ❌ Unexpected response: {result['statusCode']}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def main():
    """Run all parameter handling tests."""
    print("🚀 Testing Prometheus Lambda Parameter Handling")
    print("=" * 60)
    
    test_mcp_gateway_format()
    test_traditional_lambda_format()
    test_missing_parameters()
    
    print("\n" + "=" * 60)
    print("✅ Parameter handling tests completed!")
    print("\nNote: These tests validate parameter parsing logic.")
    print("Actual Prometheus API calls will fail without valid workspace IDs.")


if __name__ == "__main__":
    main()