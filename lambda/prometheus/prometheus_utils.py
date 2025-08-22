#!/usr/bin/env python3

"""
Shared utilities for Prometheus Lambda functions
Common functions for SigV4 authentication and HTTP requests
"""

import json
import boto3
import requests
import time
import logging
from datetime import datetime, timezone
from urllib.parse import urlencode
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

# Initialize AWS session outside for reuse
session = boto3.Session()
credentials = session.get_credentials()

def validate_credentials():
    """Validate AWS credentials are available"""
    if not credentials:
        raise NoCredentialsError("AWS credentials not found")

def sign_request(method, url, params=None, data=None, region='us-east-1'):
    """
    Sign request with AWS SigV4 authentication
    
    Args:
        method: HTTP method (GET, POST)
        url: Request URL
        params: Query parameters
        data: Request body data
        region: AWS region
        
    Returns:
        Signed AWSRequest object
    """
    if params:
        url += '?' + urlencode(params)
    
    request = AWSRequest(method=method, url=url, data=data)
    SigV4Auth(credentials, 'aps', region).add_auth(request)
    return request

def make_request_with_retry(method, url, params=None, data=None, region='us-east-1', max_retries=3):
    """
    Make HTTP request with exponential backoff retry logic
    
    Args:
        method: HTTP method
        url: Request URL
        params: Query parameters
        data: Request body
        region: AWS region
        max_retries: Maximum number of retries
        
    Returns:
        Response JSON data
        
    Raises:
        Exception: If all retries are exhausted
    """
    for attempt in range(max_retries + 1):
        try:
            # Sign the request
            signed_request = sign_request(method, url, params, data, region)
            
            # Prepare headers
            headers = dict(signed_request.headers)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            # Make the request
            response = requests.request(
                method=signed_request.method,
                url=signed_request.url,
                headers=headers,
                data=signed_request.body,
                timeout=30
            )
            
            # Check for successful response
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + (time.time() % 1)  # Exponential backoff with jitter
                    logger.warning(f"Rate limited, retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    continue
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                wait_time = (2 ** attempt) + (time.time() % 1)
                logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time:.2f} seconds: {str(e)}")
                time.sleep(wait_time)
                continue
            else:
                raise e
    
    raise Exception(f"Max retries ({max_retries}) exceeded")

def create_success_response(operation, data, **kwargs):
    """
    Create standardized success response
    
    Args:
        operation: Operation name
        data: Response data
        **kwargs: Additional fields to include
        
    Returns:
        Lambda response dictionary
    """
    response_body = {
        'success': True,
        'operation': operation,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data': data
    }
    
    # Add any additional fields
    response_body.update(kwargs)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response_body, default=str)
    }

def create_error_response(error_message, status_code=500):
    """
    Create standardized error response
    
    Args:
        error_message: Error message string
        status_code: HTTP status code
        
    Returns:
        Lambda error response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': str(error_message),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }

def validate_workspace_url(workspace_url):
    """
    Validate AWS Managed Prometheus workspace URL format
    
    Args:
        workspace_url: Workspace URL to validate
        
    Returns:
        Cleaned workspace URL (without trailing slash)
        
    Raises:
        ValueError: If URL format is invalid
    """
    if not workspace_url:
        raise ValueError("Workspace URL is required")
    
    # Expected format: https://aps-workspaces.{region}.amazonaws.com/workspaces/{workspace-id}
    import re
    pattern = r'^https://aps-workspaces\.[a-z0-9-]+\.amazonaws\.com/workspaces/ws-[a-f0-9-]+$'
    
    cleaned_url = workspace_url.rstrip('/')
    if not re.match(pattern, cleaned_url):
        raise ValueError(f"Invalid workspace URL format: {workspace_url}")
    
    return cleaned_url

def validate_required_params(event, required_params):
    """
    Validate required parameters are present in event
    
    Args:
        event: Lambda event dictionary
        required_params: List of required parameter names
        
    Raises:
        ValueError: If any required parameters are missing
    """
    missing_params = [p for p in required_params if p not in event]
    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")