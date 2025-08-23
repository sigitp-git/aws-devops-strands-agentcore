"""AWS Lambda function for metric discovery and listing.

This function retrieves all available metric names from Prometheus workspace.
Lightweight function for metadata operations (256MB, 30s timeout).
Single responsibility: metric discovery only.
"""

import json
import os
from typing import Any, Dict
from prometheus_utils import (
    PrometheusClient,
    get_workspace_details,
    create_error_response,
    create_success_response,
    validate_required_params
)
from consts import DEFAULT_AWS_REGION, DEFAULT_SERVICE_NAME


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for listing available metrics.
    
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
                "metrics": [
                    "go_gc_duration_seconds",
                    "go_goroutines",
                    "http_requests_total",
                    ...
                ]
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
        
        print(f'Listing metrics for workspace: {workspace_id}')
        
        # Get workspace details
        workspace_config = get_workspace_details(workspace_id, region)
        
        # List all available metrics
        result = PrometheusClient.make_request(
            prometheus_url=workspace_config['prometheus_url'],
            endpoint='label/__name__/values',
            params={},
            region=region,
            service_name=DEFAULT_SERVICE_NAME
        )
        
        # Sort metrics for better usability
        metrics = sorted(result) if isinstance(result, list) else []
        
        print(f'Retrieved {len(metrics)} metrics successfully')
        return create_success_response({'metrics': metrics})
        
    except ValueError as e:
        error_msg = f'Validation error: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 400)
    except Exception as e:
        error_msg = f'Error listing metrics: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 500)