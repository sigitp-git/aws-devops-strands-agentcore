"""Integration layer that routes requests to appropriate specialized functions.

This module maintains backward compatibility with existing applications while
providing automatic function selection based on operation type.
Unified interface for all Prometheus operations.
"""

import json
import boto3
from typing import Any, Dict, Optional
from botocore.config import Config


class PrometheusLambdaClient:
    """Client for invoking specialized Prometheus Lambda functions."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the client with AWS region."""
        self.region = region
        self.lambda_client = boto3.client(
            'lambda',
            region_name=region,
            config=Config(user_agent_extra='prometheus-lambda-integration')
        )
        
        # Function name mappings
        self.function_names = {
            'query': 'prometheus-query',
            'range_query': 'prometheus-range-query',
            'list_metrics': 'prometheus-list-metrics',
            'server_info': 'prometheus-server-info'
        }
    
    def _invoke_function(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a specific Lambda function."""
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps({'body': payload})
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            if response_payload.get('statusCode') != 200:
                error_body = json.loads(response_payload.get('body', '{}'))
                raise RuntimeError(f"Lambda function error: {error_body.get('error', 'Unknown error')}")
            
            # Extract data from response body
            body = json.loads(response_payload.get('body', '{}'))
            return body.get('data', {})
            
        except Exception as e:
            raise RuntimeError(f"Error invoking {function_name}: {str(e)}")
    
    def execute_query(
        self,
        workspace_id: str,
        query: str,
        time: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute an instant PromQL query."""
        payload = {
            'workspace_id': workspace_id,
            'query': query,
            'region': region or self.region
        }
        if time:
            payload['time'] = time
        
        return self._invoke_function(self.function_names['query'], payload)
    
    def execute_range_query(
        self,
        workspace_id: str,
        query: str,
        start: str,
        end: str,
        step: str,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a PromQL range query."""
        payload = {
            'workspace_id': workspace_id,
            'query': query,
            'start': start,
            'end': end,
            'step': step,
            'region': region or self.region
        }
        
        return self._invoke_function(self.function_names['range_query'], payload)
    
    def list_metrics(
        self,
        workspace_id: str,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all available metrics."""
        payload = {
            'workspace_id': workspace_id,
            'region': region or self.region
        }
        
        return self._invoke_function(self.function_names['list_metrics'], payload)
    
    def get_server_info(
        self,
        workspace_id: str,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get server configuration information."""
        payload = {
            'workspace_id': workspace_id,
            'region': region or self.region
        }
        
        return self._invoke_function(self.function_names['server_info'], payload)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main integration handler that routes to appropriate specialized functions.
    
    This handler maintains backward compatibility while routing requests
    to the appropriate specialized Lambda function based on operation type.
    
    Expected event body:
    {
        "operation": "query|range_query|list_metrics|server_info",
        "workspace_id": "ws-12345678-abcd-1234-efgh-123456789012",
        "query": "up" (for query operations),
        "start": "2023-04-01T00:00:00Z" (for range_query),
        "end": "2023-04-01T01:00:00Z" (for range_query),
        "step": "5m" (for range_query),
        "time": "2023-04-01T00:00:00Z" (optional for query),
        "region": "us-east-1" (optional)
    }
    """
    try:
        # Parse request body
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        operation = body.get('operation')
        if not operation:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: operation',
                    'success': False
                })
            }
        
        region = body.get('region', 'us-east-1')
        client = PrometheusLambdaClient(region)
        
        # Route to appropriate function based on operation
        if operation == 'query':
            result = client.execute_query(
                workspace_id=body['workspace_id'],
                query=body['query'],
                time=body.get('time'),
                region=region
            )
        elif operation == 'range_query':
            result = client.execute_range_query(
                workspace_id=body['workspace_id'],
                query=body['query'],
                start=body['start'],
                end=body['end'],
                step=body['step'],
                region=region
            )
        elif operation == 'list_metrics':
            result = client.list_metrics(
                workspace_id=body['workspace_id'],
                region=region
            )
        elif operation == 'server_info':
            result = client.get_server_info(
                workspace_id=body['workspace_id'],
                region=region
            )
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown operation: {operation}',
                    'success': False
                })
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'data': result,
                'success': True
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Integration error: {str(e)}',
                'success': False
            })
        }