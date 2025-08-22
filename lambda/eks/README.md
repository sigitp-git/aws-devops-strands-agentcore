# AWS EKS Lambda Functions

A collection of AWS Lambda functions for EKS cluster management, following AWS Lambda best practices with single responsibility principle.

## Architecture Overview

This implementation follows the **single responsibility principle** with separate Lambda functions for each operation:

- **`lambda_list_clusters.py`** - List EKS clusters with pagination
- **`lambda_get_cluster.py`** - Get detailed cluster information  
- **`lambda_cluster_health.py`** - Perform cluster health checks

## AWS Lambda Best Practices Implemented

### ✅ Function Design & Architecture
- **Single Responsibility**: Each function handles one specific operation
- **Independent Scaling**: Functions scale independently based on usage
- **Clear Error Isolation**: Issues in one function don't affect others
- **Granular Monitoring**: Individual CloudWatch metrics per function

### ✅ Performance Optimization
- **Cold Start Optimization**: Minimal dependencies, small packages
- **ARM64 Architecture**: Better price-performance with Graviton2
- **Connection Reuse**: AWS clients initialized outside handlers
- **Right-sized Memory**: 256MB with appropriate timeout settings

### ✅ Code Best Practices
- **Structured Logging**: JSON format with correlation IDs
- **Environment Variables**: Configuration through env vars
- **Error Handling**: Comprehensive exception handling with specific HTTP status codes
- **Input Validation**: Parameter validation with clear error messages

### ✅ Security Best Practices
- **Least Privilege IAM**: Minimal required permissions
- **No Embedded Credentials**: Uses IAM roles
- **Specific Resource ARNs**: Where possible, avoiding wildcards

### ✅ Monitoring & Observability
- **Correlation IDs**: Request tracing across function execution
- **Structured Responses**: Consistent JSON response format
- **Detailed Logging**: Operation context and error details
- **HTTP Status Codes**: Proper status codes for different scenarios

## Quick Start

### 1. Deploy All Functions

```bash
cd lambda/eks
./deploy_lambda.sh
```

This will:
- Create IAM role with least privilege permissions
- Deploy all three Lambda functions
- Configure ARM64 architecture for cost optimization
- Set up proper environment variables and timeouts

### 2. Test Individual Functions

```bash
# List clusters
aws lambda invoke \
  --function-name aws-devops-eks-list-clusters \
  --payload '{"max_results":10}' \
  response.json

# Get cluster details
aws lambda invoke \
  --function-name aws-devops-eks-get-cluster \
  --payload '{"cluster_name":"my-cluster"}' \
  response.json

# Check cluster health
aws lambda invoke \
  --function-name aws-devops-eks-cluster-health \
  --payload '{"cluster_name":"my-cluster"}' \
  response.json
```

## Function Details

### 1. List Clusters (`aws-devops-eks-list-clusters`)

**Purpose**: List EKS clusters with pagination support

**Input**:
```json
{
  "max_results": 50,     // Optional, defaults to 100, max 100
  "region": "us-east-1"  // Optional, uses environment default
}
```

**Output**:
```json
{
  "success": true,
  "operation": "list_clusters",
  "timestamp": "2023-01-01T12:00:00Z",
  "correlation_id": "abc-123",
  "data": {
    "clusters": [
      {
        "name": "my-cluster",
        "status": "ACTIVE",
        "version": "1.24",
        "created_at": "2023-01-01T10:00:00Z",
        "arn": "arn:aws:eks:us-east-1:123456789012:cluster/my-cluster",
        "tags": {}
      }
    ],
    "count": 1,
    "region": "us-east-1"
  }
}
```

### 2. Get Cluster (`aws-devops-eks-get-cluster`)

**Purpose**: Get comprehensive cluster information including node groups, Fargate profiles, and add-ons

**Input**:
```json
{
  "cluster_name": "my-cluster",  // Required
  "region": "us-east-1"          // Optional
}
```

**Output**:
```json
{
  "success": true,
  "operation": "get_cluster",
  "timestamp": "2023-01-01T12:00:00Z",
  "correlation_id": "abc-123",
  "data": {
    "cluster": {
      "name": "my-cluster",
      "status": "ACTIVE",
      "version": "1.24",
      "endpoint": "https://...",
      "vpc_config": {},
      "logging": {},
      "tags": {}
    },
    "node_groups": [],
    "fargate_profiles": [],
    "addons": [],
    "region": "us-east-1"
  }
}
```

### 3. Cluster Health (`aws-devops-eks-cluster-health`)

**Purpose**: Comprehensive health check with recommendations

**Input**:
```json
{
  "cluster_name": "my-cluster",  // Required
  "region": "us-east-1"          // Optional
}
```

