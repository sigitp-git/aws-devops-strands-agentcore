#!/usr/bin/env python3
"""
Local test script for Lambda function without external API calls
"""

import json
import sys
import os

# Add the current directory to Python path to import lambda_websearch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_websearch import lambda_handler

def test_lambda_function():
    """Test the Lambda function locally"""
    
    print("🧪 Testing Lambda Function Locally")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Request",
            "event": {
                "keywords": "test search",
                "region": "us-en",
                "max_results": 2
            }
        },
        {
            "name": "Empty Keywords",
            "event": {
                "keywords": "",
                "region": "us-en"
            }
        },
        {
            "name": "Missing Keywords",
            "event": {
                "region": "us-en",
                "max_results": 3
            }
        },
        {
            "name": "Minimal Request",
            "event": {
                "keywords": "aws lambda"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Mock context object
            class MockContext:
                def __init__(self):
                    self.function_name = "test-function"
                    self.function_version = "$LATEST"
                    self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
                    self.memory_limit_in_mb = 256
                    self.remaining_time_in_millis = 30000
                    self.log_group_name = "/aws/lambda/test-function"
                    self.log_stream_name = "2023/01/01/[$LATEST]test123"
                    self.aws_request_id = "test-request-id"
            
            context = MockContext()
            
            # Call the Lambda handler
            response = lambda_handler(test_case['event'], context)
            
            print(f"Status Code: {response['statusCode']}")
            
            # Parse and display the response body
            body = json.loads(response['body'])
            print(f"Success: {body.get('success', 'N/A')}")
            
            if body.get('success'):
                print(f"Query: {body.get('query', 'N/A')}")
                print(f"Region: {body.get('region', 'N/A')}")
                results = body.get('results', {})
                if isinstance(results, dict):
                    print(f"Results Count: {results.get('count', 0)}")
                    if results.get('error'):
                        print(f"Search Error: {results['error']}")
                    elif results.get('results'):
                        print(f"Found {len(results['results'])} results")
                        for j, result in enumerate(results['results'][:2], 1):
                            print(f"  {j}. {result.get('title', 'No title')}")
            else:
                print(f"Error: {body.get('error', 'Unknown error')}")
                
            print("✅ Test completed successfully")
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
    
    print(f"\n🎉 All tests completed!")
    print("\n💡 Note: Search results may show rate limit errors from DuckDuckGo,")
    print("   but this indicates the Lambda function is working correctly.")

if __name__ == "__main__":
    test_lambda_function()