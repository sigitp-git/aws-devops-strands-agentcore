import json
import boto3
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

class EKSManager:
    """AWS EKS management operations with best practices"""
    
    def __init__(self, region: str = None):
        """
        Initialize EKS manager
        
        Args:
            region: AWS region (defaults to environment or us-east-1)
        """
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize AWS clients with error handling
        try:
            self.eks_client = boto3.client('eks', region_name=self.region)
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.iam_client = boto3.client('iam', region_name=self.region)
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise
    
    def list_clusters(self, max_results: int = 100) -> Dict[str, Any]:
        """
        List EKS clusters with pagination support
        
        Args:
            max_results: Maximum number of clusters to return
            
        Returns:
            Dictionary with cluster information
        """
        try:
            logger.info("Listing EKS clusters")
            
            clusters = []
            paginator = self.eks_client.get_paginator('list_clusters')
            
            for page in paginator.paginate(maxResults=min(max_results, 100)):
                for cluster_name in page.get('clusters', []):
                    try:
                        # Get detailed cluster information
                        cluster_detail = self.eks_client.describe_cluster(name=cluster_name)
                        cluster_info = cluster_detail['cluster']
                        
                        # Extract key information
                        clusters.append({
                            'name': cluster_info['name'],
                            'status': cluster_info['status'],
                            'version': cluster_info['version'],
                            'endpoint': cluster_info.get('endpoint'),
                            'created_at': cluster_info['createdAt'].isoformat() if cluster_info.get('createdAt') else None,
                            'arn': cluster_info['arn'],
                            'platform_version': cluster_info.get('platformVersion'),
                            'tags': cluster_info.get('tags', {})
                        })
                        
                        if len(clusters) >= max_results:
                            break
                            
                    except ClientError as e:
                        logger.warning(f"Could not describe cluster {cluster_name}: {str(e)}")
                        continue
                
                if len(clusters) >= max_results:
                    break
            
            return {
                'clusters': clusters,
                'count': len(clusters),
                'region': self.region
            }
            
        except ClientError as e:
            logger.error(f"Failed to list clusters: {str(e)}")
            raise
    
    def get_cluster_details(self, cluster_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific EKS cluster
        
        Args:
            cluster_name: Name of the EKS cluster
            
        Returns:
            Detailed cluster information
        """
        try:
            logger.info(f"Getting details for cluster: {cluster_name}")
            
            # Get cluster details
            cluster_response = self.eks_client.describe_cluster(name=cluster_name)
            cluster = cluster_response['cluster']
            
            # Get node groups
            nodegroups = []
            try:
                ng_response = self.eks_client.list_nodegroups(clusterName=cluster_name)
                for ng_name in ng_response.get('nodegroups', []):
                    ng_detail = self.eks_client.describe_nodegroup(
                        clusterName=cluster_name,
                        nodegroupName=ng_name
                    )
                    nodegroups.append({
                        'name': ng_detail['nodegroup']['nodegroupName'],
                        'status': ng_detail['nodegroup']['status'],
                        'instance_types': ng_detail['nodegroup'].get('instanceTypes', []),
                        'ami_type': ng_detail['nodegroup'].get('amiType'),
                        'capacity_type': ng_detail['nodegroup'].get('capacityType'),
                        'scaling_config': ng_detail['nodegroup'].get('scalingConfig', {}),
                        'created_at': ng_detail['nodegroup']['createdAt'].isoformat() if ng_detail['nodegroup'].get('createdAt') else None
                    })
            except ClientError as e:
                logger.warning(f"Could not list node groups: {str(e)}")
            
            # Get Fargate profiles
            fargate_profiles = []
            try:
                fp_response = self.eks_client.list_fargate_profiles(clusterName=cluster_name)
                for fp_name in fp_response.get('fargateProfileNames', []):
                    fp_detail = self.eks_client.describe_fargate_profile(
                        clusterName=cluster_name,
                        fargateProfileName=fp_name
                    )
                    fargate_profiles.append({
                        'name': fp_detail['fargateProfile']['fargateProfileName'],
                        'status': fp_detail['fargateProfile']['status'],
                        'selectors': fp_detail['fargateProfile'].get('selectors', []),
                        'created_at': fp_detail['fargateProfile']['createdAt'].isoformat() if fp_detail['fargateProfile'].get('createdAt') else None
                    })
            except ClientError as e:
                logger.warning(f"Could not list Fargate profiles: {str(e)}")
            
            # Get add-ons
            addons = []
            try:
                addon_response = self.eks_client.list_addons(clusterName=cluster_name)
                for addon_name in addon_response.get('addons', []):
                    addon_detail = self.eks_client.describe_addon(
                        clusterName=cluster_name,
                        addonName=addon_name
                    )
                    addons.append({
                        'name': addon_detail['addon']['addonName'],
                        'status': addon_detail['addon']['status'],
                        'version': addon_detail['addon'].get('addonVersion'),
                        'created_at': addon_detail['addon']['createdAt'].isoformat() if addon_detail['addon'].get('createdAt') else None
                    })
            except ClientError as e:
                logger.warning(f"Could not list add-ons: {str(e)}")
            
            return {
                'cluster': {
                    'name': cluster['name'],
                    'status': cluster['status'],
                    'version': cluster['version'],
                    'platform_version': cluster.get('platformVersion'),
                    'endpoint': cluster.get('endpoint'),
                    'created_at': cluster['createdAt'].isoformat() if cluster.get('createdAt') else None,
                    'arn': cluster['arn'],
                    'role_arn': cluster.get('roleArn'),
                    'vpc_config': cluster.get('resourcesVpcConfig', {}),
                    'logging': cluster.get('logging', {}),
                    'identity': cluster.get('identity', {}),
                    'encryption_config': cluster.get('encryptionConfig', []),
                    'tags': cluster.get('tags', {})
                },
                'node_groups': nodegroups,
                'fargate_profiles': fargate_profiles,
                'addons': addons,
                'region': self.region
            }
            
        except ClientError as e:
            logger.error(f"Failed to get cluster details: {str(e)}")
            raise
    
    def get_cluster_health(self, cluster_name: str) -> Dict[str, Any]:
        """
        Get cluster health status and metrics
        
        Args:
            cluster_name: Name of the EKS cluster
            
        Returns:
            Cluster health information
        """
        try:
            logger.info(f"Checking health for cluster: {cluster_name}")
            
            # Get cluster status
            cluster_response = self.eks_client.describe_cluster(name=cluster_name)
            cluster = cluster_response['cluster']
            
            health_status = {
                'cluster_name': cluster_name,
                'cluster_status': cluster['status'],
                'cluster_version': cluster['version'],
                'endpoint_accessible': bool(cluster.get('endpoint')),
                'issues': [],
                'recommendations': []
            }
            
            # Check cluster status
            if cluster['status'] != 'ACTIVE':
                health_status['issues'].append(f"Cluster status is {cluster['status']}, expected ACTIVE")
            
            # Check node groups health
            try:
                ng_response = self.eks_client.list_nodegroups(clusterName=cluster_name)
                unhealthy_nodegroups = []
                
                for ng_name in ng_response.get('nodegroups', []):
                    ng_detail = self.eks_client.describe_nodegroup(
                        clusterName=cluster_name,
                        nodegroupName=ng_name
                    )
                    ng_status = ng_detail['nodegroup']['status']
                    
                    if ng_status != 'ACTIVE':
                        unhealthy_nodegroups.append(f"{ng_name}: {ng_status}")
                
                if unhealthy_nodegroups:
                    health_status['issues'].extend([f"Unhealthy node groups: {', '.join(unhealthy_nodegroups)}"])
                
                health_status['node_groups_count'] = len(ng_response.get('nodegroups', []))
                
            except ClientError as e:
                health_status['issues'].append(f"Could not check node groups: {str(e)}")
            
            # Check add-ons health
            try:
                addon_response = self.eks_client.list_addons(clusterName=cluster_name)
                unhealthy_addons = []
                
                for addon_name in addon_response.get('addons', []):
                    addon_detail = self.eks_client.describe_addon(
                        clusterName=cluster_name,
                        addonName=addon_name
                    )
                    addon_status = addon_detail['addon']['status']
                    
                    if addon_status not in ['ACTIVE', 'CREATING']:
                        unhealthy_addons.append(f"{addon_name}: {addon_status}")
                
                if unhealthy_addons:
                    health_status['issues'].extend([f"Unhealthy add-ons: {', '.join(unhealthy_addons)}"])
                
                health_status['addons_count'] = len(addon_response.get('addons', []))
                
            except ClientError as e:
                health_status['issues'].append(f"Could not check add-ons: {str(e)}")
            
            # Generate recommendations
            if not health_status['issues']:
                health_status['recommendations'].append("Cluster appears healthy")
            else:
                health_status['recommendations'].append("Review and resolve identified issues")
            
            # Overall health score
            health_status['health_score'] = 'HEALTHY' if not health_status['issues'] else 'UNHEALTHY'
            
            return health_status
            
        except ClientError as e:
            logger.error(f"Failed to check cluster health: {str(e)}")
            raise


def lambda_handler(event, context):
    """
    AWS Lambda handler for EKS operations
    
    Expected event structure:
    {
        "operation": "list_clusters|get_cluster|health_check",
        "cluster_name": "my-cluster",  # Required for get_cluster and health_check
        "region": "us-east-1",         # Optional
        "max_results": 50              # Optional for list_clusters
    }
    """
    try:
        # Validate required parameters
        if 'operation' not in event:
            raise ValueError("Missing required parameter: operation")
        
        operation = event['operation']
        region = event.get('region', os.environ.get('AWS_REGION', 'us-east-1'))
        
        # Initialize EKS manager
        eks_manager = EKSManager(region)
        
        # Execute operation based on type
        if operation == 'list_clusters':
            max_results = event.get('max_results', 100)
            result = eks_manager.list_clusters(max_results)
            
        elif operation == 'get_cluster':
            if 'cluster_name' not in event:
                raise ValueError("Missing required parameter: cluster_name")
            
            result = eks_manager.get_cluster_details(event['cluster_name'])
            
        elif operation == 'health_check':
            if 'cluster_name' not in event:
                raise ValueError("Missing required parameter: cluster_name")
            
            result = eks_manager.get_cluster_health(event['cluster_name'])
            
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'operation': operation,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': result
            }, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }