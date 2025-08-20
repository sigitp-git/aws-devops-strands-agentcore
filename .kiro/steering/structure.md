# Project Structure

## Root Directory Layout
```
├── agent.py              # Main agent implementation and entry point
├── utils.py              # Utility functions for AWS services and config
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation and setup guide
├── LICENSE              # MIT License file
├── .gitignore           # Git exclusions (Python, AWS, IDE files)
├── notes.md             # Development notes and testing results
├── model_temperature.md # Documentation on model temperature settings
├── cognito_authentication_documentation.md # Complete authentication flow documentation
├── FUNCTIONALITY_STATUS.md # Comprehensive system status report
├── DOCUMENTATION_STATUS.md # Documentation completeness tracking
├── check_permissions.py # AWS permission validation tool
├── test_memory_save.py  # Memory functionality testing
├── debug_memory.py      # Memory troubleshooting utilities
├── lambda/              # AWS Lambda functions and deployment
│   ├── lambda_websearch.py      # Web search Lambda function
│   ├── lambda_requirements.txt  # Lambda dependencies
│   ├── deploy_lambda.sh         # Lambda deployment script
│   ├── test_lambda_local.py     # Local Lambda testing
│   ├── lambda_integration.py    # Agent integration code
│   ├── lambda_package/          # Lambda deployment package
│   ├── test_payload.json        # Test payloads
│   └── response.json            # Test responses
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

### README.md
- Comprehensive project documentation
- Installation and setup instructions
- Usage examples and troubleshooting
- Architecture overview and features

### LICENSE
- MIT License for open source distribution
- Copyright and usage permissions

### notes.md
- Development notes and testing results
- Memory functionality verification with real conversation examples
- Test execution logs and outcomes
- Cross-session memory persistence demonstrations

### model_temperature.md
- Temperature configuration documentation
- Best practices for different use cases
- Technical accuracy optimization guide

### cognito_authentication_documentation.md
- Complete OAuth2 Client Credentials flow documentation
- Visual authentication flow diagram
- Parameter exchange details and security considerations
- Troubleshooting guide and configuration requirements

### FUNCTIONALITY_STATUS.md
- Comprehensive system status report
- All functionality verification results
- Performance characteristics and testing results

### DOCUMENTATION_STATUS.md
- Documentation completeness tracking
- Update history and recent changes
- File organization and maintenance status

## Testing and Debug Files

### check_permissions.py
- Comprehensive AWS permission checker
- Validates credentials, SSM, Bedrock, and AgentCore access
- Provides detailed error reporting and remediation steps

### test_memory_save.py
- Tests AgentCore Memory functionality
- Verifies event creation and retrieval
- Validates memory persistence

### debug_memory.py
- Advanced memory troubleshooting
- Memory resource investigation
- SSM parameter validation
- Memory creation capability testing

## Lambda Directory

### lambda_websearch.py
- AWS Lambda function for web search functionality
- DuckDuckGo search integration with DDGS library
- Comprehensive error handling and rate limit management
- Structured JSON response format

### lambda_requirements.txt
- Lambda-specific Python dependencies
- DuckDuckGo search library and supporting packages
- Optimized for AWS Lambda runtime environment

### deploy_lambda.sh
- Automated Lambda deployment script
- Package creation and dependency installation
- IAM role creation and function deployment
- Automated testing and validation

### test_lambda_local.py
- Local Lambda function testing without AWS deployment
- Multiple test scenarios including error cases
- Mock context object for Lambda runtime simulation

### lambda_integration.py
- Integration code for connecting Lambda with main agent
- AWS Lambda invocation utilities
- Response parsing and error handling

### lambda_package/
- Deployment package directory
- Contains Lambda function code and dependencies
- Generated during deployment process

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