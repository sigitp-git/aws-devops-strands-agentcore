"""
Core MCP Server as Lambda Function
"""
import json
import logging
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CoreServer:
    """Core MCP server functionality."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.ssm_client = boto3.client('ssm', region_name=region)
        self.sts_client = boto3.client('sts', region_name=region)
    
    def prompt_understanding(self) -> Dict[str, Any]:
        """Analyze and understand user prompts for AWS expert advice."""
        try:
            # This would typically analyze the user's query and provide context
            # For Lambda implementation, we'll return structured guidance
            
            understanding = {
                'analysis': {
                    'intent': 'aws_expert_consultation',
                    'domain': 'cloud_infrastructure',
                    'complexity': 'intermediate',
                    'requires_context': True
                },
                'recommendations': {
                    'approach': 'systematic_analysis',
                    'best_practices': [
                        'Follow AWS Well-Architected Framework principles',
                        'Consider security, reliability, performance, cost optimization',
                        'Use Infrastructure as Code when possible',
                        'Implement proper monitoring and logging'
                    ],
                    'tools_to_use': [
                        'AWS CloudFormation or CDK for infrastructure',
                        'CloudWatch for monitoring',
                        'AWS Config for compliance',
                        'AWS Cost Explorer for cost analysis'
                    ]
                },
                'context': {
                    'aws_services': 'comprehensive_knowledge',
                    'devops_practices': 'industry_standard',
                    'security_focus': 'zero_trust_model',
                    'cost_awareness': 'optimization_first'
                }
            }
            
            return understanding
            
        except Exception as e:
            logger.error(f"Failed to process prompt understanding: {e}")
            return {
                'analysis': {'error': str(e)},
                'recommendations': {},
                'context': {}
            }
    
    def get_aws_context(self) -> Dict[str, Any]:
        """Get current AWS context information."""
        try:
            # Get caller identity
            identity = self.sts_client.get_caller_identity()
            
            # Get region information
            ec2_client = boto3.client('ec2', region_name=self.region)
            regions_response = ec2_client.describe_regions()
            available_regions = [r['RegionName'] for r in regions_response['Regions']]
            
            context = {
                'account_id': identity.get('Account'),
                'user_arn': identity.get('Arn'),
                'user_id': identity.get('UserId'),
                'current_region': self.region,
                'available_regions': available_regions[:10],  # Limit for Lambda response size
                'timestamp': datetime.utcnow().isoformat(),
                'session_info': {
                    'authenticated': True,
                    'permissions': 'lambda_execution_role',
                    'access_level': 'programmatic'
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get AWS context: {e}")
            return {
                'account_id': 'unknown',
                'current_region': self.region,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and health information."""
        try:
            # Check various AWS service endpoints
            services_status = {}
            
            # Check STS (always available)
            try:
                self.sts_client.get_caller_identity()
                services_status['sts'] = 'healthy'
            except Exception:
                services_status['sts'] = 'unhealthy'
            
            # Check SSM
            try:
                self.ssm_client.describe_parameters(MaxResults=1)
                services_status['ssm'] = 'healthy'
            except Exception:
                services_status['ssm'] = 'unhealthy'
            
            # Check EC2 (basic connectivity)
            try:
                ec2_client = boto3.client('ec2', region_name=self.region)
                ec2_client.describe_regions()
                services_status['ec2'] = 'healthy'
            except Exception:
                services_status['ec2'] = 'unhealthy'
            
            # Overall health
            healthy_services = sum(1 for status in services_status.values() if status == 'healthy')
            total_services = len(services_status)
            overall_health = 'healthy' if healthy_services == total_services else 'degraded'
            
            status = {
                'overall_health': overall_health,
                'services': services_status,
                'health_score': f"{healthy_services}/{total_services}",
                'region': self.region,
                'timestamp': datetime.utcnow().isoformat(),
                'lambda_info': {
                    'function_name': 'core-mcp-server',
                    'runtime': 'python3.11',
                    'memory_limit': '512MB',
                    'timeout': '300s'
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'overall_health': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration settings."""
        try:
            # Get configuration from SSM parameters
            config = {
                'region': self.region,
                'service': 'core-mcp-server',
                'version': '1.0.0',
                'features': {
                    'prompt_understanding': True,
                    'aws_context': True,
                    'system_status': True,
                    'configuration_management': True
                },
                'limits': {
                    'max_response_size': '6MB',
                    'timeout': '300s',
                    'memory': '512MB'
                },
                'integrations': {
                    'bedrock_agentcore': True,
                    'lambda_gateway': True,
                    'ssm_parameters': True
                }
            }
            
            # Try to get additional config from SSM
            try:
                response = self.ssm_client.get_parameter(
                    Name='/app/devopsagent/core/config',
                    WithDecryption=True
                )
                ssm_config = json.loads(response['Parameter']['Value'])
                config.update(ssm_config)
            except self.ssm_client.exceptions.ParameterNotFound:
                logger.info("No additional configuration found in SSM")
            except Exception as e:
                logger.warning(f"Could not load SSM configuration: {e}")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            return {
                'region': self.region,
                'error': str(e)
            }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for Core MCP server."""
    try:
        operation = event.get('operation', 'prompt_understanding')
        parameters = event.get('parameters', {})
        region = parameters.get('region', 'us-east-1')
        
        server = CoreServer(region=region)
        
        if operation == 'prompt_understanding':
            results = server.prompt_understanding()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'understanding': results,
                    'region': region
                })
            }
        
        elif operation == 'get_aws_context':
            results = server.get_aws_context()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'context': results
                }, default=str)
            }
        
        elif operation == 'get_system_status':
            results = server.get_system_status()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'status': results
                }, default=str)
            }
        
        elif operation == 'get_configuration':
            results = server.get_configuration()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'configuration': results
                })
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"Core Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }