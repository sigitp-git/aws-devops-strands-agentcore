# Project Structure

## Root Directory Layout
```
├── agent.py              # Main agent implementation and entry point
├── utils.py              # Utility functions for AWS services and config
├── requirements.txt      # Python dependencies
├── README.md            # Quick start guide (points to docs/)
├── docs/                   # Documentation directory
├── LICENSE              # MIT License file
├── .gitignore           # Git exclusions (Python, AWS, IDE files)
│   ├── README.md        # Main project documentation
│   ├── DEPLOYMENT.md    # Complete deployment guide
│   ├── AUTHENTICATION.md # Complete authentication flow documentation
│   ├── DEVELOPMENT.md   # Development guide and testing
│   ├── STATUS.md        # System status and functionality reports
│   └── notes.md         # Development notes and testing results
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

## Core Files

### agent.py
- Main application entry point
- Agent configuration with Bedrock model
- Memory hooks implementation (DevOpsAgentMemoryHooks)
- Web search tool integration
- OAuth2 authentication with Cognito
- MCP gateway integration with JWT tokens
- Interactive conversation loop
- Memory resource creation and management

### utils.py
- AWS service utility functions
- SSM Parameter Store operations (get/put/delete)
- Configuration file readers (JSON/YAML)
- AWS account/region helpers
- Cognito client utilities and secret retrieval

## Documentation Files

## Documentation Directory (`docs/`)

### docs/README.md
- Main project documentation and quick start guide
- Installation instructions and usage examples
- Architecture overview and key features

### docs/DEPLOYMENT.md
- Complete deployment guide for all modes (local CLI, cloud runtime, Lambda)
- AgentCore Runtime containerized deployment
- Lambda web search function deployment
- Testing strategies and troubleshooting

### docs/AUTHENTICATION.md
- Complete OAuth2 Client Credentials flow documentation
- Visual authentication flow diagram with Cognito
- Parameter exchange details and security considerations
- Troubleshooting guide and configuration requirements

### docs/DEVELOPMENT.md
- Development setup and technology stack
- Testing suite and debugging utilities
- Memory system implementation and patterns
- Kiro IDE integration and automation
- Model temperature configuration and best practices
- Contributing guidelines and code standards

### docs/STATUS.md
- Comprehensive system status and functionality reports
- All test results and performance metrics
- Production readiness confirmation
- Current deployment status and success metrics

### docs/notes.md
- Development notes and testing results
- Memory functionality verification with real conversation examples
- Test execution logs and outcomes
- Cross-session memory persistence demonstrations

## Testing and Debug Files

## Testing Directory (`tests/`)

### tests/check_permissions.py
- Comprehensive AWS permission checker
- Validates credentials, SSM, Bedrock, and AgentCore access
- Provides detailed error reporting and remediation steps

### tests/test_memory_save.py
- Tests AgentCore Memory functionality
- Verifies event creation and retrieval
- Validates memory persistence

### tests/debug_memory.py
- Advanced memory troubleshooting
- Memory resource investigation
- SSM parameter validation
- Memory creation capability testing

### tests/test_runtime_local.py
- Local AgentCore Runtime testing
- Endpoint validation and performance testing
- Comprehensive test suite before deployment

### tests/test_simple_runtime.py
- Basic BedrockAgentCoreApp functionality testing
- Simple echo server for isolating issues
- Minimal runtime validation
- SSM parameter validation
- Memory creation capability testing

## Lambda Directory

### lambda/websearch/
The websearch subdirectory contains all web search Lambda function components:

### lambda/websearch/lambda_websearch.py
- AWS Lambda function for web search functionality
- DuckDuckGo search integration with DDGS library
- Comprehensive error handling and rate limit management
- Structured JSON response format

### lambda/websearch/lambda_requirements.txt
- Lambda-specific Python dependencies
- DuckDuckGo search library and supporting packages
- Optimized for AWS Lambda runtime environment

### lambda/websearch/deploy_lambda.sh
- Automated Lambda deployment script
- Package creation and dependency installation
- IAM role creation and function deployment
- Automated testing and validation

### lambda/websearch/test_lambda_local.py
- Local Lambda function testing without AWS deployment
- Multiple test scenarios including error cases
- Mock context object for Lambda runtime simulation

### lambda/websearch/lambda_integration.py
- Integration code for connecting Lambda with main agent
- AWS Lambda invocation utilities
- Response parsing and error handling

### lambda/websearch/lambda_package/
- Deployment package directory (created during deployment)
- Contains Lambda function code and dependencies
- Automatically cleaned up after deployment

## Kiro IDE Configuration

### .kiro/hooks/
- **code-quality-analyzer.kiro.hook**: Automated code quality analysis on file changes
- **docs-sync-hook.kiro.hook**: Documentation synchronization automation

### .kiro/steering/
- **product.md**: Product overview and core features
- **structure.md**: Project structure and file organization
- **tech.md**: Technology stack and configuration details

## Configuration Patterns

### Memory Management
- Memory ID stored in SSM: `/app/devopsagent/agentcore/memory_id`
- Automatic memory resource discovery and creation
- Graceful fallback when memory unavailable

### Authentication Configuration
- Cognito authentication parameters in SSM Parameter Store
- OAuth2 Client Credentials flow implementation
- JWT token management and refresh
- MCP gateway integration with secure authentication

### AWS Integration
- Region configuration via environment variables
- Boto3 session management
- Service-specific client initialization
- Cognito User Pool and gateway integration

### Error Handling
- Comprehensive exception handling
- Logging with appropriate levels
- User-friendly error messages
- Graceful degradation strategies

## Development Conventions

### Code Organization
- Single-responsibility utility functions
- Clear separation of concerns
- Comprehensive error handling
- Detailed logging and debugging support

### Memory Patterns
- Namespace structure: `agent/devops/{actorId}/{strategy}`
- Event-driven memory updates
- Context retrieval before query processing
- Automatic interaction persistence