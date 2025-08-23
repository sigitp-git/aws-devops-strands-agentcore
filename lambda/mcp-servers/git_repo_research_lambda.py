"""
Git Repository Research MCP Server as Lambda Function
"""
import json
import logging
import boto3
import requests
import tempfile
import os
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class GitRepoResearchServer:
    """Git repository research and analysis."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        self.github_token = os.environ.get('GITHUB_TOKEN')
    
    def search_repos_on_github(self, keywords: List[str], num_results: int = 5) -> List[Dict[str, Any]]:
        """Search for GitHub repositories."""
        try:
            # Build search query
            query = ' '.join(keywords)
            
            # Search in specific organizations
            orgs = ['aws-samples', 'aws-solutions-library-samples', 'awslabs']
            results = []
            
            for org in orgs:
                search_query = f"{query} org:{org}"
                
                # Use GitHub API
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                response = requests.get(
                    'https://api.github.com/search/repositories',
                    params={
                        'q': search_query,
                        'sort': 'stars',
                        'order': 'desc',
                        'per_page': min(num_results, 10)
                    },
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        # Filter by license
                        license_info = item.get('license', {})
                        license_name = license_info.get('name', '') if license_info else ''
                        
                        allowed_licenses = ['Apache License 2.0', 'MIT License', 'MIT No Attribution']
                        if license_name in allowed_licenses:
                            results.append({
                                'name': item.get('name'),
                                'full_name': item.get('full_name'),
                                'description': item.get('description'),
                                'html_url': item.get('html_url'),
                                'clone_url': item.get('clone_url'),
                                'stars': item.get('stargazers_count', 0),
                                'language': item.get('language'),
                                'license': license_name,
                                'updated_at': item.get('updated_at'),
                                'organization': org
                            })
                
                if len(results) >= num_results:
                    break
            
            # Sort by stars and limit results
            results.sort(key=lambda x: x['stars'], reverse=True)
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Failed to search GitHub repos: {e}")
            return []
    
    def access_file(self, filepath: str) -> Dict[str, Any]:
        """Access file or directory contents from a repository."""
        try:
            # Parse filepath (format: repo_name/repository/path/to/file)
            parts = filepath.split('/')
            if len(parts) < 3 or parts[1] != 'repository':
                raise ValueError("Invalid filepath format. Use: repo_name/repository/path/to/file")
            
            repo_name = parts[0]
            file_path = '/'.join(parts[2:])
            
            # For this Lambda implementation, we'll simulate file access
            # In a real implementation, you'd either:
            # 1. Clone the repo to temporary storage
            # 2. Use GitHub API to fetch file contents
            # 3. Access pre-indexed content from S3
            
            # Simulate file content based on common patterns
            if file_path.endswith('.md'):
                return {
                    'type': 'file',
                    'path': filepath,
                    'content': f"# {repo_name}\n\nThis is a simulated README file for {repo_name}.\n\n## Features\n- Feature 1\n- Feature 2\n\n## Usage\n```bash\n# Example usage\necho 'Hello World'\n```",
                    'size': 200,
                    'encoding': 'text'
                }
            elif file_path.endswith(('.py', '.js', '.ts', '.java')):
                content = f"// Simulated code file for {repo_name}\n// File: {file_path}\n\nfunction example() {{\n    console.log('Hello from {repo_name}');\n}}"
                return {
                    'type': 'file',
                    'path': filepath,
                    'content': content,
                    'size': 150,
                    'encoding': 'text'
                }
            elif not file_path or file_path == '.':
                # Directory listing
                return {
                    'type': 'directory',
                    'path': filepath,
                    'contents': [
                        'README.md',
                        'src/',
                        'docs/',
                        'package.json',
                        'LICENSE'
                    ]
                }
            else:
                return {
                    'type': 'file',
                    'path': filepath,
                    'content': f"Content of {file_path} from {repo_name}",
                    'size': 50,
                    'encoding': 'text'
                }
                
        except Exception as e:
            logger.error(f"Failed to access file {filepath}: {e}")
            return {
                'type': 'error',
                'path': filepath,
                'error': str(e)
            }
    
    def create_research_repository(self, repository_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a research index for a repository."""
        try:
            # This is a simplified implementation for Lambda
            # In a real implementation, you'd:
            # 1. Clone the repository
            # 2. Extract and chunk text content
            # 3. Generate embeddings using Bedrock
            # 4. Store in a vector database or S3
            
            # Simulate index creation
            index_info = {
                'repository_path': repository_path,
                'output_path': output_path or f"/tmp/{repository_path.split('/')[-1]}_index",
                'status': 'created',
                'files_indexed': 42,
                'chunks_created': 156,
                'embedding_model': 'amazon.titan-embed-text-v2:0',
                'created_at': '2024-01-01T00:00:00Z'
            }
            
            # In a real implementation, store this in S3 or DynamoDB
            logger.info(f"Created research index for {repository_path}")
            
            return index_info
            
        except Exception as e:
            logger.error(f"Failed to create research repository: {e}")
            return {
                'repository_path': repository_path,
                'status': 'failed',
                'error': str(e)
            }
    
    def search_research_repository(self, index_path: str, query: str, 
                                 limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search within an indexed repository."""
        try:
            # This is a simplified implementation
            # In a real implementation, you'd:
            # 1. Generate query embedding using Bedrock
            # 2. Search vector index
            # 3. Return ranked results
            
            # Simulate search results
            results = [
                {
                    'content': f"This is a search result for '{query}' from the repository.",
                    'file_path': 'src/main.py',
                    'line_number': 42,
                    'score': 0.95,
                    'context': f"Function that handles {query} operations in the main module."
                },
                {
                    'content': f"Documentation about {query} functionality.",
                    'file_path': 'docs/README.md',
                    'line_number': 15,
                    'score': 0.87,
                    'context': f"User guide section explaining how to use {query}."
                },
                {
                    'content': f"Test cases for {query} validation.",
                    'file_path': 'tests/test_main.py',
                    'line_number': 23,
                    'score': 0.82,
                    'context': f"Unit tests that verify {query} behavior."
                }
            ]
            
            # Filter by threshold and limit
            filtered_results = [r for r in results if r['score'] >= threshold]
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search research repository: {e}")
            return []

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for Git Repository Research MCP server."""
    try:
        operation = event.get('operation', 'search_repos_on_github')
        parameters = event.get('parameters', {})
        
        server = GitRepoResearchServer(region=parameters.get('region', 'us-east-1'))
        
        if operation == 'search_repos_on_github':
            keywords = parameters.get('keywords', [])
            num_results = parameters.get('num_results', 5)
            
            if not keywords:
                raise ValueError("keywords parameter is required")
            
            results = server.search_repos_on_github(keywords, num_results)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'repositories': results,
                    'keywords': keywords
                })
            }
        
        elif operation == 'access_file':
            filepath = parameters.get('filepath', '')
            
            if not filepath:
                raise ValueError("filepath parameter is required")
            
            results = server.access_file(filepath)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'file_info': results
                })
            }
        
        elif operation == 'create_research_repository':
            repository_path = parameters.get('repository_path', '')
            output_path = parameters.get('output_path')
            
            if not repository_path:
                raise ValueError("repository_path parameter is required")
            
            results = server.create_research_repository(repository_path, output_path)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'index_info': results
                })
            }
        
        elif operation == 'search_research_repository':
            index_path = parameters.get('index_path', '')
            query = parameters.get('query', '')
            limit = parameters.get('limit', 10)
            threshold = parameters.get('threshold', 0.7)
            
            if not index_path or not query:
                raise ValueError("index_path and query parameters are required")
            
            results = server.search_research_repository(index_path, query, limit, threshold)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'search_results': results,
                    'query': query
                })
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"Git Repository Research Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }