#!/usr/bin/env python3

"""
AWS Lambda function for Prometheus instant queries
Handles single PromQL query execution with SigV4 authentication
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
    AWS Lambda handler for Prometheus instant queries
    
    Expected event structure:
    {
        "workspace_url": "https://aps-workspaces.region.amazonaws.com/workspaces/ws-xxx",
        "region": "us-east-1",
        "query": "up",
        "time": "2023-01-01T00:00:00Z"  # Optional
    }
    """
    try:
        # Validate required parameters
        validate_required_params(event, ['workspace_url', 'query'])
        
        # Validate and clean workspace URL
        workspace_url = validate_workspace_url(event['workspace_url'])
        region = event.get('region', 'us-east-1')
        query = event['query']
        time_param = event.get('time')
        
        # Validate credentials
        validate_credentials()
        
        # Prepare query parameters
        params = {'query': query}
        if time_param:
            params['time'] = time_param
        
        # Execute query
        url = f"{workspace_url}/api/v1/query"
        logger.info(f"Executing instant query: {query}")
        
        result = make_request_with_retry('GET', url, params=params, region=region)
        
        # Return successful response
        return create_success_response('query', result, query=query)
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return create_error_response(str(e))