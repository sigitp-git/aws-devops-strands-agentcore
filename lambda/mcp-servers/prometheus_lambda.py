"""
Prometheus MCP Server as Lambda Function

This is a unified Lambda function that consolidates all Prometheus operations
ported from the official awslabs.prometheus-mcp-server and the existing
microservices architecture in lambda/prometheus/.

Supports:
- ExecuteQuery: Instant PromQL queries
- ExecuteRangeQuery: Range queries over time periods  
- ListMetrics: Metric discovery and listing
- GetServerInfo: Server configuration and build information
- GetAvailableWorkspaces: List all available Prometheus workspaces
"""
import json
import logging
import os
import time
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Any, Dict, Optional, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
DEFAULT_AWS_REGION = 'us-east-1'
DEFAULT_SERVICE_NAME = 'aps'
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1  # seconds
API_VERSION_PATH = '/api/v1'

# Security patterns to block
DANGEROUS_PATTERNS = [
    ';', '&&', '||', '`', '$(', '${',
    'file://', '/etc/', '/var/log',
    'http://', 'https://'
]


class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_string(value: str, context: str = 'value') -> bool:
        """Validate a string for potential security issues."""
        if not isinstance(value, str):
            return True
            
        for pattern in DANGEROUS_PATTERNS:
            if pattern in value:
                logger.warning(f'Potentially dangerous {context} detected: {pattern}')
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
                    logger.info(f'Request failed: {e}. Retrying in {retry_delay_seconds}s...')
                    time.sleep(retry_delay_seconds)
                else:
                    logger.error(f'Request failed after {max_retries} attempts: {e}')
                    raise
        
        if last_exception:
            raise last_exception
        return None


