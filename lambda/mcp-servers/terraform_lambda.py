"""
Terraform MCP Server as Lambda Function
"""
import json
import logging
import boto3
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TerraformServer:
    """Terraform operations."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
    
    def search_aws_provider_docs(self, asset_name: str, asset_type: str = "resource") -> Dict[str, Any]:
        """Search AWS provider documentation."""
        try:
            # This is a simplified implementation
            # In a real implementation, you'd query the Terraform registry API
            
            # Normalize asset name
            if not asset_name.startswith('aws_'):
                asset_name = f'aws_{asset_name}'
            
            # Mock response structure
            docs = {
                'aws_s3_bucket': {
                    'name': 'aws_s3_bucket',
                    'type': 'resource',
                    'description': 'Provides a S3 bucket resource.',
                    'url': 'https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket',
                    'arguments': [
                        {'name': 'bucket', 'description': 'The name of the bucket', 'required': False},
                        {'name': 'bucket_prefix', 'description': 'Creates a unique bucket name beginning with the specified prefix', 'required': False},
                        {'name': 'force_destroy', 'description': 'A boolean that indicates all objects should be deleted from the bucket', 'required': False}
                    ],
                    'attributes': [
                        {'name': 'id', 'description': 'The name of the bucket'},
                        {'name': 'arn', 'description': 'The ARN of the bucket'},
                        {'name': 'bucket_domain_name', 'description': 'The bucket domain name'}
                    ]
                },
                'aws_instance': {
                    'name': 'aws_instance',
                    'type': 'resource',
                    'description': 'Provides an EC2 instance resource.',
                    'url': 'https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance',
                    'arguments': [
                        {'name': 'ami', 'description': 'AMI to use for the instance', 'required': True},
                        {'name': 'instance_type', 'description': 'The type of instance to start', 'required': True},
                        {'name': 'key_name', 'description': 'The key name of the Key Pair to use for the instance', 'required': False}
                    ],
                    'attributes': [
                        {'name': 'id', 'description': 'The instance ID'},
                        {'name': 'arn', 'description': 'The ARN of the instance'},
                        {'name': 'public_ip', 'description': 'The public IP address assigned to the instance'}
                    ]
                }
            }
            
            if asset_name in docs:
                return {
                    'found': True,
                    'asset_name': asset_name,
                    'asset_type': asset_type,
                    'documentation': docs[asset_name]
                }
            else:
                return {
                    'found': False,
                    'asset_name': asset_name,
                    'asset_type': asset_type,
                    'message': f'Documentation for {asset_name} not found in cache'
                }
                
        except Exception as e:
            logger.error(f"Failed to search AWS provider docs: {e}")
            return {
                'found': False,
                'asset_name': asset_name,
                'error': str(e)
            }
    
    def validate_terraform_config(self, config_content: str) -> Dict[str, Any]:
        """Validate Terraform configuration."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write config to temporary file
                config_file = Path(temp_dir) / "main.tf"
                config_file.write_text(config_content)
                
                # Run terraform validate (if terraform is available)
                try:
                    result = subprocess.run(
                        ['terraform', 'validate'],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    return {
                        'valid': result.returncode == 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'return_code': result.returncode
                    }
                except FileNotFoundError:
                    # Terraform not available, do basic syntax check
                    return self._basic_syntax_check(config_content)
                except subprocess.TimeoutExpired:
                    return {
                        'valid': False,
                        'error': 'Validation timeout',
                        'stderr': 'Terraform validation timed out after 30 seconds'
                    }
                    
        except Exception as e:
            logger.error(f"Failed to validate terraform config: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _basic_syntax_check(self, config_content: str) -> Dict[str, Any]:
        """Basic Terraform syntax validation."""
        try:
            # Basic checks for common Terraform syntax
            lines = config_content.split('\n')
            errors = []
            
            brace_count = 0
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Count braces
                brace_count += line.count('{') - line.count('}')
                
                # Check for basic syntax issues
                if line.endswith('{') and not any(keyword in line for keyword in ['resource', 'data', 'variable', 'output', 'locals', 'module']):
                    if '=' not in line:
                        errors.append(f"Line {i}: Possible syntax error - opening brace without assignment")
            
            if brace_count != 0:
                errors.append(f"Mismatched braces: {brace_count} unclosed braces")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'message': 'Basic syntax check completed (terraform binary not available)'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Basic syntax check failed: {e}'
            }
    
    def generate_terraform_template(self, resource_type: str, resource_name: str, 
                                  properties: Dict[str, Any]) -> str:
        """Generate Terraform configuration template."""
        try:
            # Generate basic Terraform resource block
            template_lines = [
                f'resource "{resource_type}" "{resource_name}" {{',
            ]
            
            # Add properties
            for key, value in properties.items():
                if isinstance(value, str):
                    template_lines.append(f'  {key} = "{value}"')
                elif isinstance(value, bool):
                    template_lines.append(f'  {key} = {str(value).lower()}')
                elif isinstance(value, (int, float)):
                    template_lines.append(f'  {key} = {value}')
                elif isinstance(value, list):
                    if all(isinstance(item, str) for item in value):
                        formatted_list = ', '.join(f'"{item}"' for item in value)
                        template_lines.append(f'  {key} = [{formatted_list}]')
                    else:
                        template_lines.append(f'  {key} = {json.dumps(value)}')
                elif isinstance(value, dict):
                    template_lines.append(f'  {key} = {{')
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str):
                            template_lines.append(f'    {sub_key} = "{sub_value}"')
                        else:
                            template_lines.append(f'    {sub_key} = {json.dumps(sub_value)}')
                    template_lines.append('  }')
            
            template_lines.append('}')
            
            return '\n'.join(template_lines)
            
        except Exception as e:
            logger.error(f"Failed to generate terraform template: {e}")
            return f"# Error generating template: {e}"

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for Terraform MCP server."""
    try:
        operation = event.get('operation', 'search_aws_provider_docs')
        parameters = event.get('parameters', {})
        
        server = TerraformServer(region=parameters.get('region', 'us-east-1'))
        
        if operation == 'search_aws_provider_docs':
            asset_name = parameters.get('asset_name', '')
            asset_type = parameters.get('asset_type', 'resource')
            
            if not asset_name:
                raise ValueError("asset_name parameter is required")
            
            results = server.search_aws_provider_docs(asset_name, asset_type)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'results': results
                })
            }
        
        elif operation == 'validate_terraform_config':
            config_content = parameters.get('config_content', '')
            
            if not config_content:
                raise ValueError("config_content parameter is required")
            
            results = server.validate_terraform_config(config_content)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'validation': results
                })
            }
        
        elif operation == 'generate_terraform_template':
            resource_type = parameters.get('resource_type', '')
            resource_name = parameters.get('resource_name', '')
            properties = parameters.get('properties', {})
            
            if not resource_type or not resource_name:
                raise ValueError("resource_type and resource_name parameters are required")
            
            template = server.generate_terraform_template(resource_type, resource_name, properties)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'template': template,
                    'resource_type': resource_type,
                    'resource_name': resource_name
                })
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"Terraform Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }