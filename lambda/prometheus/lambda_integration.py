#!/usr/bin/env python3
"""
Prometheus Lambda Integration Layer

This module provides a unified interface for all Prometheus Lambda functions,
making it easier to integrate with MCP (Model Context Protocol) and other systems.
It routes requests to the appropriate specialized Lambda function based on operation type.

Features:
- Unified interface for all Prometheus operations
- Automatic function selection based on operation type
- Backward compatibility with existing applications
- Error handling and response standardization
- Support for both direct invocation and MCP integration
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional
from enum import Enum

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class PrometheusOperation(Enum):
    """Enumeration of supported Prometheus operations."""
    QUERY = "query"
    RANGE_QUERY = "range_query"
    LIST_METRICS = "list_metrics"
    SERVER_INFO = "server_info"
    FIND_WORKSPACE = "find_workspace"

class PrometheusLambdaIntegration:
    """
    Integration layer for Prometheus Lambda functions.
    
    This class provides a unified interface to all Prometheus Lambda functions,
    automatically routing requests to the appropriate specialized function.
    """
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize the integration layer.
        
        Args:
            region: AWS region for Lambda functions
        """
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        
        # Function name mappings
        self.function_names = {
            PrometheusOperation.QUERY: "aws-devops-prometheus-query",
            PrometheusOperation.RANGE_QUERY: "aws-devops-prometheus-range-query",
            PrometheusOperation.LIST_METRICS: "aws-devops-prometheus-list-metrics",
            PrometheusOperation.SERVER_INFO: "aws-devops-prometheus-server-info",
            PrometheusOperation.FIND_WORKSPACE: "aws-devops-prometheus-find-workspace"
        }
    
    def execute_operation(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Prometheus operation by routing to the appropriate Lambda function.
        
        Args:
            operation: The operation to perform (query, range_query, list_metrics, etc.)
            parameters: Parameters for the operation
            
        Returns:
            Response from the Lambda function
        """
        try:
            # Validate operation
            if operation not in [op.value for op in PrometheusOperation]:
                return {
                    'statusCode': 400,
                    'error': f'Unsupported operation: {operation}',
                    'supported_operations': [op.value for op in PrometheusOperation]
                }
            
            # Get the appropriate function name
            operation_enum = PrometheusOperation(operation)
            function_name = self.function_names[operation_enum]
            
            logger.info(f"Routing {operation} to function: {function_name}")
            
            # Invoke the Lambda function
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(parameters)
            )
            
            # Parse the response
            response_payload = response['Payload'].read()
            result = json.loads(response_payload)
            
            # Add integration metadata
            if isinstance(result, dict):
                result['integration_info'] = {
                    'routed_to': function_name,
                    'operation': operation,
                    'integration_layer': 'prometheus-lambda-integration'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing operation {operation}: {str(e)}")
            return {
                'statusCode': 500,
                'error': str(e),
                'operation': operation,
                'message': 'Integration layer error'
            }
    
    def query(self, workspace_url: str, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an instant PromQL query.
        
        Args:
            workspace_url: Prometheus workspace URL
            query: PromQL query string
            time: Optional timestamp for evaluation
            
        Returns:
            Query results
        """
        parameters = {
            'workspace_url': workspace_url,
            'query': query
        }
        if time:
            parameters['time'] = time
            
        return self.execute_operation('query', parameters)
    
    def range_query(self, workspace_url: str, query: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """
        Execute a PromQL range query.
        
        Args:
            workspace_url: Prometheus workspace URL
            query: PromQL query string
            start: Start timestamp
            end: End timestamp
            step: Query resolution step
            
        Returns:
            Range query results
        """
        parameters = {
            'workspace_url': workspace_url,
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        
        return self.execute_operation('range_query', parameters)
    
    def list_metrics(self, workspace_url: str) -> Dict[str, Any]:
        """
        List all available metrics.
        
        Args:
            workspace_url: Prometheus workspace URL
            
        Returns:
            List of available metrics
        """
        parameters = {
            'workspace_url': workspace_url
        }
        
        return self.execute_operation('list_metrics', parameters)
    
    def server_info(self, workspace_url: str) -> Dict[str, Any]:
        """
        Get server configuration and build information.
        
        Args:
            workspace_url: Prometheus workspace URL
            
        Returns:
            Server information
        """
        parameters = {
            'workspace_url': workspace_url
        }
        
        return self.execute_operation('server_info', parameters)
    
    def find_workspace(self, alias: Optional[str] = None, workspace_id: Optional[str] = None, 
                      list_all: bool = False, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Find workspace by alias or ID, or list all workspaces.
        
        Args:
            alias: Workspace alias to search for
            workspace_id: Workspace ID to find
            list_all: Whether to list all workspaces
            region: AWS region
            
        Returns:
            Workspace information
        """
        parameters = {}
        if alias:
            parameters['alias'] = alias
        if workspace_id:
            parameters['workspace_id'] = workspace_id
        if list_all:
            parameters['list_all'] = list_all
        if region:
            parameters['region'] = region
            
        return self.execute_operation('find_workspace', parameters)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for the integration layer.
    
    This allows the integration layer itself to be deployed as a Lambda function
    for use in environments where direct SDK access isn't available.
    
    Expected event format:
    {
        "operation": "query|range_query|list_metrics|server_info|find_workspace",
        "parameters": {
            // Operation-specific parameters
        }
    }
    """
    try:
        # Extract operation and parameters
        operation = event.get('operation')
        parameters = event.get('parameters', {})
        
        if not operation:
            return {
                'statusCode': 400,
                'error': 'Missing required field: operation',
                'supported_operations': [op.value for op in PrometheusOperation]
            }
        
        # Initialize integration layer
        integration = PrometheusLambdaIntegration()
        
        # Execute the operation
        result = integration.execute_operation(operation, parameters)
        
        return result
        
    except Exception as e:
        logger.error(f"Integration layer error: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'message': 'Integration layer handler error'
        }

# Utility functions for direct use
def create_integration_client(region: str = "us-east-1") -> PrometheusLambdaIntegration:
    """
    Create a Prometheus Lambda integration client.
    
    Args:
        region: AWS region
        
    Returns:
        PrometheusLambdaIntegration instance
    """
    return PrometheusLambdaIntegration(region)

# Example usage
if __name__ == "__main__":
    # Example usage of the integration layer
    integration = PrometheusLambdaIntegration()
    
    # Example: Find all workspaces
    print("Finding all workspaces...")
    result = integration.find_workspace(list_all=True)
    print(json.dumps(result, indent=2))
    
    # Example: Execute a query (would need a real workspace URL)
    # result = integration.query(
    #     workspace_url="https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-example",
    #     query="up"
    # )
    # print(json.dumps(result, indent=2))