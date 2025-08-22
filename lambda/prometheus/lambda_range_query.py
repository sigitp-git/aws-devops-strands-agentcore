#!/usr/bin/env python3

"""
AWS Lambda function for Prometheus range queries
Handles PromQL range query execution with SigV4 authentication
"""

import logging
from prometheus_utils import (
    validate_credentials, 
    validate_required_params, 
    validate_workspace_url,
    make_request_with_retry,
    create_success_response,
    create_error_response
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for Prometheus range queries
    
    Expected event structure:
    {
        "workspace_url": "https://aps-workspaces.region.amazonaws.com/workspaces/ws-xxx",
        "region": "us-east-1",
        "query": "rate(cpu_usage_total[5m])",
        "start": "2023-01-01T00:00:00Z",
        "end": "2023-01-01T01:00:00Z",
        "step": "15s"
    }
    """
    try:
        # Validate required parameters
        validate_required_params(event, ['workspace_url', 'query', 'start', 'end', 'step'])
        
        # Validate and clean workspace URL
        workspace_url = validate_workspace_url(event['workspace_url'])
        region = event.get('region', 'us-east-1')
        query = event['query']
        start = event['start']
        end = event['end']
        step = event['step']
        
        # Validate credentials
        validate_credentials()
        
        # Prepare query parameters
        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        
        # Execute range query
        url = f"{workspace_url}/api/v1/query_range"
        logger.info(f"Executing range query: {query} from {start} to {end} with step {step}")
        
        result = make_request_with_retry('GET', url, params=params, region=region)
        
        # Return successful response
        return create_success_response('range_query', result, 
                                     query=query, start=start, end=end, step=step)
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return create_error_response(str(e))