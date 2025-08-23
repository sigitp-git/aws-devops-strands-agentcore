"""
AWS Documentation MCP Server as Lambda Function
"""
import json
import logging
import requests
import boto3
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AWSDocumentationServer:
    """AWS Documentation search and retrieval."""
    
    def __init__(self):
        self.base_url = "https://docs.aws.amazon.com"
        self.search_api = "https://docs.aws.amazon.com/search/doc-search.html"
    
    def search_documentation(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search AWS documentation."""
        try:
            # Use AWS documentation search API
            params = {
                'searchPath': 'documentation',
                'searchQuery': query,
                'size': limit,
                'startIndex': 0
            }
            
            response = requests.get(self.search_api, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse search results
            results = []
            data = response.json()
            
            for item in data.get('items', [])[:limit]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'excerpt': item.get('excerpt', ''),
                    'service': item.get('service', ''),
                    'rank': item.get('rank', 0)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Documentation search failed: {e}")
            return []
    
    def read_documentation(self, url: str, max_length: int = 5000) -> str:
        """Read AWS documentation page content."""
        try:
            if not url.startswith('https://docs.aws.amazon.com'):
                raise ValueError("URL must be from docs.aws.amazon.com")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract main content (simplified)
            content = response.text
            
            # Remove HTML tags (basic cleanup)
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Limit content length
            if len(content) > max_length:
                content = content[:max_length] + "... [truncated]"
            
            return content
            
        except Exception as e:
            logger.error(f"Documentation read failed: {e}")
            return f"Error reading documentation: {e}"

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for AWS Documentation MCP server."""
    try:
        operation = event.get('operation', 'search_documentation')
        parameters = event.get('parameters', {})
        
        server = AWSDocumentationServer()
        
        if operation == 'search_documentation':
            query = parameters.get('query', '')
            limit = parameters.get('limit', 10)
            
            if not query:
                raise ValueError("Query parameter is required")
            
            results = server.search_documentation(query, limit)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'results': results,
                    'query': query
                })
            }
        
        elif operation == 'read_documentation':
            url = parameters.get('url', '')
            max_length = parameters.get('max_length', 5000)
            
            if not url:
                raise ValueError("URL parameter is required")
            
            content = server.read_documentation(url, max_length)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'content': content,
                    'url': url
                })
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"AWS Documentation Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }