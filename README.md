# AWS DevOps Bot

An intelligent AWS DevOps assistant built with Amazon Bedrock and AgentCore Memory. The bot provides expert guidance on AWS infrastructure, operations, and DevOps best practices while maintaining conversation context through persistent memory.

## Features

- **AWS Expertise**: Specialized knowledge of AWS services, infrastructure, and DevOps practices
- **Memory Integration**: Uses Amazon Bedrock AgentCore Memory to remember user preferences and conversation history
- **Web Search**: Real-time web search capability for current information using DuckDuckGo
- **Conversational AI**: Powered by Claude Sonnet 4 with optimized temperature settings for technical accuracy

## Prerequisites

- Python 3.10+
- AWS CLI configured with appropriate credentials
- Access to Amazon Bedrock and AgentCore Memory services
- AWS region set to `us-east-1` (default)
- Required Python packages: `strands-agents`, `boto3`, `bedrock-agentcore`, `ddgs`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd aws-devops-bot
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

## Usage

### Running the Agent

Start the interactive conversation:
```bash
python3 agent.py
```

### Testing and Debugging

**Check AWS permissions and service access:**
```bash
python3 check_permissions.py
```
Validates AWS credentials, SSM, Bedrock, and AgentCore Memory permissions.

**Test memory functionality:**
```bash
python3 test_memory_save.py
```
Verifies memory creation, event saving, and retrieval capabilities.

**Debug memory issues:**
```bash
python3 debug_memory.py
```
Advanced troubleshooting for memory resource problems and SSM parameter validation.

## Configuration

### Core Settings
- **Model**: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- **Temperature**: 0.3 (optimized for technical accuracy and consistent responses)
- **Memory Expiry**: 90 days
- **Region**: us-east-1
- **Actor ID**: `devops_001` (used for memory namespace organization)

### Memory Management
Memory ID is automatically stored in SSM Parameter Store at:
```
/app/devopsagent/agentcore/memory_id
```

## Architecture

### Core Components

- **agent.py**: Main application entry point with agent configuration
- **utils.py**: AWS service utilities and configuration helpers
- **Memory Hooks**: DevOpsAgentMemoryHooks for conversation persistence
- **Web Search**: DuckDuckGo integration for real-time information

### AWS Services Used

- **Amazon Bedrock**: LLM inference and model hosting
- **Amazon Bedrock AgentCore Memory**: Conversation persistence
- **SSM Parameter Store**: Configuration storage
- **STS**: Identity and credential management

## Target Users

DevOps engineers, cloud architects, and AWS practitioners seeking intelligent assistance with:
- AWS infrastructure management
- DevOps workflow optimization
- Troubleshooting AWS services
- Best practices guidance
- Technical decision support

## Error Handling

The bot includes comprehensive error handling with:
- Graceful degradation when memory service is unavailable
- Detailed logging and debugging support
- User-friendly error messages
- Automatic fallback mechanisms

## Development

### Project Structure
```
├── agent.py              # Main agent implementation
├── utils.py              # AWS utility functions
├── requirements.txt      # Python dependencies
├── check_permissions.py  # AWS permission checker
├── test_memory_save.py   # Memory functionality tests
├── debug_memory.py       # Memory troubleshooting
└── .kiro/               # IDE configuration
```

### Memory Patterns
- **Namespaces**: 
  - `agent/devops/{actorId}/preferences` - User preferences and behavior
  - `agent/devops/{actorId}/semantic` - Conversation facts and context
- **Event-driven memory updates**: Automatic saving after each interaction
- **Context retrieval**: Relevant memories retrieved before query processing
- **Automatic interaction persistence**: All conversations stored for 90 days

## Key Features in Detail

### Intelligent Memory System
- **Automatic Context Retrieval**: Relevant past conversations are retrieved before processing new queries
- **Dual Strategy Storage**: Separate namespaces for user preferences and semantic conversation facts
- **Graceful Degradation**: Bot continues to function even if memory service is unavailable
- **Session Management**: Each conversation session is tracked with unique identifiers

### Web Search Integration
- **Real-time Information**: DuckDuckGo search for current AWS updates and information
- **Rate Limit Handling**: Automatic handling of search API rate limits
- **Fallback Mechanisms**: Graceful error handling for search failures

### AWS Service Integration
- **SSM Parameter Store**: Persistent storage for memory IDs and configuration
- **Multi-service Support**: Bedrock, AgentCore Memory, STS integration
- **Region Awareness**: Automatic region detection and configuration

## Troubleshooting

### Common Issues

1. **Permission Errors**: Run `python3 check_permissions.py` to validate AWS access
2. **Memory Issues**: Use `python3 debug_memory.py` for detailed diagnostics
3. **Region Mismatch**: Ensure AWS_DEFAULT_REGION is set to `us-east-1`
4. **Memory Creation**: If memory doesn't exist, the bot will automatically create it on first run

### Logs and Debugging

The application provides detailed logging for troubleshooting. Check console output for error messages and debugging information. Memory operations are logged at INFO level for monitoring.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests: `python3 check_permissions.py && python3 test_memory_save.py`
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request