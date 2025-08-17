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
├── check_permissions.py # AWS permission validation tool
├── test_memory_save.py  # Memory functionality testing
├── debug_memory.py      # Memory troubleshooting utilities
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
- Interactive conversation loop
- Memory resource creation and management

### utils.py
- AWS service utility functions
- SSM Parameter Store operations (get/put/delete)
- Configuration file readers (JSON/YAML)
- AWS account/region helpers
- Cognito client utilities

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

### AWS Integration
- Region configuration via environment variables
- Boto3 session management
- Service-specific client initialization

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