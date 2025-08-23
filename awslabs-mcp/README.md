# MCP Server Configuration

This directory contains the Model Context Protocol (MCP) server configuration for the AWS DevOps Agent.

## Files

- **`mcp.json`** - Main MCP server configuration with 16+ AWS services
- **`.env.example`** - Template for environment variables
- **`.env`** - Your actual environment variables (not committed to git)
- **`deploy_mcp_lambdas.py`** - Deploy MCP servers as AWS Lambda functions
- **`deploy.sh`** - Deployment script for Lambda functions

## Quick Setup

1. **Copy environment template:**
   ```bash
   cp awslabs-mcp/.env.example awslabs-mcp/.env
   ```

2. **Edit environment variables:**
   ```bash
   # Edit .env with your actual values
   nano awslabs-mcp/.env
   ```

3. **Upload configuration to runtime (for production):**
   ```bash
   python3 agent.py upload-mcp-config
   ```

4. **Deploy MCP servers as Lambda functions (optional):**
   ```bash
   cd awslabs-mcp
   ./deploy.sh
   ```

## Environment Variables

Required environment variables (see `.env.example`):

```bash
# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_personal_access_token

# AWS Configuration  
AWS_PROFILE=your_aws_profile_name

# Prometheus Configuration
PROMETHEUS_WORKSPACE_URL=https://aps-workspaces.us-east-1.amazonaws.com/workspaces/your-workspace-id
```

## Available MCP Servers

The configuration includes 16 MCP servers providing access to:

### AWS Services
- **Core MCP Server** - Core AWS functionality
- **AWS Pricing** - Cost calculation and pricing information
- **AWS Documentation** - Search and read AWS documentation
- **AWS CloudFormation** - Infrastructure as code management
- **AWS CloudWatch** - Monitoring and logging
- **AWS CloudWatch Application Signals** - Application monitoring
- **AWS EKS** - Kubernetes cluster management
- **AWS Location Services** - Geospatial services
- **AWS Terraform** - Infrastructure automation
- **AWS Cloud Control API** - Resource management

### Development Tools
- **Frontend MCP Server** - Web application development
- **Git Repository Research** - Repository analysis and search
- **AWS Diagram Generator** - Architecture diagrams
- **Prometheus** - Metrics and monitoring
- **GitHub Integration** - Repository management

### Knowledge & Documentation
- **AWS Knowledge Base** - Expert AWS guidance

## Runtime vs Local Environments

### Local Development (`python3 agent.py`)
- ✅ Loads configuration from `awslabs-mcp/mcp.json`
- ✅ Starts all 16 MCP servers locally
- ✅ Full development capabilities
- ✅ Direct access to environment variables

### Production Runtime (`python3 invoke_runtime.py`)
- ✅ Loads configuration from AWS Systems Manager Parameter Store
- ✅ Access to MCP tools through Bedrock AgentCore Gateway
- ✅ Production-ready deployment
- ⚠️ Requires configuration upload: `python3 agent.py upload-mcp-config`

## Configuration Management

### Upload to Runtime
```bash
# Upload MCP configuration to SSM for runtime access
python3 agent.py upload-mcp-config
```

### Verify Configuration
```bash
# Test local configuration
python3 agent.py

# Test runtime configuration  
python3 invoke_runtime.py
```

## Troubleshooting

### Missing Environment Variables
- Ensure `.env` file exists and contains all required variables
- Check that environment variables are properly formatted
- Verify AWS credentials and permissions

### Runtime Configuration Issues
- Run `python3 agent.py upload-mcp-config` to sync configuration
- Check AWS Systems Manager Parameter Store permissions
- Verify the runtime has access to required SSM parameters

### MCP Server Startup Failures
- Check that `uvx` and `uv` are installed
- Verify network connectivity for Docker-based servers
- Review server-specific requirements in `mcp.json`

## Lambda Deployment

### Deploy MCP Servers as Lambda Functions
```bash
cd awslabs-mcp
./deploy.sh
```

This will:
- ✅ Analyze MCP configuration for Lambda-deployable servers
- ✅ Create IAM execution roles with appropriate permissions
- ✅ Generate Lambda function code for each server
- ✅ Deploy functions with optimized resource allocation
- ✅ Save deployment information to SSM Parameter Store

### Lambda Integration Benefits
- **Scalability** - Automatic scaling based on demand
- **Cost Efficiency** - Pay only for actual usage
- **Gateway Integration** - Seamless integration with Bedrock AgentCore Gateway
- **Security** - Isolated execution environments with least-privilege permissions

### The Architecture Reality
The AgentCore Runtime is designed to work with:
- Gateway MCP Tools - Tools deployed and managed by AWS through the gateway
- Built-in Tools - Tools that are part of the container image
- Lambda Functions - MCP servers deployed as serverless functions
It's not designed to start external processes or run local MCP servers.