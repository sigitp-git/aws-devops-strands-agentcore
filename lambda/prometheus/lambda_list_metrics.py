#!/usr/bin/env python3

"""
AWS Lambda function for listing Prometheus metrics
Handles metric discovery with SigV4 authentication
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
    AWS Lambda handler for listing Prometheus metrics
    
    Expected event structure:
    {
        "workspace_url": "https://aps-workspaces.region.amazonaws.com/workspaces/ws-xxx",
        "region": "us-east-1"
    }
    """
    try:
        # Validate required parameters
        validate_required_params(event, ['workspace_url'])
        
        # Validate and clean workspace URL
        workspace_url = validate_workspace_url(event['workspace_url'])
        region = event.get('region', 'us-east-1')
        
        # Validate credentials
        validate_credentials()
        
        # List all available metric names
        url = f"{workspace_url}/api/v1/label/__name__/values"
        logger.info("Listing all available metrics")
        
        result = make_request_with_retry('GET', url, region=region)
        
        # Return successful response
        return create_success_response('list_metrics', result, 
                                     metric_count=len(result.get('data', [])))
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return create_error_response(str(e))