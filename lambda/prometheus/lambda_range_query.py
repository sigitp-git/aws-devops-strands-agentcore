"""AWS Lambda function for PromQL range queries over time periods.

This function handles time-series data retrieval with configurable step intervals.
Right-sized resources for data-intensive operations (512MB, 60s timeout).
Single responsibility: range query operations only.
"""

import json
import os
from typing import Any, Dict
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
    """Lambda handler for PromQL range queries.
    
    Expected event body:
    {
        "workspace_id": "ws-12345678-abcd-1234-efgh-123456789012",
        "query": "rate(node_cpu_seconds_total{mode=\"system\"}[5m])",
        "start": "2023-04-01T00:00:00Z",
        "end": "2023-04-01T01:00:00Z",
        "step": "5m",
        "region": "us-east-1" (optional)
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "data": {
                "resultType": "matrix",
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
        required_params = ['workspace_id', 'query', 'start', 'end', 'step']
        missing_params = []
        for param in required_params:
            if param not in body or body[param] is None:
                missing_params.append(param)
        
        if missing_params:
            error_msg = f'Missing required parameters: {", ".join(missing_params)}'
            return create_error_response(error_msg, 400)
        
        workspace_id = body['workspace_id']
        query = body['query']
        start = body['start']
        end = body['end']
        step = body['step']
        region = body.get('region', os.getenv('AWS_REGION', DEFAULT_AWS_REGION))
        
        print(f'Executing range query: {query} from {start} to {end} with step {step} for workspace: {workspace_id}')
        
        # Validate query for security
        if not SecurityValidator.validate_string(query, 'query'):
            return create_error_response('Query validation failed: potentially dangerous query pattern detected', 400)
        
        # Get workspace details
        workspace_config = get_workspace_details(workspace_id, region)
        
        # Prepare query parameters
        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        
        # Execute range query
        result = PrometheusClient.make_request(
            prometheus_url=workspace_config['prometheus_url'],
            endpoint='query_range',
            params=params,
            region=region,
            service_name=DEFAULT_SERVICE_NAME
        )
        
        print(f'Range query executed successfully, result type: {result.get("resultType", "unknown")}')
        return create_success_response(result)
        
    except ValueError as e:
        error_msg = f'Validation error: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 400)
    except Exception as e:
        error_msg = f'Error executing range query: {str(e)}'
        print(error_msg)
        return create_error_response(error_msg, 500)