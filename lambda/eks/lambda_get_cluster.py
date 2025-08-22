import json
import boto3
import logging
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients outside handler for reuse across invocations
try:
    EKS_CLIENT = boto3.client('eks', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
except Exception as e:
    logger.error(f"Failed to initialize EKS client: {str(e)}")
    EKS_CLIENT = None

def lambda_handler(event, context):
    """
    Get detailed information about a specific EKS cluster
    
    Single responsibility: Only retrieves detailed cluster information
    
    Expected event:
    {
        "cluster_name": "my-cluster",  # Required
        "region": "us-east-1"          # Optional
    }
    """
    # Correlation ID for tracing
    correlation_id = context.aws_request_id
    logger.info("Starting get_cluster operation", extra={'correlation_id': correlation_id})
    
    try:
        # Validate client initialization
        if not EKS_CLIENT:
            raise RuntimeError("EKS client not initialized")
        
        # Validate required parameters
        if 'cluster_name' not in event:
            raise ValueError("Missing required parameter: cluster_name")
        
        cluster_name = event['cluster_name']
        region = event.get('region', os.environ.get('AWS_REGION', 'us-east-1'))
        
        logger.info(f"Getting cluster details", extra={
            'correlation_id': correlation_id,
            'cluster_name': cluster_name,
            'region': region
        })
        
        # Get cluster details
        cluster_response = EKS_CLIENT.describe_cluster(name=cluster_name)
        cluster = cluster_response['cluster']
        
        # Get node groups with error handling
        nodegroups = []
        try:
            ng_response = EKS_CLIENT.list_nodegroups(clusterName=cluster_name)
            for ng_name in ng_response.get('nodegroups', []):
                try:
                    ng_detail = EKS_CLIENT.describe_nodegroup(
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
                    logger.warning(f"Could not describe node group {ng_name}", extra={
                        'correlation_id': correlation_id,
                        'cluster_name': cluster_name,
                        'nodegroup_name': ng_name,
                        'error': str(e)
                    })
        except ClientError as e:
            logger.warning(f"Could not list node groups", extra={
                'correlation_id': correlation_id,
                'cluster_name': cluster_name,
                'error': str(e)
            })
        
        # Get Fargate profiles with error handling
        fargate_profiles = []
        try:
            fp_response = EKS_CLIENT.list_fargate_profiles(clusterName=cluster_name)
            for fp_name in fp_response.get('fargateProfileNames', []):
                try:
                    fp_detail = EKS_CLIENT.describe_fargate_profile(
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
                    logger.warning(f"Could not describe Fargate profile {fp_name}", extra={
                        'correlation_id': correlation_id,
                        'cluster_name': cluster_name,
                        'fargate_profile_name': fp_name,
                        'error': str(e)
                    })
        except ClientError as e:
            logger.warning(f"Could not list Fargate profiles", extra={
                'correlation_id': correlation_id,
                'cluster_name': cluster_name,
                'error': str(e)
            })
        
        # Get add-ons with error handling
        addons = []
        try:
            addon_response = EKS_CLIENT.list_addons(clusterName=cluster_name)
            for addon_name in addon_response.get('addons', []):
                try:
                    addon_detail = EKS_CLIENT.describe_addon(
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
                    logger.warning(f"Could not describe add-on {addon_name}", extra={
                        'correlation_id': correlation_id,
                        'cluster_name': cluster_name,
                        'addon_name': addon_name,
                        'error': str(e)
                    })
        except ClientError as e:
            logger.warning(f"Could not list add-ons", extra={
                'correlation_id': correlation_id,
                'cluster_name': cluster_name,
                'error': str(e)
            })
        
        # Build comprehensive cluster information
        result = {
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
            'region': region
        }
        
        logger.info(f"Successfully retrieved cluster details", extra={
            'correlation_id': correlation_id,
            'cluster_name': cluster_name,
            'node_groups_count': len(nodegroups),
            'fargate_profiles_count': len(fargate_profiles),
            'addons_count': len(addons)
        })
        
        # Structured response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'X-Correlation-ID': correlation_id
            },
            'body': json.dumps({
                'success': True,
                'operation': 'get_cluster',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'correlation_id': correlation_id,
                'data': result
            }, default=str)
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(f"AWS API error in get_cluster", extra={
            'correlation_id': correlation_id,
            'cluster_name': event.get('cluster_name'),
            'error_code': error_code,
            'error_message': str(e)
        })
        
        # Handle specific error cases
        status_code = 404 if error_code == 'ResourceNotFoundException' else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'X-Correlation-ID': correlation_id
            },
            'body': json.dumps({
                'success': False,
                'error': f"AWS API Error: {error_code}",
                'correlation_id': correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except ValueError as e:
        logger.error(f"Validation error in get_cluster", extra={
            'correlation_id': correlation_id,
            'error': str(e)
        })
        
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'X-Correlation-ID': correlation_id
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'correlation_id': correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_cluster", extra={
            'correlation_id': correlation_id,
            'error': str(e)
        })
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'X-Correlation-ID': correlation_id
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'correlation_id': correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }