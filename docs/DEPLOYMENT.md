# AWS DevOps Agent - Deployment Guide

This comprehensive guide covers all deployment options for the AWS DevOps Agent, including local development, cloud deployment via Amazon Bedrock AgentCore Runtime, and Lambda functions.

## Deployment Modes

### 1. **Local CLI Mode** (Development)
- **File**: `agent.py`
- **Usage**: `python3 agent.py`
- **Features**: Interactive conversation, full memory integration, MCP tools
- **Purpose**: Development, testing, and local usage

### 2. **Local Runtime Mode** (Testing)
- **File**: `agent_runtime.py`
- **Usage**: `python3 agent_runtime.py`
- **Features**: HTTP API endpoints (`/invocations`, `/ping`)
- **Purpose**: Local testing of production API

### 3. **AgentCore Runtime Mode** (Production) ✅ **DEPLOYED**
- **Deployment**: `python3 deploy_runtime.py`
- **Runtime ARN**: `arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/devops_agent-*`
- **Features**: Managed AWS service, auto-scaling, monitoring
- **Purpose**: Production deployment with AWS managed infrastructure

### 4. **Lambda MCP Servers** (Production) ✅ **DEPLOYED**
- **Deployment**: `./lambda/mcp-servers/deploy_all_mcp_servers.sh`
- **Functions**: 9 Lambda functions replacing local MCP processes
- **Features**: Scalable microservices, AgentCore Gateway integration
- **Purpose**: Production-ready MCP server infrastructure

## AgentCore Runtime Features

- **Scalable HTTP API** - Deploy as containerized service
- **AWS Integration** - Native integration with AWS services
- **Production Ready** - Built-in health checks and monitoring
- **MCP Tools Integration** - Advanced functionality via MCP gateway
- **Optimized Performance** - 4-5 second response times for basic queries
- **Conservative Web Search** - Only triggers when explicitly requested

## Quick Start

### Local Testing

Test the runtime version locally before deployment:

```bash
# Test full runtime with MCP tools (recommended)
python3 tests/test_runtime_local.py

# Test basic functionality only
python3 tests/test_simple_runtime.py

# Manual testing
python3 agent_runtime.py &
curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d '{"prompt": "Hello"}'
```

### Production Deployment ✅ **COMPLETED**

The agent has been successfully deployed to Amazon Bedrock AgentCore Runtime:

```bash
# Deploy to AgentCore Runtime (already completed)
python3 deploy_runtime.py
```

**Deployment Results:**
- ✅ **Runtime ARN**: `arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/devops_agent-*`
- ✅ **Status**: Successfully deployed and operational
- ✅ **Container**: ARM64 Docker image in ECR
- ✅ **IAM Role**: `AgentRuntimeExecutionRole` with proper permissions

### Using Deployed Agent

```bash
# Interactive mode with deployed agent
python3 invoke_runtime.py interactive

# Single invocation
python3 invoke_runtime.py invoke "What are AWS best practices?"

# Run test scenarios
python3 invoke_runtime.py test
```

## API Endpoints

### POST /invocations

Main agent processing endpoint.

**Request:**
```json
{
  "prompt": "What are AWS best practices for EC2?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "message": "Here are key AWS best practices for EC2...",
  "timestamp": "2024-01-01T12:00:00Z",
  "model": "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "session_id": "session-123",
  "status": "success",
  "tools_used": ["websearch"]
}
```

### GET /ping

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Prerequisites

### AWS Requirements
- AWS CLI configured with appropriate credentials
- Access to Amazon Bedrock and AgentCore Runtime services
- IAM role for AgentCore Runtime execution
- ECR repository for container images

### Local Requirements
- Python 3.8+
- Docker with buildx support (for deployment)
- AWS region set to `us-east-1` (default)

## Configuration

### IAM Role Configuration ✅ **CONFIGURED**

The deployment script automatically created the `AgentRuntimeExecutionRole` with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/app/devopsagent/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:devops-agent-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    }
  ]
}
```

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### SSM Parameters ✅ **CONFIGURED**

The deployment script created/uses these SSM parameters:

- `/app/devopsagent/agentcore/execution_role_arn` - IAM role for runtime ✅
- `/app/devopsagent/agentcore/runtime_arn` - Deployed agent ARN ✅
- `/app/devopsagent/agentcore/gateway_id` - MCP Gateway ID ✅
- `/app/devopsagent/agentcore/machine_client_id` - Cognito client ID ✅
- `/app/devopsagent/agentcore/cognito_discovery_url` - OIDC discovery URL ✅
- `/app/devopsagent/agentcore/memory_id` - AgentCore Memory resource ID ✅

## Manual Deployment

### Build Docker Image

```bash
# Create buildx builder (one time)
docker buildx create --use

