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
    Check EKS cluster health status and provide recommendations
    
    Single responsibility: Only performs cluster health checks
    
    Expected event:
    {
        "cluster_name": "my-cluster",  # Required
        "region": "us-east-1"          # Optional
    }
    """
    # Correlation ID for tracing
    correlation_id = context.aws_request_id
    logger.info("Starting cluster_health operation", extra={'correlation_id': correlation_id})
    
    try:
        # Validate client initialization
        if not EKS_CLIENT:
            raise RuntimeError("EKS client not initialized")
        
        # Validate required parameters
        if 'cluster_name' not in event:
            raise ValueError("Missing required parameter: cluster_name")
        
        cluster_name = event['cluster_name']
        region = event.get('region', os.environ.get('AWS_REGION', 'us-east-1'))
        
        logger.info(f"Checking cluster health", extra={
            'correlation_id': correlation_id,
            'cluster_name': cluster_name,
            'region': region
        })
        
        # Get cluster status
        cluster_response = EKS_CLIENT.describe_cluster(name=cluster_name)
        cluster = cluster_response['cluster']
        
        # Initialize health status
        health_status = {
            'cluster_name': cluster_name,
            'cluster_status': cluster['status'],
            'cluster_version': cluster['version'],
            'endpoint_accessible': bool(cluster.get('endpoint')),
            'issues': [],
            'recommendations': [],
            'components': {
                'cluster': {'status': cluster['status'], 'healthy': cluster['status'] == 'ACTIVE'},
                'node_groups': {'count': 0, 'healthy_count': 0, 'unhealthy': []},
                'fargate_profiles': {'count': 0, 'healthy_count': 0, 'unhealthy': []},
                'addons': {'count': 0, 'healthy_count': 0, 'unhealthy': []}
            }
        }
        
        # Check cluster status
        if cluster['status'] != 'ACTIVE':
            health_status['issues'].append(f"Cluster status is {cluster['status']}, expected ACTIVE")
        
        # Check node groups health
        try:
            ng_response = EKS_CLIENT.list_nodegroups(clusterName=cluster_name)
            nodegroups = ng_response.get('nodegroups', [])
            health_status['components']['node_groups']['count'] = len(nodegroups)
            
            for ng_name in nodegroups:
                try:
                    ng_detail = EKS_CLIENT.describe_nodegroup(
                        clusterName=cluster_name,
                        nodegroupName=ng_name
                    )
                    ng_status = ng_detail['nodegroup']['status']
                    
                    if ng_status == 'ACTIVE':
                        health_status['components']['node_groups']['healthy_count'] += 1
                    else:
                        health_status['components']['node_groups']['unhealthy'].append({
                            'name': ng_name,
                            'status': ng_status
                        })
                        health_status['issues'].append(f"Node group {ng_name} status: {ng_status}")
                        
                except ClientError as e:
                    logger.warning(f"Could not check node group {ng_name}", extra={
                        'correlation_id': correlation_id,
                        'cluster_name': cluster_name,
                        'nodegroup_name': ng_name,
                        'error': str(e)
                    })
                    health_status['issues'].append(f"Could not check node group {ng_name}: {str(e)}")
                
        except ClientError as e:
            logger.warning(f"Could not list node groups", extra={
                'correlation_id': correlation_id,
                'cluster_name': cluster_name,
                'error': str(e)
            })
            health_status['issues'].append(f"Could not check node groups: {str(e)}")
        
        # Check Fargate profiles health
        try:
            fp_response = EKS_CLIENT.list_fargate_profiles(clusterName=cluster_name)
            fargate_profiles = fp_response.get('fargateProfileNames', [])
            health_status['components']['fargate_profiles']['count'] = len(fargate_profiles)
            
            for fp_name in fargate_profiles:
                try:
                    fp_detail = EKS_CLIENT.describe_fargate_profile(
                        clusterName=cluster_name,
                        fargateProfileName=fp_name
                    )
                    fp_status = fp_detail['fargateProfile']['status']
                    
                    if fp_status == 'ACTIVE':
                        health_status['components']['fargate_profiles']['healthy_count'] += 1
                    else:
                        health_status['components']['fargate_profiles']['unhealthy'].append({
                            'name': fp_name,
                            'status': fp_status
                        })
                        health_status['issues'].append(f"Fargate profile {fp_name} status: {fp_status}")
                        
                except ClientError as e:
                    logger.warning(f"Could not check Fargate profile {fp_name}", extra={
                        'correlation_id': correlation_id,
                        'cluster_name': cluster_name,
                        'fargate_profile_name': fp_name,
                        'error': str(e)
                    })
                    health_status['issues'].append(f"Could not check Fargate profile {fp_name}: {str(e)}")
                
        except ClientError as e:
            logger.warning(f"Could not list Fargate profiles", extra={
                'correlation_id': correlation_id,
                'cluster_name': cluster_name,
                'error': str(e)
            })
            # Fargate profiles are optional, so this is not a critical error
            logger.info("No Fargate profiles found or accessible")
        
        # Check add-ons health
        try:
            addon_response = EKS_CLIENT.list_addons(clusterName=cluster_name)
            addons = addon_response.get('addons', [])
            health_status['components']['addons']['count'] = len(addons)
            
            for addon_name in addons:
                try:
                    addon_detail = EKS_CLIENT.describe_addon(
                        clusterName=cluster_name,
                        addonName=addon_name
                    )
                    addon_status = addon_detail['addon']['status']
                    
                    if addon_status in ['ACTIVE', 'CREATING']:
                        health_status['components']['addons']['healthy_count'] += 1
                    else:
                        health_status['components']['addons']['unhealthy'].append({
                            'name': addon_name,
                            'status': addon_status
                        })
                        health_status['issues'].append(f"Add-on {addon_name} status: {addon_status}")
                        
                except ClientError as e:
                    logger.warning(f"Could not check add-on {addon_name}", extra={
                        'correlation_id': correlation_id,
                        'cluster_name': cluster_name,
                        'addon_name': addon_name,
                        'error': str(e)
                    })
                    health_status['issues'].append(f"Could not check add-on {addon_name}: {str(e)}")
                
        except ClientError as e:
            logger.warning(f"Could not list add-ons", extra={
                'correlation_id': correlation_id,
                'cluster_name': cluster_name,
                'error': str(e)
            })
            # Add-ons are optional, so this is not a critical error
            logger.info("No add-ons found or accessible")
        
        # Generate health score and recommendations
        total_components = (
            1 +  # cluster itself
            health_status['components']['node_groups']['count'] +
            health_status['components']['fargate_profiles']['count'] +
            health_status['components']['addons']['count']
        )
        
        healthy_components = (
            (1 if health_status['components']['cluster']['healthy'] else 0) +
            health_status['components']['node_groups']['healthy_count'] +
            health_status['components']['fargate_profiles']['healthy_count'] +
            health_status['components']['addons']['healthy_count']
        )
        
        if total_components > 0:
            health_percentage = (healthy_components / total_components) * 100
        else:
            health_percentage = 0
        
        # Determine overall health status
        if health_percentage == 100 and not health_status['issues']:
            health_status['health_score'] = 'HEALTHY'
            health_status['recommendations'].append("Cluster appears to be in good health")
        elif health_percentage >= 80:
            health_status['health_score'] = 'WARNING'
            health_status['recommendations'].append("Some components need attention but cluster is mostly functional")
        else:
            health_status['health_score'] = 'UNHEALTHY'
            health_status['recommendations'].append("Multiple components require immediate attention")
        
        # Add specific recommendations based on issues
        if health_status['issues']:
            health_status['recommendations'].append("Review and resolve the identified issues")
            health_status['recommendations'].append("Check CloudWatch logs for detailed error information")
        
        # Add general recommendations
        if health_status['components']['node_groups']['count'] == 0 and health_status['components']['fargate_profiles']['count'] == 0:
            health_status['recommendations'].append("Consider adding node groups or Fargate profiles to run workloads")
        
        health_status['health_percentage'] = round(health_percentage, 2)
        
        logger.info(f"Cluster health check completed", extra={
            'correlation_id': correlation_id,
            'cluster_name': cluster_name,
            'health_score': health_status['health_score'],
            'health_percentage': health_status['health_percentage'],
            'issues_count': len(health_status['issues'])
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
                'operation': 'cluster_health',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'correlation_id': correlation_id,
                'data': health_status
            }, default=str)
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(f"AWS API error in cluster_health", extra={
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
        logger.error(f"Validation error in cluster_health", extra={
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
        logger.error(f"Unexpected error in cluster_health", extra={
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