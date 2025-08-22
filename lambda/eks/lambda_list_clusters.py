import json
import boto3
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients outside handler for reuse
try:
    EKS_CLIENT = boto3.client('eks', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
except Exception as e:
    logger.error(f"Failed to initialize EKS client: {str(e)}")
    EKS_CLIENT = None

def lambda_handler(event, context):
    """
    List EKS clusters with pagination support
    
    Single responsibility: Only lists EKS clusters
    
    Expected event:
    {
        "max_results": 50,  # Optional, defaults to 100
        "region": "us-east-1"  # Optional
    }
    """
    # Correlation ID for tracing
    correlation_id = context.aws_request_id
    logger.info(f"Starting list_clusters operation", extra={'correlation_id': correlation_id})
    
    try:
        # Validate client initialization
        if not EKS_CLIENT:
            raise RuntimeError("EKS client not initialized")
        
        # Get parameters with defaults
        max_results = min(event.get('max_results', 100), 100)  # Cap at 100 for performance
        region = event.get('region', os.environ.get('AWS_REGION', 'us-east-1'))
        
        logger.info(f"Listing EKS clusters", extra={
            'correlation_id': correlation_id,
            'max_results': max_results,
            'region': region
        })
        
        clusters = []
        paginator = EKS_CLIENT.get_paginator('list_clusters')
        
        # Use pagination for efficient memory usage
        for page in paginator.paginate(maxResults=min(max_results, 100)):
            for cluster_name in page.get('clusters', []):
                try:
                    # Get basic cluster information
                    cluster_detail = EKS_CLIENT.describe_cluster(name=cluster_name)
                    cluster_info = cluster_detail['cluster']
                    
                    # Extract only essential information for list operation
                    clusters.append({
                        'name': cluster_info['name'],
                        'status': cluster_info['status'],
                        'version': cluster_info['version'],
                        'created_at': cluster_info['createdAt'].isoformat() if cluster_info.get('createdAt') else None,
                        'arn': cluster_info['arn'],
                        'tags': cluster_info.get('tags', {})
                    })
                    
                    if len(clusters) >= max_results:
                        break
                        
                except ClientError as e:
                    logger.warning(f"Could not describe cluster {cluster_name}", extra={
                        'correlation_id': correlation_id,
                        'cluster_name': cluster_name,
                        'error': str(e)
                    })
                    continue
            
            if len(clusters) >= max_results:
                break
        
        result = {
            'clusters': clusters,
            'count': len(clusters),
            'region': region
        }
        
        logger.info(f"Successfully listed {len(clusters)} clusters", extra={
            'correlation_id': correlation_id,
            'cluster_count': len(clusters)
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
                'operation': 'list_clusters',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'correlation_id': correlation_id,
                'data': result
            }, default=str)
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(f"AWS API error in list_clusters", extra={
            'correlation_id': correlation_id,
            'error_code': error_code,
            'error_message': str(e)
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
                'error': f"AWS API Error: {error_code}",
                'correlation_id': correlation_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in list_clusters", extra={
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