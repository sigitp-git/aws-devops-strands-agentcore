# AWS DevOps Agent

An intelligent AWS DevOps assistant built with Amazon Bedrock and AgentCore Memory. The agent provides expert guidance on AWS infrastructure, operations, and DevOps best practices while maintaining conversation context through persistent memory.

## Core Features

- **AWS Expertise**: Specialized knowledge of AWS services, infrastructure, and DevOps practices
- **Memory Integration**: Uses Amazon Bedrock AgentCore Memory to remember user preferences and conversation history
- **Secure Authentication**: OAuth2 Client Credentials flow with Amazon Cognito for secure service access
- **MCP Gateway Integration**: Bedrock AgentCore Gateway with JWT authentication for advanced tool access
- **Web Search**: Real-time web search capability for current information using DuckDuckGo
- **Lambda Integration**: Lambda functions will be integrated with Bedrock AgentCore Gateway, they'll be accessible through the MCP (Model Context Protocol) framework, which provides a much cleaner and more scalable integration pattern
- **Conversational AI**: Powered by Claude Sonnet 4 with optimized temperature settings for technical accuracy

## Target Users

DevOps engineers, cloud architects, and AWS practitioners seeking intelligent assistance with:
- AWS infrastructure management
- DevOps workflow optimization  
- Troubleshooting AWS services
- Best practices guidance
- Technical decision support

## Key Capabilities

- Answers AWS technical questions with high accuracy
- Remembers user preferences and past interactions
- Secure authentication with Amazon Cognito and JWT tokens
- Advanced tool access through MCP gateway integration
- Provides up-to-date information through web search
- Scalable Lambda-based microservices architecture
  - Web search functionality with DuckDuckGo integration
  - Prometheus monitoring with specialized functions following Lambda best practices
- Maintains professional, helpful tone
- Focuses on actionable, practical advice
- Automated code quality analysis through Kiro IDE hooks
- Comprehensive testing and debugging utilities
- Production-ready Lambda deployment with error handling
- Complete authentication flow documentation with diagrams
- Demonstrates Lambda best practices with real-world microservices implementation

## Repository Information

- **GitHub**: https://github.com/sigitp-git/aws-devops-strands-agentcore
- **License**: MIT License
- **Language**: Python 3.8+
- **Platform**: Cross-platform (Linux, macOS, Windows)