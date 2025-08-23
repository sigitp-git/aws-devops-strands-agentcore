"""AWS Lambda function for instant PromQL queries.

This function handles single query execution with SigV4 authentication.
Optimized for fast response times (256MB, 30s timeout).
Single responsibility: instant query operations only.
"""

import json
import os
from typing import Any, Dict, Optional
from prometheus_utils import (
    PrometheusClient,
    SecurityValidator,
    get_workspace_details,
    create_error_response,
    create_success_response,
    validate_required_params
)
from consts import DEFAULT_AWS_REGION, DEFAULT_SERVICE_NAME


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for instant PromQL queries.
    
    Expected event body:
    {
        "workspace_id": "ws-12345678-abcd-1234-efgh-123456789012",
        "query": "up",
        "time": "2023-04-01T00:00:00Z" (optional),
        "region": "us-east-1" (optional)
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "data": {
                "resultType": "vector",
                "result": [...]
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
        required_params = ['workspace_id', 'query']
        missing_params = []
        for param in required_params:
            if param not in body or body[param] is None:
                missing_params.append(param)
        
        if missing_params:
            error_msg = f'Missing required parameters: {", ".join(missing_params)}'
            return create_error_response(error_msg, 400)
        
        workspace_id = body['workspace_id']
        query = body['query']
        time_param = body.get('time')
        region = body.get('region', os.getenv('AWS_REGION', DEFAULT_AWS_REGION))
        
        print(f'Executing instant query: {query} for workspace: {workspace_id}')
        
        # Validate query for security
        if not SecurityValidator.validate_string(query, 'query'):
            return create_error_response('Query validation failed: potentially dangerous query pattern detected', 400)
        
        # Get workspace details
        workspace_config = get_workspace_details(workspace_id, region)
        
        # Prepare query parameters
        params = {'query': query}
        if time_param:
            params['time'] = time_param
        
        # Execute query
        result = PrometheusClient.make_request(
            prometheus_url=workspace_config['prometheus_url'],
            endpoint='query',
            params=params,
            region=region,
            service_name=DEFAULT_SERVICE_NAME
        )
        
        print(f'Query executed successfully, result type: {result.get("resultType", "unknown")}')
        return create_success_response(result)
        
    except ValueError as e:
        error_msg = f'Validation error: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 400)
    except Exception as e:
        error_msg = f'Error executing query: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 500)