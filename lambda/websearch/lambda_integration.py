#!/usr/bin/env python3
"""
Lambda Integration Module for AWS DevOps Agent

This module provides integration with the deployed Lambda web search function.
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class LambdaWebSearchClient:
    """Client for interacting with the deployed Lambda web search function"""
    
    def __init__(self, function_name: str = "devops-agent-websearch", region: str = "us-east-1"):
        """
        Initialize the Lambda web search client
        
        Args:
            function_name: Name of the Lambda function
            region: AWS region where the function is deployed
        """
        self.function_name = function_name
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
    
    def search(self, keywords: str, region: str = "us-en", max_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform a web search using the Lambda function
        
        Args:
            keywords: Search terms
            region: Search region (us-en, uk-en, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results or error information
        """
        try:
            # Prepare the payload
            payload = {
                "keywords": keywords,
                "region": region
            }
            
            if max_results is not None:
                payload["max_results"] = max_results
            
            logger.info(f"Invoking Lambda function for search: '{keywords}'")
            
            # Invoke the Lambda function
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse the response
            response_payload = json.loads(response['Payload'].read())
            
            if response.get('StatusCode') == 200:
                # Parse the Lambda response body
                body = json.loads(response_payload.get('body', '{}'))
                
                if body.get('success'):
                    logger.info(f"Search completed successfully for: '{keywords}'")
                    return {
                        'success': True,
                        'results': body.get('results', {}),
                        'query': body.get('query'),
                        'region': body.get('region')
                    }
                else:
                    logger.warning(f"Search failed: {body.get('error')}")
                    return {
                        'success': False,
                        'error': body.get('error', 'Unknown error'),
                        'query': keywords
                    }
            else:
                logger.error(f"Lambda invocation failed with status: {response.get('StatusCode')}")
                return {
                    'success': False,
                    'error': f"Lambda invocation failed with status: {response.get('StatusCode')}",
                    'query': keywords
                }
                
        except ClientError as e:
            error_msg = f"AWS error during Lambda invocation: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'query': keywords
            }
        except Exception as e:
            error_msg = f"Unexpected error during web search: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'query': keywords
            }
    
    def format_search_results(self, search_response: Dict[str, Any]) -> str:
        """
        Format search results for display in the agent
        
        Args:
            search_response: Response from the search method
            
        Returns:
            Formatted string representation of the search results
        """
        if not search_response.get('success'):
            return f"❌ Search failed: {search_response.get('error', 'Unknown error')}"
        
        results = search_response.get('results', {})
        
        if isinstance(results, dict) and results.get('error'):
            return f"⚠️ Search service error: {results['error']}"
        
        search_results = results.get('results', []) if isinstance(results, dict) else []
        
        if not search_results:
            return f"🔍 No results found for: '{search_response.get('query')}'"
        
        formatted = f"🔍 Search results for: '{search_response.get('query')}'\n"
        formatted += f"📍 Region: {search_response.get('region', 'N/A')}\n\n"
        
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No description')
            url = result.get('url', 'No URL')
            
            # Truncate long descriptions
            if len(body) > 200:
                body = body[:200] + "..."
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   {body}\n"
            formatted += f"   🔗 {url}\n\n"
        
        return formatted.strip()
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the Lambda function
        
        Returns:
            Dictionary with test results
        """
        try:
            logger.info("Testing Lambda function connection...")
            
            # Test with a simple query
            test_response = self.search("test connection", max_results=1)
            
            return {
                'success': True,
                'message': 'Lambda function is accessible',
                'function_name': self.function_name,
                'region': self.region,
                'test_response': test_response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Lambda function test failed: {str(e)}",
                'function_name': self.function_name,
                'region': self.region
            }

def create_web_search_client() -> LambdaWebSearchClient:
    """
    Factory function to create a web search client
    
    Returns:
        Configured LambdaWebSearchClient instance
    """
    return LambdaWebSearchClient()

# Example usage
if __name__ == "__main__":
    # Test the Lambda integration
    client = create_web_search_client()
    
    print("🧪 Testing Lambda Web Search Integration")
    print("=" * 50)
    
    # Test connection
    connection_test = client.test_connection()
    print(f"Connection Test: {'✅ PASSED' if connection_test['success'] else '❌ FAILED'}")
    
    if not connection_test['success']:
        print(f"Error: {connection_test['error']}")
    else:
        print(f"Function: {connection_test['function_name']}")
        print(f"Region: {connection_test['region']}")
        
        # Test search
        print("\n🔍 Testing search functionality...")
        search_result = client.search("AWS DevOps best practices", max_results=2)
        formatted_results = client.format_search_results(search_result)
        print(formatted_results)