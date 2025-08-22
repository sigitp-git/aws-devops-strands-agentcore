#!/usr/bin/env python3
"""
AWS Lambda function to find Prometheus workspace endpoint URL based on alias/name.

This function searches for Amazon Managed Service for Prometheus workspaces
by alias or workspace ID and returns the endpoint URL for connecting to the workspace.

Features:
- Search by workspace alias (friendly name)
- Search by workspace ID
- List all available workspaces
- Return workspace details including endpoint URL
- Comprehensive error handling and validation
"""

import json
import boto3
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler to find Prometheus workspace endpoint URL.
    
    Expected event format:
    {
        "alias": "production-metrics",           # Optional: workspace alias to search for
        "workspace_id": "ws-12345678-abcd-...", # Optional: specific workspace ID
        "region": "us-east-1",                  # Optional: AWS region (defaults to current)
        "list_all": false                       # Optional: list all workspaces
    }
    
    Returns:
    {
        "statusCode": 200,
        "workspace": {
            "workspaceId": "ws-12345678-abcd-1234-efgh-123456789012",
            "alias": "production-metrics",
            "arn": "arn:aws:aps:us-east-1:123456789012:workspace/ws-12345678-abcd-1234-efgh-123456789012",
            "status": "ACTIVE",
            "prometheusEndpoint": "https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-12345678-abcd-1234-efgh-123456789012",
            "createdAt": "2023-01-01T00:00:00Z",
            "tags": {}
        },
        "workspaces": [...],  # Only when list_all=true
        "message": "Found workspace by alias: production-metrics"
    }
    """
    
    try:
        # Extract parameters from event
        alias = event.get('alias')
        workspace_id = event.get('workspace_id')
        region = event.get('region')
        list_all = event.get('list_all', False)
        
        # Validate input
        if not list_all and not alias and not workspace_id:
            return {
                'statusCode': 400,
                'error': 'Must provide either alias, workspace_id, or set list_all=true',
                'message': 'Invalid request parameters'
            }
        
        # Initialize AMP client
        if region:
            amp_client = boto3.client('amp', region_name=region)
        else:
            amp_client = boto3.client('amp')
            region = amp_client.meta.region_name
        
        logger.info(f"Searching for Prometheus workspace in region: {region}")
        
        # List all workspaces
        workspaces = []
        paginator = amp_client.get_paginator('list_workspaces')
        
        for page in paginator.paginate():
            for workspace in page['workspaces']:
                # Get detailed workspace information
                workspace_detail = amp_client.describe_workspace(
                    workspaceId=workspace['workspaceId']
                )['workspace']
                
                # Build workspace info with endpoint URL
                workspace_info = {
                    'workspaceId': workspace_detail['workspaceId'],
                    'alias': workspace_detail.get('alias', ''),
                    'arn': workspace_detail['arn'],
                    'status': workspace_detail['status'],
                    'prometheusEndpoint': workspace_detail['prometheusEndpoint'],
                    'createdAt': workspace_detail['createdAt'].isoformat() if hasattr(workspace_detail['createdAt'], 'isoformat') else str(workspace_detail['createdAt']),
                    'tags': workspace_detail.get('tags', {})
                }
                
                workspaces.append(workspace_info)
        
        logger.info(f"Found {len(workspaces)} workspaces")
        
        # If list_all is requested, return all workspaces
        if list_all:
            return {
                'statusCode': 200,
                'workspaces': workspaces,
                'count': len(workspaces),
                'message': f'Found {len(workspaces)} Prometheus workspaces in {region}'
            }
        
        # Search for specific workspace
        found_workspace = None
        search_criteria = None
        
        if workspace_id:
            # Search by workspace ID
            for workspace in workspaces:
                if workspace['workspaceId'] == workspace_id:
                    found_workspace = workspace
                    search_criteria = f"workspace ID: {workspace_id}"
                    break
        elif alias:
            # Search by alias (case-insensitive)
            alias_lower = alias.lower()
            for workspace in workspaces:
                workspace_alias = workspace.get('alias', '').lower()
                if workspace_alias == alias_lower:
                    found_workspace = workspace
                    search_criteria = f"alias: {alias}"
                    break
        
        if found_workspace:
            logger.info(f"Found workspace by {search_criteria}")
            return {
                'statusCode': 200,
                'workspace': found_workspace,
                'message': f'Found workspace by {search_criteria}'
            }
        else:
            search_term = workspace_id if workspace_id else alias
            search_type = "workspace ID" if workspace_id else "alias"
            
            logger.warning(f"Workspace not found by {search_type}: {search_term}")
            return {
                'statusCode': 404,
                'error': f'Workspace not found by {search_type}: {search_term}',
                'available_workspaces': [
                    {
                        'workspaceId': ws['workspaceId'],
                        'alias': ws.get('alias', ''),
                        'status': ws['status']
                    } for ws in workspaces
                ],
                'message': f'No workspace found matching {search_type}: {search_term}'
            }
    
    except Exception as e:
        logger.error(f"Error finding Prometheus workspace: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'message': 'Internal server error while finding workspace'
        }

def find_workspace_by_alias(alias: str, region: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Utility function to find workspace by alias.
    Can be used by other Lambda functions or applications.
    """
    event = {
        'alias': alias,
        'region': region
    }
    
    result = lambda_handler(event, None)
    
    if result['statusCode'] == 200 and 'workspace' in result:
        return result['workspace']
    
    return None

def find_workspace_by_id(workspace_id: str, region: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Utility function to find workspace by ID.
    Can be used by other Lambda functions or applications.
    """
    event = {
        'workspace_id': workspace_id,
        'region': region
    }
    
    result = lambda_handler(event, None)
    
    if result['statusCode'] == 200 and 'workspace' in result:
        return result['workspace']
    
    return None

def list_all_workspaces(region: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Utility function to list all workspaces.
    Can be used by other Lambda functions or applications.
    """
    event = {
        'list_all': True,
        'region': region
    }
    
    result = lambda_handler(event, None)
    
    if result['statusCode'] == 200 and 'workspaces' in result:
        return result['workspaces']
    
    return []

# Example usage for testing
if __name__ == "__main__":
    # Test cases
    test_events = [
        # Find by alias
        {
            "alias": "production-metrics",
            "region": "us-east-1"
        },
        # Find by workspace ID
        {
            "workspace_id": "ws-12345678-abcd-1234-efgh-123456789012",
            "region": "us-east-1"
        },
        # List all workspaces
        {
            "list_all": True,
            "region": "us-east-1"
        }
    ]
    
    for i, event in enumerate(test_events, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Event: {json.dumps(event, indent=2)}")
        
        result = lambda_handler(event, None)
        print(f"Result: {json.dumps(result, indent=2, default=str)}")