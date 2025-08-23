# Technology Stack

## Core Framework
- **Strands Agents**: Primary agent framework for building conversational AI
- **Amazon Bedrock**: LLM service using Claude Sonnet 4 model
- **Amazon Bedrock AgentCore Memory**: Persistent memory system for conversation context

## Dependencies
- **boto3/botocore**: AWS SDK for Python (>=1.40.8)
- **bedrock-agentcore**: Memory client and toolkit (>=0.1.2)
- **ddgs**: DuckDuckGo search integration
- **aws-opentelemetry-distro**: Observability and tracing (~0.10.1)

## AWS Services
- **Bedrock**: LLM inference and model hosting
- **Amazon Bedrock AgentCore Memory**: Conversation persistence and retrieval
- **Amazon Bedrock AgentCore Gateway**: MCP tool integration with secure authentication
- **Amazon Cognito**: User Pool for OAuth2 authentication and JWT token management
- **SSM Parameter Store**: Configuration and authentication parameter storage
- **STS**: Identity and credential management
- **AWS Lambda**: Microservices architecture with specialized functions
  - Web search function with DuckDuckGo integration
  - Prometheus monitoring functions (4 specialized functions following Lambda best practices)
- **IAM**: Lambda execution roles and gateway permissions with least privilege
- **CloudWatch**: Lambda function logging and monitoring with granular metrics

## Configuration
- **Region**: us-east-1 (default)
- **Model**: us.anthropic.claude-sonnet-4-20250514-v1:0
- **Temperature**: 0.3 (optimized for technical accuracy)
- **Memory Expiry**: 90 days
- **Authentication**: OAuth2 Client Credentials Grant with Cognito
- **Gateway**: Bedrock AgentCore Gateway with JWT authentication

## Common Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set AWS region
export AWS_DEFAULT_REGION=us-east-1
```

### Testing and Debugging
```bash
# Check AWS permissions
python3 tests/check_permissions.py

# Test memory functionality
python3 tests/test_memory_save.py

# Debug memory issues
python3 tests/debug_memory.py

# Run the agent
python3 agent.py

# Deploy Lambda functions
cd lambda/websearch/ && ./deploy_lambda.sh
cd lambda/prometheus/ && ./deploy_all.sh

# Test Lambda functions locally
cd lambda/websearch/ && python3 test_lambda_local.py
cd lambda/prometheus/ && python3 test_parameter_handling.py
```

### AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Verify identity
aws sts get-caller-identity
```

## Kiro IDE Integration

### Agent Hooks
- **Code Quality Analyzer**: Monitors source code files for changes and provides improvement suggestions
- **Documentation Sync**: Keeps documentation up to date with code changes
- **File Patterns**: Supports Python, JavaScript, TypeScript, Java, C++, and more
- **Debounce**: Short delay to batch rapid file changes

### Steering Rules
- **Product Guidelines**: Core features and capabilities documentation
- **Structure Guidelines**: Project organization and file structure
- **Technology Guidelines**: Stack details and configuration

## Development Notes
- Memory hooks are automatically registered if memory is available
- Graceful degradation when memory service is unavailable
- Comprehensive error handling and logging
- SSM parameter store used for persistent configuration
- Automated code quality analysis on file changes
- MIT License for open source distribution
- Lambda functions follow microservices architecture and best practices
- Prometheus functions refactored for AgentCore Gateway MCP integration
- Simplified parameter handling with direct workspace_id usage
- Enhanced security validation and dangerous pattern detection
- Shared utilities pattern eliminates code duplication while maintaining function separation
- Gateway configuration schema defined for MCP tool integration