# Build ARM64 image
docker buildx build --platform linux/arm64 -f Dockerfile.runtime -t devops-agent:runtime .
```

### Deploy with AWS CLI

```bash
# Create ECR repository
aws ecr create-repository --repository-name devops-agent-runtime

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag devops-agent:runtime ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/devops-agent-runtime:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/devops-agent-runtime:latest

# Deploy to AgentCore Runtime
aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name devops-agent \
  --agent-runtime-artifact containerConfiguration='{containerUri=ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/devops-agent-runtime:latest}' \
  --network-configuration networkMode=PUBLIC \
  --role-arn arn:aws:iam::ACCOUNT:role/AgentRuntimeExecutionRole
```

## Architecture

```
Local Mode:           Runtime Mode:
┌─────────────┐      ┌─────────────┐    ┌──────────────┐
│   Terminal  │      │   HTTP      │───▶│  AgentCore   │
│   (CLI)     │      │   Client    │    │  Runtime     │
└─────────────┘      └─────────────┘    └──────────────┘
       │                                        │
       ▼                                        ▼
┌─────────────┐                        ┌──────────────┐
│ agent.py    │                        │ Docker       │
│ (Direct)    │                        │ Container    │
└─────────────┘                        └──────────────┘
       │                                        │
       ▼                                        ▼
┌─────────────────────────────────────────────────────┐
│           Same Core Functionality                   │
│  • Bedrock Model  • MCP Tools  • Web Search       │
└─────────────────────────────────────────────────────┘
```

## Monitoring

### CloudWatch Logs

Agent logs are automatically sent to CloudWatch:

```bash
# View logs
aws logs describe-log-groups --log-group-name-prefix "/aws/bedrock-agentcore"
```

### Health Monitoring

Monitor the `/ping` endpoint for health status:

```bash
# Check health
curl https://your-agent-runtime-url/ping
```

## Troubleshooting

### Common Issues

1. **Build Fails**
   - Ensure Docker buildx is installed: `docker buildx create --use`
   - Check ARM64 platform support

2. **Deployment Fails**
   - Verify IAM role permissions
   - Check ECR repository exists
   - Ensure AgentCore Runtime is available in your region

3. **Invocation Fails**
   - Check agent runtime status in AWS Console
   - Verify MCP gateway configuration
   - Check CloudWatch logs for errors

4. **Slow Response Times**
   - Web search queries take 30-60 seconds (expected)
   - Basic queries should respond in 4-5 seconds
   - MCP tool initialization adds ~1 second

5. **MCP Tools Not Working**
   - Verify gateway configuration in SSM parameters
   - Check Cognito authentication setup
   - Ensure gateway IAM role has proper permissions

### Debug Commands

```bash
# Check Docker buildx
docker buildx ls

# Test local runtime
python3 tests/test_runtime_local.py

# Check AWS permissions
aws sts get-caller-identity
aws bedrock-agentcore-control list-agent-runtimes

# View agent logs
aws logs tail /aws/bedrock-agentcore/your-agent-name --follow
```

## Cost Considerations

- **AgentCore Runtime** - Pay per invocation
- **ECR Storage** - Minimal cost for Docker images
- **Bedrock Model** - Pay per token (same as local mode)
- **MCP Gateway** - Pay per request

## Performance Characteristics

- **Basic Queries**: 4-5 seconds
- **Web Search Queries**: 30-60 seconds
- **MCP Tool Queries**: 5-10 seconds
- **Error Responses**: <1 second
- **Concurrent Requests**: Supported with auto-scaling

## Development Workflow

1. **Develop locally** with `agent.py`
2. **Test runtime** with `tests/test_runtime_local.py`
3. **Deploy to AWS** with `deploy_runtime.py`
4. **Invoke remotely** with `invoke_runtime.py`

## Deployment Status

- ✅ **Local CLI Mode** - Fully operational
- ✅ **Local Runtime Mode** - HTTP API server working
- ✅ **AgentCore Runtime** - **SUCCESSFULLY DEPLOYED TO PRODUCTION**
- ✅ **Docker Image** - ARM64 container built and pushed to ECR
- ✅ **IAM Configuration** - Execution role created with proper permissions
- ✅ **MCP Integration** - All tools working with secure authentication
- ✅ **Web Search** - Lambda function deployed and operational
- ✅ **Error Handling** - Comprehensive validation and recovery
- ✅ **Performance** - Optimized for cloud deployment
#
# Lambda Functions

The project includes deployable AWS Lambda functions following microservices architecture and best practices:

## Web Search Function

### Lambda Function Features
- **Function Name**: `devops-agent-websearch`
- **Runtime**: Python 3.11 with 256MB memory
- **Web Search**: DuckDuckGo integration with rate limit handling
- **Error Handling**: Comprehensive validation and error responses
- **CloudWatch Logging**: Full logging for debugging and monitoring

### Deploy the Web Search Function

```bash
cd lambda/websearch/
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

