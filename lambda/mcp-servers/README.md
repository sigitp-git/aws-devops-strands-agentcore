# MCP Servers as Lambda Functions

This directory contains AWS Lambda implementations of MCP (Model Context Protocol) servers for AgentCore Gateway integration. Each MCP server is implemented as a specialized Lambda function following AWS Lambda best practices.

## Architecture Overview

The MCP servers are deployed as individual Lambda functions that integrate with the Bedrock AgentCore Gateway through the MCP framework. This provides:

- **Scalability**: Automatic scaling based on demand
- **Cost Efficiency**: Pay only for actual usage
- **Security**: IAM-based permissions and VPC integration
- **Reliability**: Built-in error handling and retry mechanisms
- **Monitoring**: CloudWatch logging and metrics

## Available MCP Servers

### Core Services
- **`core_lambda.py`** - Core MCP server functionality and AWS context
- **`aws_documentation_lambda.py`** - AWS documentation search and retrieval
- **`aws_pricing_lambda.py`** - AWS pricing information and cost analysis

### Infrastructure & DevOps
- **`cloudwatch_lambda.py`** - CloudWatch logs, metrics, and monitoring
- **`eks_lambda.py`** - EKS cluster management and Kubernetes operations
- **`terraform_lambda.py`** - Terraform configuration and validation

### Development & Research
- **`git_repo_research_lambda.py`** - Git repository research and code analysis
- **`frontend_lambda.py`** - Frontend development guidance and React documentation

### Location Services
- **`aws_location_lambda.py`** - AWS Location Service operations and mapping

## Deployment

### Quick Deployment
Deploy all MCP servers with a single command:

```bash
./deploy_all_mcp_servers.sh
```

### Manual Deployment
Use the Python deployment script for more control:

```bash
cd ../../awslabs-mcp/
python3 deploy_mcp_lambdas.py
```

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.11+ runtime
- IAM permissions for Lambda, IAM, and SSM operations

## Testing

### Run All Tests
```bash
python3 test_mcp_lambdas.py
```

### Test Individual Functions
```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Test core server
response = lambda_client.invoke(
    FunctionName='mcp-core-server',
    Payload=json.dumps({
        'operation': 'prompt_understanding',
        'parameters': {}
    })
)

print(json.loads(response['Payload'].read()))
```

## Function Specifications

### Common Interface
All Lambda functions follow a consistent interface:

```python
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Standard Lambda handler interface.
    
    Args:
        event: {
            'operation': str,      # Operation to perform
            'parameters': dict     # Operation-specific parameters
        }
        context: Lambda context object
    
    Returns:
        {
            'statusCode': int,     # HTTP status code
            'body': str           # JSON response body
        }
    """
```

### Response Format
All functions return standardized responses:

```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "operation": "operation_name",
    "results": {},
    "error": "error_message"  // Only present on failure
  }
}
```

## Configuration

### Environment Variables
Each Lambda function supports these environment variables:
- `AWS_REGION` - AWS region for operations
- `MCP_SERVER_NAME` - Name of the MCP server
- `FASTMCP_LOG_LEVEL` - Logging level (ERROR, WARNING, INFO, DEBUG)

### IAM Permissions
The deployment script creates an IAM role with these permissions:
- Basic Lambda execution permissions
- SSM Parameter Store access
- AWS service-specific permissions (S3, Bedrock, CloudWatch, etc.)

### Memory and Timeout
- **Memory**: 512 MB (optimized for most operations)
- **Timeout**: 300 seconds (5 minutes)
- **Runtime**: Python 3.11

## Integration with AgentCore Gateway

### MCP Configuration
Update your `mcp.json` to use Lambda functions instead of local processes:

```json
{
  "mcpServers": {
    "awslabs.core-mcp-server": {
      "command": "lambda",
      "args": ["mcp-core-server"],
      "env": {
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### Gateway Configuration
Configure the AgentCore Gateway to invoke Lambda functions:

```json
{
  "gateway": {
    "lambda_functions": {
      "mcp-core-server": "arn:aws:lambda:us-east-1:123456789012:function:mcp-core-server"
    }
  }
}
```

## Monitoring and Debugging

### CloudWatch Logs
Each function logs to CloudWatch with the log group:
```
/aws/lambda/mcp-{server-name}
```

### Metrics
Monitor these CloudWatch metrics:
- **Duration** - Function execution time
- **Errors** - Number of failed invocations
- **Throttles** - Number of throttled invocations
- **Invocations** - Total number of invocations

### Debugging
Enable debug logging by setting environment variable:
```bash
FASTMCP_LOG_LEVEL=DEBUG
```

## Cost Optimization

### Right-Sizing
Functions are configured with appropriate memory and timeout:
- **Lightweight operations** (docs, pricing): 256 MB, 30s
- **Standard operations** (core, frontend): 512 MB, 300s
- **Heavy operations** (EKS, research): 1024 MB, 300s

### Cold Start Optimization
- Minimal dependencies in requirements.txt
- Efficient imports and initialization
- Connection reuse across invocations

## Security Best Practices

### IAM Permissions
- Principle of least privilege
- Function-specific IAM roles
- No hardcoded credentials

### VPC Configuration
- Optional VPC deployment for sensitive operations
- Security group restrictions
- Private subnet deployment

### Data Protection
- Encryption in transit and at rest
- Secure parameter storage in SSM
- No sensitive data in logs

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check IAM role permissions
   - Verify resource ARNs in policies

2. **Timeout Errors**
   - Increase function timeout
   - Optimize code for performance
   - Check external service latency

3. **Memory Errors**
   - Increase memory allocation
   - Optimize data structures
   - Use streaming for large datasets

4. **Cold Start Issues**
   - Use provisioned concurrency for critical functions
   - Minimize package size
   - Optimize imports

### Debug Commands
```bash
# Check function configuration
aws lambda get-function --function-name mcp-core-server

# View recent logs
aws logs tail /aws/lambda/mcp-core-server --follow

# Test function locally
python3 -c "
import json
from core_lambda import lambda_handler
result = lambda_handler({'operation': 'get_aws_context'}, None)
print(json.dumps(result, indent=2))
"
```

## Development

### Adding New Operations
1. Add operation handler to the appropriate Lambda function
2. Update the operation routing in `lambda_handler`
3. Add test cases to `test_mcp_lambdas.py`
4. Update documentation

### Creating New MCP Servers
1. Create new Lambda function file following the pattern
2. Add to `deploy_all_mcp_servers.sh`
3. Add test cases to test suite
4. Update MCP configuration

## Performance Benchmarks

Typical performance metrics:
- **Cold start**: 1-3 seconds
- **Warm execution**: 50-500ms
- **Memory usage**: 50-200 MB
- **Cost per invocation**: $0.0000002-$0.0000020

## Migration from Local MCP Servers

### Benefits of Lambda Migration
- **No local process management**
- **Automatic scaling and availability**
- **Centralized logging and monitoring**
- **Better security model**
- **Cost optimization**

### Migration Steps
1. Deploy Lambda functions using provided scripts
2. Test functions with test suite
3. Update MCP configuration to use Lambda endpoints
4. Configure AgentCore Gateway integration
5. Monitor and optimize performance

## Support and Maintenance

### Regular Maintenance
- Monitor CloudWatch metrics and alarms
- Update dependencies in requirements.txt
- Review and rotate IAM permissions
- Optimize function performance based on usage patterns

### Updates and Patches
- Use blue/green deployment with aliases
- Test updates in staging environment
- Monitor error rates after deployments
- Maintain rollback capability

For additional support, refer to the main project documentation or create an issue in the GitHub repository.