#!/usr/bin/env python3
"""
Test suite for the Prometheus Lambda Integration Layer.

This script tests the integration layer that provides a unified interface
to all Prometheus Lambda functions.
"""

import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path to import the integration layer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lambda_integration import PrometheusLambdaIntegration, PrometheusOperation, lambda_handler, create_integration_client

def test_integration_client_creation():
    """Test creating integration client."""
    print("🧪 Testing integration client creation...")
    
    # Test default region
    client = create_integration_client()
    assert client.region == "us-east-1"
    assert len(client.function_names) == 5
    print("✅ Default client creation - SUCCESS")
    
    # Test custom region
    client = create_integration_client("us-west-2")
    assert client.region == "us-west-2"
    print("✅ Custom region client creation - SUCCESS")

def test_operation_routing():
    """Test operation routing to correct Lambda functions."""
    print("🧪 Testing operation routing...")
    
    with patch('boto3.client') as mock_boto3:
        # Mock Lambda client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Mock successful Lambda response
        mock_response = {
            'Payload': Mock()
        }
        mock_response['Payload'].read.return_value = json.dumps({
            'statusCode': 200,
            'body': {'success': True, 'data': 'test_data'}
        }).encode('utf-8')
        mock_client.invoke.return_value = mock_response
        
        # Create integration client
        integration = PrometheusLambdaIntegration()
        
        # Test each operation
        operations_to_test = [
            ('query', {'workspace_url': 'test', 'query': 'up'}),
            ('range_query', {'workspace_url': 'test', 'query': 'up', 'start': '2023-01-01T00:00:00Z', 'end': '2023-01-01T01:00:00Z', 'step': '15s'}),
            ('list_metrics', {'workspace_url': 'test'}),
            ('server_info', {'workspace_url': 'test'}),
            ('find_workspace', {'list_all': True})
        ]
        
        for operation, parameters in operations_to_test:
            result = integration.execute_operation(operation, parameters)
            
            # Verify the function was called
            assert mock_client.invoke.called
            
            # Verify correct function name was used
            call_args = mock_client.invoke.call_args
            expected_function = integration.function_names[PrometheusOperation(operation)]
            assert call_args[1]['FunctionName'] == expected_function
            
            # Verify integration metadata was added
            assert 'integration_info' in result
            assert result['integration_info']['operation'] == operation
            
            print(f"✅ {operation} routing - SUCCESS")
            
            # Reset mock for next test
            mock_client.reset_mock()

def test_convenience_methods():
    """Test convenience methods for each operation."""
    print("🧪 Testing convenience methods...")
    
    with patch('boto3.client') as mock_boto3:
        # Mock Lambda client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Mock successful Lambda response
        mock_response = {
            'Payload': Mock()
        }
        mock_response['Payload'].read.return_value = json.dumps({
            'statusCode': 200,
            'body': {'success': True}
        }).encode('utf-8')
        mock_client.invoke.return_value = mock_response
        
        # Create integration client
        integration = PrometheusLambdaIntegration()
        
        # Test query method
        result = integration.query('test_url', 'up', '2023-01-01T00:00:00Z')
        assert mock_client.invoke.called
        print("✅ query() method - SUCCESS")
        
        mock_client.reset_mock()
        
        # Test range_query method
        result = integration.range_query('test_url', 'up', '2023-01-01T00:00:00Z', '2023-01-01T01:00:00Z', '15s')
        assert mock_client.invoke.called
        print("✅ range_query() method - SUCCESS")
        
        mock_client.reset_mock()
        
        # Test list_metrics method
        result = integration.list_metrics('test_url')
        assert mock_client.invoke.called
        print("✅ list_metrics() method - SUCCESS")
        
        mock_client.reset_mock()
        
        # Test server_info method
        result = integration.server_info('test_url')
        assert mock_client.invoke.called
        print("✅ server_info() method - SUCCESS")
        
        mock_client.reset_mock()
        
        # Test find_workspace method
        result = integration.find_workspace(alias='test-workspace')
        assert mock_client.invoke.called
        print("✅ find_workspace() method - SUCCESS")