class PrometheusServer:
    """Prometheus MCP Server operations."""
    
    def __init__(self, region: str = DEFAULT_AWS_REGION):
        self.region = region
        self.aps_client = boto3.client('amp', region_name=region)
    
    def get_workspace_details(self, workspace_id: str) -> Dict[str, Any]:
        """Get details for a specific Prometheus workspace using DescribeWorkspace API."""
        try:
            response = self.aps_client.describe_workspace(workspaceId=workspace_id)
            workspace = response.get('workspace', {})

            prometheus_url = workspace.get('prometheusEndpoint')
            if not prometheus_url:
                raise ValueError(f'No prometheusEndpoint found in workspace response for {workspace_id}')

            return {
                'workspace_id': workspace_id,
                'alias': workspace.get('alias', 'No alias'),
                'status': workspace.get('status', {}).get('statusCode', 'UNKNOWN'),
                'prometheus_url': prometheus_url,
                'region': self.region,
            }
        except Exception as e:
            logger.error(f'Error in DescribeWorkspace API: {str(e)}')
            raise
    
    def get_available_workspaces(self, profile: Optional[str] = None) -> Dict[str, Any]:
        """List all available Prometheus workspaces in the specified region."""
        try:
            response = self.aps_client.list_workspaces()
            workspaces = []
            
            for workspace in response.get('workspaces', []):
                workspace_id = workspace.get('workspaceId')
                if workspace_id:
                    try:
                        # Get detailed workspace info
                        details = self.get_workspace_details(workspace_id)
                        workspaces.append({
                            'workspace_id': workspace_id,
                            'alias': details.get('alias', 'No alias'),
                            'status': details.get('status', 'UNKNOWN'),
                            'prometheus_url': details.get('prometheus_url'),
                            'is_configured': True,  # All workspaces are considered configured
                        })
                    except Exception as e:
                        logger.warning(f'Failed to get details for workspace {workspace_id}: {e}')
                        # Add basic info even if details fail
                        workspaces.append({
                            'workspace_id': workspace_id,
                            'alias': workspace.get('alias', 'No alias'),
                            'status': workspace.get('status', {}).get('statusCode', 'UNKNOWN'),
                            'prometheus_url': None,
                            'is_configured': False,
                        })
            
            return {
                'workspaces': workspaces,
                'count': len(workspaces),
                'region': self.region,
                'requires_user_selection': len(workspaces) > 1,
                'configured_workspace_id': workspaces[0]['workspace_id'] if workspaces else None
            }
            
        except Exception as e:
            logger.error(f'Failed to list workspaces: {e}')
            return {
                'workspaces': [],
                'count': 0,
                'region': self.region,
                'requires_user_selection': False,
                'configured_workspace_id': None,
                'error': str(e)
            }
    
    def execute_query(self, workspace_id: str, query: str, time_param: Optional[str] = None) -> Dict[str, Any]:
        """Execute an instant PromQL query."""
        logger.info(f'Executing instant query: {query} for workspace: {workspace_id}')
        
        # Validate query for security
        if not SecurityValidator.validate_string(query, 'query'):
            raise ValueError('Query validation failed: potentially dangerous query pattern detected')
        
        # Get workspace details
        workspace_config = self.get_workspace_details(workspace_id)
        
        # Prepare query parameters
        params = {'query': query}
        if time_param:
            params['time'] = time_param
        
        # Execute query
        result = PrometheusClient.make_request(
            prometheus_url=workspace_config['prometheus_url'],
            endpoint='query',
            params=params,
            region=self.region,
            service_name=DEFAULT_SERVICE_NAME
        )
        
        logger.info(f'Query executed successfully, result type: {result.get("resultType", "unknown")}')
        return result
    
    def execute_range_query(self, workspace_id: str, query: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """Execute a PromQL range query over time periods."""
        logger.info(f'Executing range query: {query} from {start} to {end} with step {step} for workspace: {workspace_id}')
        
        # Validate query for security
        if not SecurityValidator.validate_string(query, 'query'):
            raise ValueError('Query validation failed: potentially dangerous query pattern detected')
        
        # Get workspace details
        workspace_config = self.get_workspace_details(workspace_id)
        
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
            region=self.region,
            service_name=DEFAULT_SERVICE_NAME
        )
        
        logger.info(f'Range query executed successfully, result type: {result.get("resultType", "unknown")}')
        return result
    
    def list_metrics(self, workspace_id: str) -> Dict[str, Any]:
        """List all available metric names from Prometheus workspace."""
        logger.info(f'Listing metrics for workspace: {workspace_id}')
        
        # Get workspace details
        workspace_config = self.get_workspace_details(workspace_id)
        
        # List all available metrics
        result = PrometheusClient.make_request(
            prometheus_url=workspace_config['prometheus_url'],
            endpoint='label/__name__/values',
            params={},
            region=self.region,
            service_name=DEFAULT_SERVICE_NAME
        )
        
        # Sort metrics for better usability
        metrics = sorted(result) if isinstance(result, list) else []
        
        logger.info(f'Retrieved {len(metrics)} metrics successfully')
        return {'metrics': metrics}
    
    def get_server_info(self, workspace_id: str) -> Dict[str, Any]:
        """Get server configuration and build information."""
        logger.info(f'Retrieving server info for workspace: {workspace_id}')
        
        # Get workspace details
        workspace_config = self.get_workspace_details(workspace_id)
        
        # Prepare server information response
        server_info = {
            'prometheus_url': workspace_config['prometheus_url'],
            'aws_region': self.region,
            'service_name': DEFAULT_SERVICE_NAME,
            'workspace_id': workspace_id,
            'workspace_alias': workspace_config.get('alias', 'No alias'),
            'workspace_status': workspace_config.get('status', 'UNKNOWN')
        }
        
        logger.info(f'Server info retrieved successfully for workspace: {workspace_id}')
        return server_info


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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Prometheus MCP Server operations.
    
    Supports multiple operations based on the 'operation' parameter:
    - execute_query: Instant PromQL queries
    - execute_range_query: Range queries over time periods
    - list_metrics: Metric discovery and listing
    - get_server_info: Server configuration information
    - get_available_workspaces: List all available workspaces
    
    Expected event format:
    {
        "operation": "execute_query",
        "workspace_id": "ws-12345678-abcd-1234-efgh-123456789012",
        "query": "up",
        "time": "2023-04-01T00:00:00Z" (optional),
        "region": "us-east-1" (optional)
    }
    """
    try:
        logger.info(f'Received event: {json.dumps(event)}')
        
        # Handle both direct parameter passing (MCP gateway) and nested body format
        if 'body' in event and event['body']:
            # Traditional Lambda invocation with body
            body = event['body']
            if isinstance(body, str):
                body = json.loads(body)
        else:
            # Direct parameter passing (MCP gateway format)
            body = event
        
        # Get operation type
        operation = body.get('operation')
        if not operation:
            return create_error_response('Missing required parameter: operation', 400)
        
        # Get region
        region = body.get('region', os.getenv('AWS_REGION', DEFAULT_AWS_REGION))
        
        # Initialize Prometheus server
        prometheus_server = PrometheusServer(region=region)
        
        # Route to appropriate operation
        if operation == 'execute_query':
            # Validate required parameters for instant query
            required_params = ['workspace_id', 'query']
            missing_params = [param for param in required_params if param not in body or body[param] is None]
            
            if missing_params:
                error_msg = f'Missing required parameters: {", ".join(missing_params)}'
                return create_error_response(error_msg, 400)
            
            result = prometheus_server.execute_query(
                workspace_id=body['workspace_id'],
                query=body['query'],
                time_param=body.get('time')
            )
            return create_success_response(result)
        
        elif operation == 'execute_range_query':
            # Validate required parameters for range query
            required_params = ['workspace_id', 'query', 'start', 'end', 'step']
            missing_params = [param for param in required_params if param not in body or body[param] is None]
            
            if missing_params:
                error_msg = f'Missing required parameters: {", ".join(missing_params)}'
                return create_error_response(error_msg, 400)
            
            result = prometheus_server.execute_range_query(
                workspace_id=body['workspace_id'],
                query=body['query'],
                start=body['start'],
                end=body['end'],
                step=body['step']
            )
            return create_success_response(result)
        
        elif operation == 'list_metrics':
            # Validate required parameters for list metrics
            if 'workspace_id' not in body or body['workspace_id'] is None:
                return create_error_response('Missing required parameter: workspace_id', 400)
            
            result = prometheus_server.list_metrics(workspace_id=body['workspace_id'])
            return create_success_response(result)
        
        elif operation == 'get_server_info':
            # Validate required parameters for server info
            if 'workspace_id' not in body or body['workspace_id'] is None:
                return create_error_response('Missing required parameter: workspace_id', 400)
            
            result = prometheus_server.get_server_info(workspace_id=body['workspace_id'])
            return create_success_response(result)
        
        elif operation == 'get_available_workspaces':
            # No required parameters for listing workspaces
            result = prometheus_server.get_available_workspaces(profile=body.get('profile'))
            return create_success_response(result)
        
        else:
            return create_error_response(f'Unknown operation: {operation}', 400)
        
    except ValueError as e:
        error_msg = f'Validation error: {str(e)}'
        logger.error(error_msg)
        return create_error_response(error_msg, 400)
    except Exception as e:
        error_msg = f'Error processing request: {str(e)}'
        logger.error(error_msg)
        return create_error_response(error_msg, 500)