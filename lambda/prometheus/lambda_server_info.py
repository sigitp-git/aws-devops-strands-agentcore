"""AWS Lambda function for server configuration and build information.

This function retrieves Prometheus server status and configuration details.
Optimized for configuration queries (256MB, 30s timeout).
Single responsibility: server information only.
"""

import json
import os
from typing import Any, Dict
from prometheus_utils import (
    get_workspace_details,
    create_error_response,
    create_success_response,
    validate_required_params
)
from consts import DEFAULT_AWS_REGION, DEFAULT_SERVICE_NAME


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for retrieving server information.
    
    Expected event body:
    {
        "workspace_id": "ws-12345678-abcd-1234-efgh-123456789012",
        "region": "us-east-1" (optional)
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "data": {
                "prometheus_url": "https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-12345678-abcd-1234-efgh-123456789012",
                "aws_region": "us-east-1",
                "service_name": "aps",
                "workspace_id": "ws-12345678-abcd-1234-efgh-123456789012",
                "workspace_alias": "production",
                "workspace_status": "ACTIVE"
            },
            "success": true
        }
    }
    """
    try:
        print(f'Received event: {json.dumps(event)}')
        
        # Handle both direct parameter passing (MCP gateway) and nested body format
        if 'body' in event and event['body']:
            # Traditional Lambda invocation with body
            body = event['body']
            if isinstance(body, str):
                body = json.loads(body)
        else:
            # Direct parameter passing (MCP gateway format)
            body = event
        
        # Validate required parameters
        required_params = ['workspace_id']
        missing_params = []
        for param in required_params:
            if param not in body or body[param] is None:
                missing_params.append(param)
        
        if missing_params:
            error_msg = f'Missing required parameters: {", ".join(missing_params)}'
            return create_error_response(error_msg, 400)
        
        workspace_id = body['workspace_id']
        region = body.get('region', os.getenv('AWS_REGION', DEFAULT_AWS_REGION))
        
        print(f'Retrieving server info for workspace: {workspace_id}')
        
        # Get workspace details
        workspace_config = get_workspace_details(workspace_id, region)
        
        # Prepare server information response
        server_info = {
            'prometheus_url': workspace_config['prometheus_url'],
            'aws_region': region,
            'service_name': DEFAULT_SERVICE_NAME,
            'workspace_id': workspace_id,
            'workspace_alias': workspace_config.get('alias', 'No alias'),
            'workspace_status': workspace_config.get('status', 'UNKNOWN')
        }
        
        print(f'Server info retrieved successfully for workspace: {workspace_id}')
        return create_success_response(server_info)
        
    except ValueError as e:
        error_msg = f'Validation error: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 400)
    except Exception as e:
        error_msg = f'Error retrieving server info: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 500)