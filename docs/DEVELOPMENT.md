# AWS DevOps Agent - Development Guide

This guide covers development setup, testing, debugging, and technical implementation details for the AWS DevOps Agent.

## Development Setup

### Prerequisites

- Python 3.8+
- AWS CLI configured with appropriate credentials
- Access to Amazon Bedrock and AgentCore Memory services
- AWS region set to `us-east-1` (default)
- Docker with buildx support ✅ **INSTALLED AND CONFIGURED**

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sigitp-git/aws-devops-strands-agentcore.git
cd aws-devops-strands-agentcore
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials:
```bash
aws configure
# or set environment variables
export AWS_DEFAULT_REGION=us-east-1
```

## Technology Stack

### Core Framework
- **Strands Agents**: Primary agent framework for building conversational AI
- **Amazon Bedrock**: LLM service using Claude Sonnet 4 model
- **Amazon Bedrock AgentCore Memory**: Persistent memory system for conversation context

### Dependencies
- **boto3/botocore**: AWS SDK for Python (>=1.40.8)
- **bedrock-agentcore**: Memory client and toolkit (>=0.1.2)
- **ddgs**: DuckDuckGo search integration
- **aws-opentelemetry-distro**: Observability and tracing (~0.10.1)

### AWS Services
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

### Core Settings
- **Model**: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- **Temperature**: 0.3 (optimized for technical accuracy and consistent responses)
- **Memory Expiry**: 90 days
- **Region**: us-east-1
- **Actor ID**: `devops_001` (used for memory namespace organization)

### Model Temperature Configuration

The agent uses temperature 0.3 for optimal technical accuracy:

#### Temperature Scale (0.0 - 1.0)
- **Low Temperature (0.0 - 0.3)**: More deterministic and predictable responses
  - Less creative but more focused and consistent
  - Better for: Factual questions, code generation, structured tasks
- **Medium Temperature (0.4 - 0.7)**: Balanced between creativity and consistency
  - Good for: General conversations, explanations, most use cases
- **High Temperature (0.8 - 1.0+)**: More creative and varied responses
  - Less predictable but more diverse
  - Better for: Creative writing, brainstorming, generating multiple ideas

#### Benefits of Temperature 0.3 for AWS DevOps Agent
1. **Consistent Structure** - Response follows clear, organized format
2. **Technical Accuracy** - Focuses on providing accurate AWS service information
3. **Professional Tone** - Maintains professional, helpful tone for technical guidance
4. **Reliable Information** - Less likely to generate inconsistent technical details

### Memory Management

Memory ID is automatically stored in SSM Parameter Store at:
```
/app/devopsagent/agentcore/memory_id
```

#### Memory Patterns
- **Enhanced Namespace Structure**: 
  - `agent/devops/{actorId}/preferences` - User preferences and behavioral patterns
  - `agent/devops/{actorId}/semantic` - Conversation facts and contextual information
- **Event-driven Memory Updates**: Automatic saving after each interaction with "ASSISTANT" role for memory compatibility
- **Semantic Context Retrieval**: Advanced semantic search retrieves relevant memories before query processing
- **Cross-Session Continuity**: Memory persists across different agent sessions for seamless user experience
- **Automatic Interaction Persistence**: All conversations stored for 90 days with intelligent preference weighting

#### Role Handling
**Important Technical Detail**: The agent maintains dual role handling:
- **Internal Role**: Uses "agent" role for conversation flow and user interaction
- **Memory Role**: Saves interactions with "ASSISTANT" role to comply with AgentCore Memory requirements
- **Supported Memory Roles**: AgentCore Memory only accepts "USER", "ASSISTANT", "TOOL", "OTHER"
- **Seamless Experience**: This dual handling is transparent to users while ensuring memory compatibility

## Testing and Debugging

### Automated Testing Suite

**Check AWS permissions and service access:**
```bash
python3 tests/check_permissions.py
```
Validates AWS credentials, SSM, Bedrock, and AgentCore Memory permissions.

**Test memory functionality:**
```bash
python3 tests/test_memory_save.py
```
Verifies memory creation, event saving, and retrieval capabilities.

**Debug memory issues:**
```bash
python3 tests/debug_memory.py
```
Advanced troubleshooting for memory resource problems and SSM parameter validation.

**Test AgentCore Runtime locally:**
```bash
python3 tests/test_runtime_local.py
```
Comprehensive testing of HTTP API endpoints before deployment.

**Test basic runtime functionality:**
```bash
python3 tests/test_simple_runtime.py
```
Basic BedrockAgentCoreApp functionality testing.

**Deploy to production:**
```bash
python3 deploy_runtime.py
```
Deploy to Amazon Bedrock AgentCore Runtime ✅ **COMPLETED**

**Test deployed agent:**
```bash
python3 invoke_runtime.py interactive
```
Interact with the production-deployed agent.