### Test the Web Search Function

**Test locally:**
```bash
cd lambda/websearch/
python3 test_lambda_local.py
```

**Test the deployed function:**
```bash
cd lambda/websearch/
aws lambda invoke --function-name devops-agent-websearch \
  --payload '{"keywords": "terraform aws provider", "max_results": 3}' \
  response.json
```

## Prometheus Monitoring Functions

The project demonstrates Lambda best practices with specialized Prometheus monitoring functions designed for AgentCore Gateway integration:

### Microservices Architecture
- **prometheus-query**: Instant PromQL queries (256MB, 30s)
- **prometheus-range-query**: Range queries over time (512MB, 60s)
- **prometheus-list-metrics**: Metric discovery (256MB, 30s)
- **prometheus-server-info**: Server configuration (256MB, 30s)

### AgentCore Gateway Integration
These functions are designed to integrate with **Bedrock AgentCore Gateway** through the **MCP (Model Context Protocol)** framework, providing:
- **Secure Authentication**: JWT-based authentication via Cognito
- **Scalable Architecture**: Multiple agents can share the same functions
- **Centralized Management**: Gateway handles connection pooling and caching
- **Clean Integration**: MCP provides standardized tool interface

### Deploy All Prometheus Functions

```bash
cd lambda/prometheus/
chmod +x deploy_all.sh
./deploy_all.sh
```

### Deploy Individual Prometheus Functions

```bash
cd lambda/prometheus/
# Deploy specific functions
./deploy_query.sh           # Instant queries
./deploy_range_query.sh     # Range queries
./deploy_list_metrics.sh    # Metric discovery
./deploy_server_info.sh     # Server information
```

### Test Prometheus Functions

**Test locally:**
```bash
cd lambda/prometheus/
python3 test_individual_functions.py
```

**Test deployed functions:**
```bash
cd lambda/prometheus/
# Test server info function
aws lambda invoke --function-name prometheus-server-info \
  --payload '{"body":{"workspace_id":"ws-12345678-abcd-1234-efgh-123456789012","region":"us-east-1"}}' \
  response.json

# Test query function
aws lambda invoke --function-name prometheus-query \
  --payload '{"body":{"workspace_id":"ws-12345678-abcd-1234-efgh-123456789012","query":"up","region":"us-east-1"}}' \
  response.json
```

### Lambda Best Practices Demonstrated

The Prometheus functions showcase Lambda best practices:
- **Single Responsibility**: Each function handles one specific operation
- **Right-sized Resources**: Memory and timeout optimized per function type
- **Shared Utilities**: Common code in `prometheus_utils.py` eliminates duplication
- **Independent Scaling**: Functions scale based on individual usage patterns
- **Granular Monitoring**: Separate CloudWatch metrics per operation
- **Enhanced Security**: Minimal IAM permissions per function

### Lambda Integration

The Lambda functions provide scalable functionality with:
- **Rate Limit Handling**: Automatic handling of service rate limits
- **Structured Responses**: Consistent JSON format for easy parsing
- **Error Recovery**: Comprehensive error handling and fallback mechanisms
- **CloudWatch Integration**: Full logging and monitoring capabilities
- **Backward Compatibility**: Integration layer maintains existing APIs

## MCP Lambda Servers ✅ **DEPLOYED**

The project includes 9 production-ready Lambda functions that replace local MCP (Model Context Protocol) processes, providing scalable microservices architecture for AgentCore Gateway integration.

### Deployed MCP Lambda Functions

1. **`mcp-core-server`** - Core MCP functionality and AWS context
2. **`mcp-aws-documentation-server`** - AWS documentation search and retrieval
3. **`mcp-aws-pricing-server`** - AWS pricing information and cost analysis
4. **`mcp-cloudwatch-server`** - CloudWatch logs, metrics, and monitoring
5. **`mcp-eks-server`** - EKS cluster management and Kubernetes operations
6. **`mcp-terraform-server`** - Terraform configuration and validation
7. **`mcp-git-repo-research-server`** - Git repository research and code analysis
8. **`mcp-frontend-server`** - Frontend development guidance and React docs
9. **`mcp-aws-location-server`** - AWS Location Service operations

### MCP Lambda Deployment