**Output**:
```json
{
  "success": true,
  "operation": "cluster_health",
  "timestamp": "2023-01-01T12:00:00Z",
  "correlation_id": "abc-123",
  "data": {
    "cluster_name": "my-cluster",
    "cluster_status": "ACTIVE",
    "health_score": "HEALTHY",
    "health_percentage": 100.0,
    "issues": [],
    "recommendations": ["Cluster appears to be in good health"],
    "components": {
      "cluster": {"status": "ACTIVE", "healthy": true},
      "node_groups": {"count": 2, "healthy_count": 2, "unhealthy": []},
      "fargate_profiles": {"count": 0, "healthy_count": 0, "unhealthy": []},
      "addons": {"count": 3, "healthy_count": 3, "unhealthy": []}
    }
  }
}
```

## Error Handling

All functions implement comprehensive error handling:

- **400 Bad Request**: Missing or invalid parameters
- **404 Not Found**: Cluster not found
- **500 Internal Server Error**: AWS API errors or unexpected issues

Error responses include correlation IDs for tracing:

```json
{
  "success": false,
  "error": "Missing required parameter: cluster_name",
  "correlation_id": "abc-123",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

## IAM Permissions

The deployment script creates a role with minimal required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:ListNodegroups",
        "eks:DescribeNodegroup",
        "eks:ListFargateProfiles",
        "eks:DescribeFargateProfile",
        "eks:ListAddons",
        "eks:DescribeAddon"
      ],
      "Resource": "*"
    }
  ]
}
```

## Integration Examples

### With Main Agent

```python
import boto3
import json

lambda_client = boto3.client('lambda')

class EKSLambdaIntegration:
    def __init__(self):
        self.lambda_client = lambda_client
    
    def list_clusters(self, max_results=50):
        response = self.lambda_client.invoke(
            FunctionName='aws-devops-eks-list-clusters',
            Payload=json.dumps({'max_results': max_results})
        )
        return json.loads(response['Payload'].read())
    
    def get_cluster_details(self, cluster_name):
        response = self.lambda_client.invoke(
            FunctionName='aws-devops-eks-get-cluster',
            Payload=json.dumps({'cluster_name': cluster_name})
        )
        return json.loads(response['Payload'].read())
    
    def check_cluster_health(self, cluster_name):
        response = self.lambda_client.invoke(
            FunctionName='aws-devops-eks-cluster-health',
            Payload=json.dumps({'cluster_name': cluster_name})
        )
        return json.loads(response['Payload'].read())
```

### With Step Functions

```json
{
  "Comment": "EKS Cluster Health Check Workflow",
  "StartAt": "ListClusters",
  "States": {
    "ListClusters": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:aws-devops-eks-list-clusters",
      "Next": "CheckEachCluster"
    },
    "CheckEachCluster": {
      "Type": "Map",
      "ItemsPath": "$.data.clusters",
      "Iterator": {
        "StartAt": "CheckHealth",
        "States": {
          "CheckHealth": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:aws-devops-eks-cluster-health",
            "Parameters": {
              "cluster_name.$": "$.name"
            },
            "End": true
          }
        }
      },
      "End": true
    }
  }
}
```

## Monitoring

Each function automatically creates CloudWatch log groups:
- `/aws/lambda/aws-devops-eks-list-clusters`
- `/aws/lambda/aws-devops-eks-get-cluster`
- `/aws/lambda/aws-devops-eks-cluster-health`

Key metrics to monitor:
- **Duration**: Function execution time
- **Error Rate**: Failed invocations
- **Throttles**: Rate limiting events
- **Concurrent Executions**: Scaling behavior

## Cost Optimization

- **ARM64 Architecture**: ~20% cost savings vs x86
- **Right-sized Memory**: 256MB optimized for EKS API calls
- **Efficient Pagination**: Prevents large response payloads
- **Connection Reuse**: Reduces initialization overhead

## Development

### Local Testing

```bash
# Test individual functions locally
python3 lambda_list_clusters.py
python3 lambda_get_cluster.py
python3 lambda_cluster_health.py
```

### Adding New Functions

1. Create new function file following the pattern
2. Add to `FUNCTIONS` array in `deploy_lambda.sh`
3. Update IAM permissions if needed
4. Deploy with `./deploy_lambda.sh`

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check IAM role permissions
2. **Timeout**: Increase timeout or optimize queries
3. **Cold Starts**: Consider provisioned concurrency for critical functions

### Debug Mode

Set environment variable for detailed logging:
```bash
aws lambda update-function-configuration \
  --function-name aws-devops-eks-list-clusters \
  --environment Variables="{LOG_LEVEL=DEBUG}"
```

## Next Steps

1. **Add CloudWatch Alarms**: Monitor error rates and duration
2. **Implement X-Ray Tracing**: Distributed tracing across functions
3. **Add Integration Tests**: Automated testing pipeline
4. **Consider Lambda Layers**: Share common dependencies
5. **Implement Dead Letter Queues**: Handle failed invocations

This architecture provides a solid foundation for EKS management operations while following AWS Lambda best practices for maintainability, performance, and cost optimization.