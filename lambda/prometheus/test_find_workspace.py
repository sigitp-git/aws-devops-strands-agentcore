#!/usr/bin/env python3
"""
Test script for the Prometheus workspace finder Lambda function.

This script tests the lambda_find_workspace function locally without deploying to AWS.
It validates parameter handling, error cases, and response formatting.
"""

import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path to import the Lambda function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lambda_find_workspace import lambda_handler, find_workspace_by_alias, find_workspace_by_id, list_all_workspaces

def create_mock_workspace(workspace_id, alias, status="ACTIVE"):
    """Create a mock workspace object for testing."""
    return {
        'workspaceId': workspace_id,
        'alias': alias,
        'arn': f'arn:aws:aps:us-east-1:123456789012:workspace/{workspace_id}',
        'status': status,
        'prometheusEndpoint': f'https://aps-workspaces.us-east-1.amazonaws.com/workspaces/{workspace_id}',
        'createdAt': '2023-01-01T00:00:00Z',
        'tags': {}
    }

def test_find_by_alias():
    """Test finding workspace by alias."""
    print("🧪 Testing find workspace by alias...")
    
    # Mock workspaces
    mock_workspaces = [
        create_mock_workspace('ws-prod-123', 'production-metrics'),
        create_mock_workspace('ws-dev-456', 'development-metrics'),
        create_mock_workspace('ws-test-789', 'test-metrics')
    ]
    
    with patch('boto3.client') as mock_boto3:
        # Mock AMP client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        mock_client.meta.region_name = 'us-east-1'
        
        # Mock paginator
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {'workspaces': [{'workspaceId': ws['workspaceId']} for ws in mock_workspaces]}
        ]
        
        # Mock describe_workspace calls
        def mock_describe_workspace(workspaceId):
            for ws in mock_workspaces:
                if ws['workspaceId'] == workspaceId:
                    return {'workspace': ws}
            raise Exception(f"Workspace not found: {workspaceId}")
        
        mock_client.describe_workspace.side_effect = mock_describe_workspace
        
        # Test finding existing workspace
        event = {
            'alias': 'production-metrics',
            'region': 'us-east-1'
        }
        
        result = lambda_handler(event, None)
        
        assert result['statusCode'] == 200
        assert 'workspace' in result
        assert result['workspace']['alias'] == 'production-metrics'
        assert result['workspace']['workspaceId'] == 'ws-prod-123'
        print("✅ Find by alias - SUCCESS")
        
        # Test finding non-existent workspace
        event = {
            'alias': 'non-existent-workspace',
            'region': 'us-east-1'
        }
        
        result = lambda_handler(event, None)
        
        assert result['statusCode'] == 404
        assert 'error' in result
        assert 'available_workspaces' in result
        print("✅ Find non-existent alias - SUCCESS")

def test_find_by_workspace_id():
    """Test finding workspace by workspace ID."""
    print("🧪 Testing find workspace by workspace ID...")
    
    # Mock workspaces
    mock_workspaces = [
        create_mock_workspace('ws-prod-123', 'production-metrics'),
        create_mock_workspace('ws-dev-456', 'development-metrics')
    ]
    
    with patch('boto3.client') as mock_boto3:
        # Mock AMP client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        mock_client.meta.region_name = 'us-east-1'
        
        # Mock paginator
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {'workspaces': [{'workspaceId': ws['workspaceId']} for ws in mock_workspaces]}
        ]
        
        # Mock describe_workspace calls
        def mock_describe_workspace(workspaceId):
            for ws in mock_workspaces:
                if ws['workspaceId'] == workspaceId:
                    return {'workspace': ws}
            raise Exception(f"Workspace not found: {workspaceId}")
        
        mock_client.describe_workspace.side_effect = mock_describe_workspace
        
        # Test finding existing workspace
        event = {
            'workspace_id': 'ws-prod-123',
            'region': 'us-east-1'
        }
        
        result = lambda_handler(event, None)
        
        assert result['statusCode'] == 200
        assert 'workspace' in result
        assert result['workspace']['workspaceId'] == 'ws-prod-123'
        print("✅ Find by workspace ID - SUCCESS")

