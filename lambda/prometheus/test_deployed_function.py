#!/usr/bin/env python3
"""
Test the deployed find workspace Lambda function.
"""

import boto3
import json

def test_deployed_function():
    """Test the deployed Lambda function."""
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    function_name = 'aws-devops-prometheus-find-workspace'
    
    # Test payload
    test_payload = {
        "list_all": True,
        "region": "us-east-1"
    }
    
    print(f"🧪 Testing deployed function: {function_name}")
    print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        # Invoke the function
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        # Read the response
        response_payload = response['Payload'].read()
        result = json.loads(response_payload)
        
        print(f"✅ Function invoked successfully!")
        print(f"📊 Status Code: {response['StatusCode']}")
        print(f"📄 Response: {json.dumps(result, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error invoking function: {e}")
        return None

if __name__ == "__main__":
    test_deployed_function()