**Deploy all MCP servers:**
```bash
cd lambda/mcp-servers/
./deploy_all_mcp_servers.sh
```

**Test deployment:**
```bash
cd lambda/mcp-servers/
python3 test_mcp_lambdas.py
```

### MCP Lambda Features

- **✅ 100% Test Success Rate** - All 17 test cases passing
- **🏗️ Microservices Architecture** - Single responsibility per function
- **⚡ Optimized Performance** - 512MB memory, 300s timeout
- **🔐 Secure IAM Roles** - Least privilege permissions
- **📊 CloudWatch Integration** - Comprehensive logging and monitoring
- **🚀 Production Ready** - Error handling and retry mechanisms

### MCP Lambda Configuration

**Runtime Configuration:**
- **Runtime**: Python 3.11
- **Memory**: 512 MB (optimized for operations)
- **Timeout**: 300 seconds (5 minutes)
- **IAM Role**: `MCPLambdaExecutionRole`

**Environment Variables:**
- `MCP_SERVER_NAME` - Name of the MCP server
- `MCP_REGION` - AWS region for operations

### Benefits of Lambda MCP Servers

**Operational Benefits:**
- **No Local Process Management** - No more `uvx` processes to manage
- **Automatic Scaling** - Functions scale based on demand
- **Cost Optimization** - Pay only for actual usage
- **Better Security** - IAM-based permissions and isolated execution

**Integration Benefits:**
- **AgentCore Gateway Ready** - Direct integration with Bedrock AgentCore Gateway
- **MCP Protocol Compliance** - Standard MCP request/response format
- **JWT Authentication** - Secure token-based authentication
- **Centralized Monitoring** - All logs and metrics in CloudWatch

## Project Structure

### Complete File Organization
```
├── agent.py              # Main agent implementation and entry point
├── agent_runtime.py      # AgentCore Runtime wrapper for HTTP API
├── utils.py              # Utility functions for AWS services and config
├── requirements.txt      # Python dependencies
├── README.md            # Quick start guide (points to docs/)
├── docs/                   # Documentation directory
│   ├── README.md        # Main project documentation
│   ├── DEPLOYMENT.md    # This deployment guide
│   ├── AUTHENTICATION.md # Complete authentication flow documentation
│   ├── DEVELOPMENT.md   # Development guide and testing
│   └── STATUS.md        # System status and functionality reports
├── tests/               # Testing and debugging utilities
│   ├── check_permissions.py # AWS permission validation tool
│   ├── test_memory_save.py  # Memory functionality testing
│   ├── debug_memory.py      # Memory troubleshooting utilities
│   ├── test_runtime_local.py # Local runtime testing
│   └── test_simple_runtime.py # Basic runtime testing
├── lambda/              # AWS Lambda functions and deployment
│   └── websearch/           # Web search Lambda function
│       ├── lambda_websearch.py      # Web search Lambda function
│       ├── lambda_requirements.txt  # Lambda dependencies
│       ├── deploy_lambda.sh         # Lambda deployment script
│       ├── test_lambda_local.py     # Local Lambda testing
│       ├── lambda_integration.py    # Agent integration code
│       ├── lambda_package/          # Lambda deployment package (created during deployment)
│       ├── test_payload.json        # Test payloads
│       └── response.json            # Test responses (created during testing)
└── .kiro/               # Kiro IDE configuration and steering rules
    ├── hooks/           # Agent hooks for automated tasks
    └── steering/        # AI assistant guidance documents
```

## Development Workflow

### Local Development to Production Pipeline

1. **Develop locally** with `agent.py`
2. **Test runtime** with `tests/test_runtime_local.py`
3. **Deploy Lambda functions** with `lambda/websearch/deploy_lambda.sh` and `lambda/prometheus/deploy_all.sh`
4. **Deploy to AWS** with `deploy_runtime.py`
5. **Invoke remotely** with `invoke_runtime.py`

### Testing Strategy

**Local Testing:**
```bash
# Test AWS permissions
python3 tests/check_permissions.py

# Test memory functionality
python3 tests/test_memory_save.py

# Test runtime locally
python3 tests/test_runtime_local.py

# Test Lambda functions locally
cd lambda/websearch/ && python3 test_lambda_local.py
cd lambda/prometheus/ && python3 test_individual_functions.py
```

**Production Testing:**
```bash
# Test deployed runtime
python3 invoke_runtime.py test

# Test deployed Lambda functions
aws lambda invoke --function-name devops-agent-websearch \
  --payload '{"keywords": "test", "max_results": 1}' response.json

aws lambda invoke --function-name prometheus-server-info \
  --payload '{"body":{"workspace_id":"ws-test","region":"us-east-1"}}' response.json
```