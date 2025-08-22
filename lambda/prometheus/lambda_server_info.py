#!/usr/bin/env python3

"""
AWS Lambda function for Prometheus server information
Handles server configuration and build info retrieval with SigV4 authentication
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
    AWS Lambda handler for Prometheus server information
    
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
        
        logger.info("Getting server configuration")
        
        # Get build info
        build_info = {}
        try:
            build_url = f"{workspace_url}/api/v1/query"
            build_info = make_request_with_retry('GET', build_url, 
                                               params={'query': 'prometheus_build_info'}, 
                                               region=region)
        except Exception as e:
            logger.warning(f"Build info not available: {str(e)}")
            build_info = {"error": f"Build info not available: {str(e)}"}
        
        # Get config (may not be available in managed service)
        config_info = {}
        try:
            config_url = f"{workspace_url}/api/v1/status/config"
            config_info = make_request_with_retry('GET', config_url, region=region)
        except Exception as e:
            logger.warning(f"Config endpoint not available: {str(e)}")
            config_info = {"error": "Config endpoint not available in managed service"}
        
        # Compile server information
        result = {
            "build_info": build_info,
            "config": config_info,
            "workspace_url": workspace_url,
            "region": region
        }
        
        # Return successful response
        return create_success_response('server_info', result)
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return create_error_response(str(e))