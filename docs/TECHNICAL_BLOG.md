# Build Scalable Agent with Strands and Amazon Bedrock AgentCore

Building intelligent conversational agents that can maintain context, integrate with external tools, and scale to production workloads requires careful architectural decisions. This blog explores how we built a production-ready AWS DevOps agent using Strands framework and Amazon Bedrock AgentCore, demonstrating key patterns for scalable agent development.

## Architecture Overview

Our agent leverages a modern serverless architecture built on three core pillars:

**1. Conversational Intelligence**: Powered by Claude Sonnet 4 through Amazon Bedrock with temperature optimization (0.3) for technical accuracy.

**2. Persistent Memory**: Amazon Bedrock AgentCore Memory provides cross-session context retention with 90-day persistence and semantic search capabilities.

**3. Tool Integration**: MCP (Model Context Protocol) through Bedrock AgentCore Gateway enables secure, scalable tool access without direct Lambda integration.

## Key Design Decisions

### Memory-First Architecture

Traditional chatbots lose context between sessions. We implemented persistent memory as a first-class citizen:

```python
# Memory hooks automatically capture interactions
class DevOpsAgentMemoryHooks(MemoryHooks):
    def on_before_query(self, query: str, context: dict) -> dict:
        # Retrieve relevant context before processing
        return self.memory_client.retrieve_context(query)
    
    def on_after_response(self, query: str, response: str, context: dict):
        # Persist interaction for future sessions
        self.memory_client.create_event(query, response, context)
```

This approach enables the agent to remember user preferences, past conversations, and build contextual understanding over time.

### MCP Gateway Integration Pattern

Instead of direct Lambda integration, we adopted MCP through Bedrock AgentCore Gateway:

```python
# Clean separation: Agent focuses on conversation, tools handle operations
agent = BedrockAgentCoreApp(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    memory_hooks=DevOpsAgentMemoryHooks(),
    gateway_config=gateway_config  # MCP tools via gateway
)
```

**Benefits:**
- **Decoupled Architecture**: Lambda functions operate independently
- **Secure Authentication**: JWT tokens and OAuth2 Client Credentials flow
- **Scalable Tool Access**: New tools added without agent code changes
- **Production Ready**: Built-in monitoring and error handling

### Microservices Lambda Architecture

We demonstrate Lambda best practices with specialized functions:

```
lambda/
├── websearch/           # DuckDuckGo search integration
├── prometheus/          # Monitoring functions (4 specialized)
│   ├── lambda_query.py         # Instant queries (256MB, 30s)
│   ├── lambda_range_query.py   # Time series (512MB, 60s)
│   ├── lambda_list_metrics.py  # Discovery (256MB, 30s)
│   └── lambda_server_info.py   # Config (256MB, 30s)
└── eks/                # Kubernetes management functions
```

Each function follows single responsibility principle with right-sized resources and independent scaling.

## Implementation Highlights

### Multi-Modal Deployment

The agent supports four deployment modes:

**Local CLI** (`agent.py`): Interactive development with full feature access
**Local Runtime** (`agent_runtime.py`): HTTP API for testing production behavior
**Streamlit Web UI** (`streamlit/streamlit_app.py`): Modern web interface for end users
**AgentCore Runtime**: Containerized production deployment with auto-scaling

### Authentication & Security

OAuth2 Client Credentials flow with Amazon Cognito provides secure service access:

```python
# Secure token exchange for MCP gateway access
cognito_client = utils.get_cognito_client()
token_response = cognito_client.initiate_auth(
    AuthFlow='CLIENT_CREDENTIALS',
    AuthParameters={'SCOPE': 'gateway/invoke'}
)
```

### Configuration Management

SSM Parameter Store centralizes configuration with automatic discovery:

```python
# Self-configuring memory resources
memory_id = utils.get_ssm_parameter('/app/devopsagent/agentcore/memory_id')
if not memory_id:
    memory_resource = memory_client.create_memory_resource()
    utils.put_ssm_parameter('/app/devopsagent/agentcore/memory_id', memory_resource.id)
```

### Streamlit Web Interface

A modern web UI provides user-friendly access to the agent through Streamlit:

```python
class StreamlitAgentInterface:
    def invoke_agent(self, prompt, session_id=None):
        # Direct integration with AgentCore Runtime
        response = self.client.invoke_agent_runtime(
            agentRuntimeArn=agent_runtime_arn,
            runtimeSessionId=session_id,
            payload=json.dumps(payload).encode('utf-8')
        )
        return json.loads(response['response'].read())
```

**Key Features:**
- **Real-time Chat Interface**: Interactive conversation with persistent sessions
- **AWS-Themed Styling**: Professional UI with custom CSS and responsive design
- **Example Prompts**: Pre-built queries for common DevOps scenarios
- **Session Management**: New session creation and chat history clearing
- **Mobile-Friendly**: Responsive design for various screen sizes
- **Direct Runtime Integration**: No additional API layer required

## Production Deployment

### Containerized Runtime

ARM64-optimized Docker container deployed to AgentCore Runtime:

```dockerfile
FROM public.ecr.aws/lambda/python:3.11-arm64
COPY requirements.txt agent_runtime.py utils.py ./
RUN pip install -r requirements.txt
CMD ["agent_runtime.lambda_handler"]
```

### Performance Characteristics

- **Basic Queries**: 4-5 seconds response time
- **Web Search**: 30-60 seconds (external API dependent)
- **Memory Retrieval**: <1 second with semantic search
- **Cold Start**: Optimized with shared utilities pattern

### Monitoring & Observability

Comprehensive logging and monitoring through CloudWatch:

```python
# Structured logging for production debugging
logger.info("Processing query", extra={
    "session_id": session_id,
    "model": model_id,
    "tools_used": tools_used,
    "response_time": response_time
})
```

## Lessons Learned

### 1. Memory as Infrastructure
Treating memory as infrastructure rather than an afterthought enables sophisticated conversational experiences. The agent learns user preferences and maintains context across sessions.

### 2. Gateway Pattern for Tools
MCP through AgentCore Gateway provides cleaner integration than direct Lambda invocation. This pattern scales better and provides better security isolation.

### 3. Right-Sized Functions
Breaking monolithic Lambda functions into specialized microservices (query vs. range query vs. metrics) improves performance and cost efficiency.

### 4. Configuration Automation
Self-configuring resources through SSM Parameter Store reduces deployment complexity and enables environment-specific configurations.

## Results

The production deployment demonstrates:

- ✅ **Cross-session memory** with 100% persistence success rate
- ✅ **Secure authentication** with JWT tokens and OAuth2 flow
- ✅ **Scalable tool integration** through MCP gateway
- ✅ **Production performance** with 4-5s response times
- ✅ **Microservices architecture** with specialized Lambda functions
- ✅ **Modern web interface** with Streamlit providing user-friendly access
- ✅ **Multi-modal deployment** supporting CLI, web UI, and production runtime

## Getting Started

The complete implementation is available on GitHub with comprehensive documentation, deployment scripts, and testing utilities. The project demonstrates production-ready patterns for building scalable conversational agents with persistent memory and secure tool integration.

**Repository**: [aws-devops-strands-agentcore](https://github.com/sigitp-git/aws-devops-strands-agentcore)

This architecture provides a solid foundation for building sophisticated conversational agents that can maintain context, integrate with external services, and scale to production workloads while following AWS best practices for security and performance.