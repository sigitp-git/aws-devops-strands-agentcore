"""
EKS MCP Server as Lambda Function
"""
import json
import logging
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class EKSServer:
    """EKS cluster operations."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.eks_client = boto3.client('eks', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
    
    def list_clusters(self) -> List[str]:
        """List EKS clusters."""
        try:
            response = self.eks_client.list_clusters()
            return response.get('clusters', [])
        except Exception as e:
            logger.error(f"Failed to list clusters: {e}")
            return []
    
    def describe_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Get detailed cluster information."""
        try:
            response = self.eks_client.describe_cluster(name=cluster_name)
            cluster = response.get('cluster', {})
            
            # Simplify the response for Lambda
            return {
                'name': cluster.get('name'),
                'arn': cluster.get('arn'),
                'version': cluster.get('version'),
                'status': cluster.get('status'),
                'endpoint': cluster.get('endpoint'),
                'platform_version': cluster.get('platformVersion'),
                'role_arn': cluster.get('roleArn'),
                'vpc_config': {
                    'subnet_ids': cluster.get('resourcesVpcConfig', {}).get('subnetIds', []),
                    'security_group_ids': cluster.get('resourcesVpcConfig', {}).get('securityGroupIds', []),
                    'vpc_id': cluster.get('resourcesVpcConfig', {}).get('vpcId'),
                    'endpoint_access': {
                        'private': cluster.get('resourcesVpcConfig', {}).get('endpointConfigResponse', {}).get('privateAccess'),
                        'public': cluster.get('resourcesVpcConfig', {}).get('endpointConfigResponse', {}).get('publicAccess')
                    }
                },
                'logging': cluster.get('logging', {}),
                'created_at': cluster.get('createdAt').isoformat() if cluster.get('createdAt') else None,
                'tags': cluster.get('tags', {})
            }
        except Exception as e:
            logger.error(f"Failed to describe cluster {cluster_name}: {e}")
            return {'error': str(e)}
    
    def list_nodegroups(self, cluster_name: str) -> List[str]:
        """List node groups for a cluster."""
        try:
            response = self.eks_client.list_nodegroups(clusterName=cluster_name)
            return response.get('nodegroups', [])
        except Exception as e:
            logger.error(f"Failed to list nodegroups for {cluster_name}: {e}")
            return []
    
    def describe_nodegroup(self, cluster_name: str, nodegroup_name: str) -> Dict[str, Any]:
        """Get detailed node group information."""
        try:
            response = self.eks_client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=nodegroup_name
            )
            nodegroup = response.get('nodegroup', {})
            
            return {
                'nodegroup_name': nodegroup.get('nodegroupName'),
                'nodegroup_arn': nodegroup.get('nodegroupArn'),
                'cluster_name': nodegroup.get('clusterName'),
                'version': nodegroup.get('version'),
                'status': nodegroup.get('status'),
                'capacity_type': nodegroup.get('capacityType'),
                'scaling_config': nodegroup.get('scalingConfig', {}),
                'instance_types': nodegroup.get('instanceTypes', []),
                'ami_type': nodegroup.get('amiType'),
                'node_role': nodegroup.get('nodeRole'),
                'subnets': nodegroup.get('subnets', []),
                'remote_access': nodegroup.get('remoteAccess', {}),
                'created_at': nodegroup.get('createdAt').isoformat() if nodegroup.get('createdAt') else None,
                'modified_at': nodegroup.get('modifiedAt').isoformat() if nodegroup.get('modifiedAt') else None,
                'tags': nodegroup.get('tags', {})
            }
        except Exception as e:
            logger.error(f"Failed to describe nodegroup {nodegroup_name}: {e}")
            return {'error': str(e)}
    
    def get_cluster_health(self, cluster_name: str) -> Dict[str, Any]:
        """Get cluster health status."""
        try:
            # Get cluster info
            cluster_info = self.describe_cluster(cluster_name)
            if 'error' in cluster_info:
                return cluster_info
            
            # Get node groups
            nodegroups = self.list_nodegroups(cluster_name)
            nodegroup_status = []
            
            for ng_name in nodegroups:
                ng_info = self.describe_nodegroup(cluster_name, ng_name)
                if 'error' not in ng_info:
                    nodegroup_status.append({
                        'name': ng_name,
                        'status': ng_info.get('status'),
                        'capacity_type': ng_info.get('capacity_type'),
                        'scaling_config': ng_info.get('scaling_config', {})
                    })
            
            # Check addons
            try:
                addons_response = self.eks_client.list_addons(clusterName=cluster_name)
                addons = addons_response.get('addons', [])
                addon_status = []
                
                for addon_name in addons:
                    addon_response = self.eks_client.describe_addon(
                        clusterName=cluster_name,
                        addonName=addon_name
                    )
                    addon_info = addon_response.get('addon', {})
                    addon_status.append({
                        'name': addon_name,
                        'status': addon_info.get('status'),
                        'version': addon_info.get('addonVersion')
                    })
            except Exception as e:
                logger.warning(f"Could not get addon status: {e}")
                addon_status = []
            
            return {
                'cluster_name': cluster_name,
                'cluster_status': cluster_info.get('status'),
                'cluster_version': cluster_info.get('version'),
                'nodegroups': nodegroup_status,
                'addons': addon_status,
                'health_summary': {
                    'cluster_healthy': cluster_info.get('status') == 'ACTIVE',
                    'nodegroups_healthy': all(ng.get('status') == 'ACTIVE' for ng in nodegroup_status),
                    'total_nodegroups': len(nodegroup_status)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get cluster health for {cluster_name}: {e}")
            return {'error': str(e)}
    
    def get_cloudwatch_logs(self, cluster_name: str, log_type: str = "application", 
                           minutes: int = 15, limit: int = 50) -> Dict[str, Any]:
        """Get CloudWatch logs for EKS cluster."""
        try:
            # Construct log group name based on log type
            log_group_patterns = {
                'application': f'/aws/containerinsights/{cluster_name}/application',
                'host': f'/aws/containerinsights/{cluster_name}/host',
                'performance': f'/aws/containerinsights/{cluster_name}/performance',
                'control-plane': f'/aws/eks/{cluster_name}/cluster'
            }
            
            log_group_name = log_group_patterns.get(log_type, log_type)
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=minutes)
            
            # Query logs
            query_string = f"""
            fields @timestamp, @message
            | sort @timestamp desc
            | limit {limit}
            """
            
            response = self.logs_client.start_query(
                logGroupName=log_group_name,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query_string
            )
            
            query_id = response['queryId']
            
            # Poll for results (simplified for Lambda)
            import time
            for _ in range(10):  # Max 10 seconds wait
                result = self.logs_client.get_query_results(queryId=query_id)
                if result['status'] == 'Complete':
                    return {
                        'cluster_name': cluster_name,
                        'log_type': log_type,
                        'log_group': log_group_name,
                        'time_range': {
                            'start': start_time.isoformat(),
                            'end': end_time.isoformat()
                        },
                        'logs': result.get('results', []),
                        'status': 'success'
                    }
                elif result['status'] == 'Failed':
                    return {
                        'cluster_name': cluster_name,
                        'log_type': log_type,
                        'error': 'Query failed',
                        'status': 'failed'
                    }
                time.sleep(1)
            
            return {
                'cluster_name': cluster_name,
                'log_type': log_type,
                'error': 'Query timeout',
                'status': 'timeout'
            }
            
        except Exception as e:
            logger.error(f"Failed to get CloudWatch logs: {e}")
            return {
                'cluster_name': cluster_name,
                'log_type': log_type,
                'error': str(e),
                'status': 'error'
            }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for EKS MCP server."""
    try:
        operation = event.get('operation', 'list_clusters')
        parameters = event.get('parameters', {})
        region = parameters.get('region', 'us-east-1')
        
        server = EKSServer(region=region)
        
        if operation == 'list_clusters':
            results = server.list_clusters()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'clusters': results,
                    'region': region
                })
            }
        
        elif operation == 'describe_cluster':
            cluster_name = parameters.get('cluster_name', '')
            if not cluster_name:
                raise ValueError("cluster_name parameter is required")
            
            results = server.describe_cluster(cluster_name)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'cluster': results,
                    'region': region
                }, default=str)
            }
        
        elif operation == 'list_nodegroups':
            cluster_name = parameters.get('cluster_name', '')
            if not cluster_name:
                raise ValueError("cluster_name parameter is required")
            
            results = server.list_nodegroups(cluster_name)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'cluster_name': cluster_name,
                    'nodegroups': results,
                    'region': region
                })
            }
        
        elif operation == 'describe_nodegroup':
            cluster_name = parameters.get('cluster_name', '')
            nodegroup_name = parameters.get('nodegroup_name', '')
            
            if not cluster_name or not nodegroup_name:
                raise ValueError("cluster_name and nodegroup_name parameters are required")
            
            results = server.describe_nodegroup(cluster_name, nodegroup_name)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'nodegroup': results,
                    'region': region
                }, default=str)
            }
        
        elif operation == 'get_cluster_health':
            cluster_name = parameters.get('cluster_name', '')
            if not cluster_name:
                raise ValueError("cluster_name parameter is required")
            
            results = server.get_cluster_health(cluster_name)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'health': results,
                    'region': region
                }, default=str)
            }
        
        elif operation == 'get_cloudwatch_logs':
            cluster_name = parameters.get('cluster_name', '')
            log_type = parameters.get('log_type', 'application')
            minutes = parameters.get('minutes', 15)
            limit = parameters.get('limit', 50)
            
            if not cluster_name:
                raise ValueError("cluster_name parameter is required")
            
            results = server.get_cloudwatch_logs(cluster_name, log_type, minutes, limit)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'logs': results,
                    'region': region
                }, default=str)
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"EKS Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }