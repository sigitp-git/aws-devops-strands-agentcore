"""Shared utilities for Prometheus Lambda functions.

This module provides common functionality for AWS SigV4 authentication, security validation,
and Prometheus API interactions.
"""

import json
import os
import time
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Any, Dict, Optional, List
from consts import (
    DEFAULT_AWS_REGION,
    DEFAULT_SERVICE_NAME,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
    API_VERSION_PATH,
    DANGEROUS_PATTERNS
)


class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_string(value: str, context: str = 'value') -> bool:
        """Validate a string for potential security issues."""
        if not isinstance(value, str):
            return True
            
        for pattern in DANGEROUS_PATTERNS:
            if pattern in value:
                print(f'Potentially dangerous {context} detected: {pattern}')
                return False
        return True
    
    @staticmethod
    def validate_params(params: Dict) -> bool:
        """Validate request parameters for security issues."""
        if not params:
            return True
            
        for key, value in params.items():
            if isinstance(value, str) and not SecurityValidator.validate_string(value, f'parameter {key}'):
                return False
        return True


class PrometheusClient:
    """Client for interacting with Prometheus API with AWS SigV4 authentication."""
    
    @staticmethod
    def make_request(
        prometheus_url: str,
        endpoint: str,
        params: Optional[Dict] = None,
        region: str = DEFAULT_AWS_REGION,
        profile: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: int = DEFAULT_RETRY_DELAY,
        service_name: str = DEFAULT_SERVICE_NAME,
    ) -> Any:
        """Make authenticated request to Prometheus API."""
        
        if not prometheus_url:
            raise ValueError('Prometheus URL not configured')
        
        # Security validation
        if not isinstance(endpoint, str) or not SecurityValidator.validate_string(endpoint, 'endpoint'):
            raise ValueError('Invalid endpoint')
            
        if params and not SecurityValidator.validate_params(params):
            raise ValueError('Invalid parameters: potentially dangerous values detected')
        
        # Build URL
        base_url = prometheus_url
        if not base_url.endswith(API_VERSION_PATH):
            base_url = f'{base_url.rstrip("/")}{API_VERSION_PATH}'
        url = f'{base_url}/{endpoint.lstrip("/")}'
        
        # Retry logic
        retry_count = 0
        last_exception = None
        
        while retry_count < max_retries:
            try:
                # Create session and credentials
                session = boto3.Session(profile_name=profile, region_name=region)
                credentials = session.get_credentials()
                if not credentials:
                    raise ValueError('AWS credentials not found')
                
                # Create and sign request
                aws_request = AWSRequest(method='GET', url=url, params=params or {})
                SigV4Auth(credentials, service_name, region).add_auth(aws_request)
                
                # Convert to requests format
                prepared_request = requests.Request(
                    method=aws_request.method,
                    url=aws_request.url,
                    headers=dict(aws_request.headers),
                    params=params or {},
                ).prepare()
                
                # Send request
                with requests.Session() as req_session:
                    response = req_session.send(prepared_request)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data['status'] != 'success':
                        error_msg = data.get('error', 'Unknown error')
                        raise RuntimeError(f'Prometheus API request failed: {error_msg}')
                    
                    return data['data']
                    
            except (requests.RequestException, json.JSONDecodeError) as e:
                last_exception = e
                retry_count += 1
                if retry_count < max_retries:
                    retry_delay_seconds = retry_delay * (2 ** (retry_count - 1))
                    print(f'Request failed: {e}. Retrying in {retry_delay_seconds}s...')
                    time.sleep(retry_delay_seconds)
                else:
                    print(f'Request failed after {max_retries} attempts: {e}')
                    raise
        
        if last_exception:
            raise last_exception
        return None


def get_workspace_details(workspace_id: str, region: str = DEFAULT_AWS_REGION) -> Dict[str, Any]:
    """Get details for a specific Prometheus workspace using DescribeWorkspace API."""
    config = Config(user_agent_extra='prometheus-lambda-function')
    session = boto3.Session(region_name=region)
    aps_client = session.client('amp', config=config)

    try:
        response = aps_client.describe_workspace(workspaceId=workspace_id)
        workspace = response.get('workspace', {})

        prometheus_url = workspace.get('prometheusEndpoint')
        if not prometheus_url:
            raise ValueError(f'No prometheusEndpoint found in workspace response for {workspace_id}')

        return {
            'workspace_id': workspace_id,
            'alias': workspace.get('alias', 'No alias'),
            'status': workspace.get('status', {}).get('statusCode', 'UNKNOWN'),
            'prometheus_url': prometheus_url,
            'region': region,
        }
    except Exception as e:
        print(f'Error in DescribeWorkspace API: {str(e)}')
        raise


def create_error_response(error_message: str, status_code: int = 500) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({
            'error': error_message,
            'success': False
        })
    }


def create_success_response(data: Any) -> Dict[str, Any]:
    """Create a standardized success response."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({
            'data': data,
            'success': True
        })
    }


def validate_required_params(event: Dict, required_params: List[str]) -> Optional[str]:
    """Validate that required parameters are present in the event.
    
    Handles both direct parameter passing (MCP gateway) and nested body format.
    """
    # Handle both direct parameter passing (MCP gateway) and nested body format
    if 'body' in event and event['body']:
        # Traditional Lambda invocation with body
        body = event['body']
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return 'Invalid JSON in request body'
    else:
        # Direct parameter passing (MCP gateway format)
        body = event
    
    missing_params = []
    for param in required_params:
        if param not in body or body[param] is None:
            missing_params.append(param)
    
    if missing_params:
        return f'Missing required parameters: {", ".join(missing_params)}'
    
    return None