def test_error_handling():
    """Test error handling in the integration layer."""
    print("🧪 Testing error handling...")
    
    with patch('boto3.client') as mock_boto3:
        # Mock Lambda client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Create integration client
        integration = PrometheusLambdaIntegration()
        
        # Test unsupported operation
        result = integration.execute_operation('unsupported_operation', {})
        assert result['statusCode'] == 400
        assert 'Unsupported operation' in result['error']
        print("✅ Unsupported operation error - SUCCESS")
        
        # Test Lambda invocation error
        mock_client.invoke.side_effect = Exception("Lambda invocation failed")
        result = integration.execute_operation('query', {'workspace_url': 'test', 'query': 'up'})
        assert result['statusCode'] == 500
        assert 'Lambda invocation failed' in result['error']
        print("✅ Lambda invocation error - SUCCESS")

def test_lambda_handler():
    """Test the Lambda handler for the integration layer."""
    print("🧪 Testing Lambda handler...")
    
    with patch('boto3.client') as mock_boto3:
        # Mock Lambda client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Mock successful Lambda response
        mock_response = {
            'Payload': Mock()
        }
        mock_response['Payload'].read.return_value = json.dumps({
            'statusCode': 200,
            'body': {'success': True}
        }).encode('utf-8')
        mock_client.invoke.return_value = mock_response
        
        # Test valid event
        event = {
            'operation': 'query',
            'parameters': {
                'workspace_url': 'test',
                'query': 'up'
            }
        }
        
        result = lambda_handler(event, None)
        assert result['statusCode'] == 200
        print("✅ Valid Lambda handler event - SUCCESS")
        
        # Test missing operation
        event = {
            'parameters': {
                'workspace_url': 'test',
                'query': 'up'
            }
        }
        
        result = lambda_handler(event, None)
        assert result['statusCode'] == 400
        assert 'Missing required field: operation' in result['error']
        print("✅ Missing operation error - SUCCESS")

def test_function_name_mappings():
    """Test that all function name mappings are correct."""
    print("🧪 Testing function name mappings...")
    
    integration = PrometheusLambdaIntegration()
    
    expected_mappings = {
        PrometheusOperation.QUERY: "aws-devops-prometheus-query",
        PrometheusOperation.RANGE_QUERY: "aws-devops-prometheus-range-query",
        PrometheusOperation.LIST_METRICS: "aws-devops-prometheus-list-metrics",
        PrometheusOperation.SERVER_INFO: "aws-devops-prometheus-server-info",
        PrometheusOperation.FIND_WORKSPACE: "aws-devops-prometheus-find-workspace"
    }
    
    for operation, expected_name in expected_mappings.items():
        actual_name = integration.function_names[operation]
        assert actual_name == expected_name
        print(f"✅ {operation.value} -> {expected_name} - SUCCESS")

def main():
    """Run all tests."""
    print("🚀 Testing Prometheus Lambda Integration Layer")
    print("=" * 60)
    
    try:
        test_integration_client_creation()
        print()
        
        test_function_name_mappings()
        print()
        
        test_operation_routing()
        print()
        
        test_convenience_methods()
        print()
        
        test_error_handling()
        print()
        
        test_lambda_handler()
        print()
        
        print("=" * 60)
        print("🎉 All integration layer tests passed successfully!")
        print("=" * 60)
        
        # Show example usage
        print("\n💡 Example Usage:")
        print("# Create integration client")
        print("integration = create_integration_client('us-east-1')")
        print()
        print("# Execute operations")
        print("result = integration.query('workspace_url', 'up')")
        print("result = integration.find_workspace(list_all=True)")
        print()
        print("# Use as Lambda function")
        print('event = {"operation": "query", "parameters": {"workspace_url": "...", "query": "up"}}')
        print("result = lambda_handler(event, context)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()