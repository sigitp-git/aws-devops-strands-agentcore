#!/usr/bin/env python3
"""
Test finding workspace by alias.
"""

import boto3
import json

def test_find_by_alias():
    """Test finding workspace by alias."""
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    function_name = 'aws-devops-prometheus-find-workspace'
    
    # Test payload - using one of the aliases we found
    test_payload = {
        "alias": "eks-cluster-kinara-dev_workspace",
        "region": "us-east-1"
    }
    
    print(f"🧪 Testing find by alias: {test_payload['alias']}")
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
        
        if result.get('statusCode') == 200 and 'workspace' in result:
            workspace = result['workspace']
            print(f"\n🎯 Found workspace:")
            print(f"   ID: {workspace['workspaceId']}")
            print(f"   Alias: {workspace['alias']}")
            print(f"   Status: {workspace['status']}")
            print(f"   Endpoint: {workspace['prometheusEndpoint']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error invoking function: {e}")
        return None

if __name__ == "__main__":
    test_find_by_alias()