def test_list_all_workspaces():
    """Test listing all workspaces."""
    print("🧪 Testing list all workspaces...")
    
    # Mock workspaces
    mock_workspaces = [
        create_mock_workspace('ws-prod-123', 'production-metrics'),
        create_mock_workspace('ws-dev-456', 'development-metrics'),
        create_mock_workspace('ws-test-789', 'test-metrics')
    ]
    
    with patch('boto3.client') as mock_boto3:
        # Mock AMP client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        mock_client.meta.region_name = 'us-east-1'
        
        # Mock paginator
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {'workspaces': [{'workspaceId': ws['workspaceId']} for ws in mock_workspaces]}
        ]
        
        # Mock describe_workspace calls
        def mock_describe_workspace(workspaceId):
            for ws in mock_workspaces:
                if ws['workspaceId'] == workspaceId:
                    return {'workspace': ws}
            raise Exception(f"Workspace not found: {workspaceId}")
        
        mock_client.describe_workspace.side_effect = mock_describe_workspace
        
        # Test listing all workspaces
        event = {
            'list_all': True,
            'region': 'us-east-1'
        }
        
        result = lambda_handler(event, None)
        
        assert result['statusCode'] == 200
        assert 'workspaces' in result
        assert len(result['workspaces']) == 3
        assert result['count'] == 3
        print("✅ List all workspaces - SUCCESS")

def test_invalid_parameters():
    """Test invalid parameter handling."""
    print("🧪 Testing invalid parameters...")
    
    # Test missing parameters
    event = {}
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 400
    assert 'error' in result
    print("✅ Invalid parameters - SUCCESS")

def test_utility_functions():
    """Test utility functions."""
    print("🧪 Testing utility functions...")
    
    # Mock workspaces
    mock_workspaces = [
        create_mock_workspace('ws-prod-123', 'production-metrics')
    ]
    
    with patch('boto3.client') as mock_boto3:
        # Mock AMP client
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        mock_client.meta.region_name = 'us-east-1'
        
        # Mock paginator
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {'workspaces': [{'workspaceId': ws['workspaceId']} for ws in mock_workspaces]}
        ]
        
        # Mock describe_workspace calls
        def mock_describe_workspace(workspaceId):
            for ws in mock_workspaces:
                if ws['workspaceId'] == workspaceId:
                    return {'workspace': ws}
            raise Exception(f"Workspace not found: {workspaceId}")
        
        mock_client.describe_workspace.side_effect = mock_describe_workspace
        
        # Test find_workspace_by_alias
        workspace = find_workspace_by_alias('production-metrics', 'us-east-1')
        assert workspace is not None
        assert workspace['alias'] == 'production-metrics'
        print("✅ find_workspace_by_alias utility - SUCCESS")
        
        # Test find_workspace_by_id
        workspace = find_workspace_by_id('ws-prod-123', 'us-east-1')
        assert workspace is not None
        assert workspace['workspaceId'] == 'ws-prod-123'
        print("✅ find_workspace_by_id utility - SUCCESS")
        
        # Test list_all_workspaces
        workspaces = list_all_workspaces('us-east-1')
        assert len(workspaces) == 1
        print("✅ list_all_workspaces utility - SUCCESS")

def main():
    """Run all tests."""
    print("🚀 Testing Prometheus Workspace Finder Lambda Function")
    print("=" * 60)
    
    try:
        test_find_by_alias()
        print()
        
        test_find_by_workspace_id()
        print()
        
        test_list_all_workspaces()
        print()
        
        test_invalid_parameters()
        print()
        
        test_utility_functions()
        print()
        
        print("=" * 60)
        print("🎉 All tests passed successfully!")
        print("=" * 60)
        
        # Show example usage
        print("\n💡 Example Usage:")
        print("# Find workspace by alias")
        print('aws lambda invoke --function-name aws-devops-prometheus-find-workspace \\')
        print('  --payload \'{"alias":"production-metrics"}\' response.json')
        print()
        print("# Find workspace by ID")
        print('aws lambda invoke --function-name aws-devops-prometheus-find-workspace \\')
        print('  --payload \'{"workspace_id":"ws-12345678-abcd-1234-efgh-123456789012"}\' response.json')
        print()
        print("# List all workspaces")
        print('aws lambda invoke --function-name aws-devops-prometheus-find-workspace \\')
        print('  --payload \'{"list_all":true}\' response.json')
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()