### Memory Testing Examples

#### Automated Testing
```bash
# Run the comprehensive memory test suite
python3 tests/test_memory_save.py

# Check AWS permissions for memory services
python3 tests/check_permissions.py

# Debug memory resource issues
python3 tests/debug_memory.py
```

#### Manual Memory Testing Workflow
1. **Set a Preference**: Tell the agent your favorite AWS service
2. **Exit and Restart**: Close the agent and start a new session  
3. **Test Recall**: Ask the agent about your preference
4. **Verify Context**: Check if the agent uses your preference in responses

#### Memory Verification Commands
```bash
# Check memory content directly
python3 -c "
import os
from bedrock_agentcore.memory import MemoryClient
from utils import get_ssm_parameter

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
memory_client = MemoryClient(region_name='us-east-1')
memory_id = get_ssm_parameter('/app/devopsagent/agentcore/memory_id')

# Check both memory namespaces
namespaces = [
    'agent/devops/devops_001/semantic',
    'agent/devops/devops_001/preferences'
]

for namespace in namespaces:
    memories = memory_client.retrieve_memories(
        memory_id=memory_id,
        namespace=namespace,
        query='favorite AWS service',
        top_k=3
    )
    print(f'{namespace}: {len(memories)} memories')
    for i, memory in enumerate(memories):
        content = memory.get('content', {}).get('text', '')[:100]
        print(f'  {i+1}. {content}...')
"
```

### Performance Characteristics

- **Startup Time**: ~2-3 seconds
- **Response Time**: 1-5 seconds depending on complexity
- **Memory Retrieval**: <1 second
- **Web Search**: 2-4 seconds
- **Error Recovery**: Graceful degradation

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

### Hook Configuration

#### Code Quality Analyzer Hook
```yaml
# .kiro/hooks/code-quality-analyzer.kiro.hook
name: "Code Quality Analyzer"
description: "Analyzes code changes and provides improvement suggestions"
trigger:
  type: "file_change"
  patterns: ["**/*.py", "**/*.js", "**/*.ts", "**/*.java", "**/*.cpp"]
  debounce: 2000
```

#### Documentation Sync Hook
```yaml
# .kiro/hooks/docs-sync-hook.kiro.hook
name: "Documentation Sync"
description: "Keeps documentation synchronized with code changes"
trigger:
  type: "file_change"
  patterns: ["**/*.py", "**/*.md", "requirements.txt"]
  debounce: 3000
```

## Error Handling and Troubleshooting

### Common Issues

1. **Permission Errors**: Run `python3 tests/check_permissions.py` to validate AWS access
2. **Memory Issues**: Use `python3 tests/debug_memory.py` for detailed diagnostics
3. **Region Mismatch**: Ensure AWS_DEFAULT_REGION is set to `us-east-1`
4. **Memory Creation**: If memory doesn't exist, the agent will automatically create it on first run

### Logs and Debugging

The application provides detailed logging for troubleshooting. Check console output for error messages and debugging information. Memory operations are logged at INFO level for monitoring.

### Graceful Degradation

The agent implements graceful degradation when services are unavailable:
- **Memory Service**: Agent continues without memory if service is unavailable
- **Web Search**: Falls back to knowledge base if search fails
- **MCP Gateway**: Core functionality continues without gateway features
- **Authentication**: Clear error messages guide troubleshooting

## Development Automation

### Automated Code Quality Analysis
- **Kiro IDE hooks** monitor file changes and provide improvement suggestions
- **Multi-language Support**: Code analysis supports Python, JavaScript, TypeScript, Java, C++, and more
- **Intelligent Debouncing**: Batches rapid file changes to avoid excessive processing

### Documentation Synchronization
- **Automatic Updates**: Documentation stays aligned with code changes
- **Cross-Reference Validation**: Ensures all internal links remain valid
- **Consistency Checks**: Maintains consistent terminology and structure

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests: `python3 tests/check_permissions.py && python3 tests/test_memory_save.py`
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards

- Follow PEP 8 for Python code style
- Include comprehensive error handling
- Add logging for debugging support
- Write tests for new functionality
- Update documentation for changes
- Maintain backward compatibility

### Testing Requirements

All contributions must pass:
- AWS permission validation tests
- Memory functionality tests
- Runtime integration tests
- Code quality analysis
- Documentation consistency checks

## Security Best Practices

### Authentication Security
- Short-lived JWT tokens (1 hour expiration)
- Dynamic client secret retrieval
- Encrypted parameter storage
- HTTPS-only communication

### Access Control
- IAM role-based permissions
- Least privilege principle
- Service-specific access controls
- Comprehensive audit logging

### Data Protection
- Memory data encrypted at rest
- Secure token handling
- No persistent credential storage
- Comprehensive error handling without data exposure

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.