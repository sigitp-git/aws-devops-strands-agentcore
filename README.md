# AWS DevOps Agent

An intelligent AWS DevOps assistant built with Amazon Bedrock and AgentCore Memory. The agent provides expert guidance on AWS infrastructure, operations, and DevOps best practices while maintaining conversation context through persistent memory.

## 📚 Documentation

- **[Quick Setup Guide](docs/SETUP.md)** - 5-minute setup instructions
- **[Complete Guide](docs/README.md)** - Installation, usage, and architecture
- **[Deployment Guide](docs/DEPLOYMENT.md)** - All deployment options (local, cloud, Lambda)
- **[Streamlit Frontend](docs/STREAMLIT_FRONTEND.md)** - Web UI for interactive chat experience
- **[IAM Policies Guide](iampolicies/README.md)** - Security policies and role configuration
- **[Authentication Guide](docs/AUTHENTICATION.md)** - OAuth2 flow and security configuration  
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup, testing, and technical implementation
- **[System Status](docs/STATUS.md)** - Current functionality and performance status

## ✨ Key Features

- **🧠 Intelligent Memory**: Cross-session persistence with semantic search and preference learning
- **🔐 Secure Authentication**: OAuth2 Client Credentials flow with Amazon Cognito and JWT tokens
- **🚀 Production Ready**: Successfully deployed to Amazon Bedrock AgentCore Runtime
- **🔍 Real-time Search**: DuckDuckGo integration with deployable Lambda function
- **🤖 Flexible Model Selection**: Choose from 5 Claude models (Sonnet 4, 3.7 Sonnet, 3.5 Sonnet v2, 3.5 Sonnet v1, 3.5 Haiku)
- **⚡ AWS Expertise**: Specialized knowledge powered by configurable Claude models (temperature 0.3)
- **🛠️ MCP Integration**: Advanced tool access through Bedrock AgentCore Gateway
- **🎯 Kiro IDE Integration**: Automated code quality analysis and documentation sync
- **📦 ARM64 Optimized**: Docker container built for optimal performance

## 🤖 Model Selection

Choose from multiple Claude models based on your needs:

### Available Models
- **Claude Sonnet 4** - Latest, most capable model (default)
- **Claude 3.7 Sonnet** - Enhanced reasoning capabilities  
- **Claude 3.5 Sonnet v2** - Balanced performance and speed
- **Claude 3.5 Sonnet v1** - Stable, proven performance
- **Claude 3.5 Haiku** - Fast and efficient for simple tasks

### Model Selection Options

**Standalone Model Selector:**
```bash
python3 select_model.py
```

**CLI Agent with Model Selection:**
```bash
python3 agent.py --select-model
```

**Streamlit Web UI:**
- Use the model selector in the sidebar under "🤖 Model Selection"
- Changes take effect immediately in the web interface

## 🚀 Quick Start

> 📖 **For detailed setup instructions, see the [Quick Setup Guide](docs/SETUP.md)**

### Prerequisites
- Python 3.8+, AWS CLI configured, Access to Amazon Bedrock
- Docker with buildx support (for deployment)
- AWS region: `us-east-1` (default)

### 5-Minute Setup
```bash
# 1. Clone and install
git clone https://github.com/sigitp-git/aws-devops-strands-agentcore.git
cd aws-devops-strands-agentcore
pip install -r requirements.txt

# 2. Create IAM roles
cd iampolicies && ./create-iam-roles.sh && cd ..

# 3. Deploy agent
python3 deploy_runtime.py

# 4. Launch web interface
./run_streamlit.sh
```

### Usage Options

**Web Interface (Recommended):**
```bash
# Launch Streamlit web interface
./run_streamlit.sh
# Access at http://localhost:8501
```

**Command Line Interface:**
```bash
# Interactive CLI mode
python3 agent.py

# Test deployed agent
python3 invoke_runtime.py
```

**Production Deployment:**
```bash
# Deploy to AgentCore Runtime
python3 deploy_runtime.py

# Local runtime server
python3 agent_runtime.py
```

### Testing
```bash
# Validate AWS permissions
python3 tests/check_permissions.py

# Test memory functionality  
python3 tests/test_memory_save.py

# Test runtime deployment
python3 tests/test_runtime_local.py
```

## 🏗️ Architecture

### Core Components
- **Claude Sonnet 4**: AI model (temperature 0.3 for technical accuracy)
- **AgentCore Memory**: 90-day persistent memory with semantic search
- **Cognito Authentication**: OAuth2 JWT tokens for secure access
- **MCP Gateway**: Advanced tool integration
- **Lambda Functions**: Scalable microservices architecture with AgentCore Gateway integration
  - Web search capability with DuckDuckGo integration
  - Prometheus monitoring with 4 specialized functions following Lambda best practices
  - MCP (Model Context Protocol) framework integration for clean tool access

### AWS Services
Amazon Bedrock • AgentCore Memory • Cognito • SSM Parameter Store • Lambda • IAM • CloudWatch

## 📊 Current Status

✅ **PRODUCTION DEPLOYED** - Successfully deployed to Amazon Bedrock AgentCore Runtime  
✅ **Runtime ARN** - `arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/devops_agent-*`  
✅ **AWS Integration** - 25 Claude models, all permissions verified  
✅ **Memory System** - Cross-session persistence with 100% success rate  
✅ **Authentication** - OAuth2 JWT tokens with secure gateway access  
✅ **Performance** - 2-3s startup, 1-5s response time, <1s memory retrieval  

## 🎯 Target Users

DevOps engineers, cloud architects, and AWS practitioners seeking intelligent assistance with AWS infrastructure management, DevOps workflows, troubleshooting, and best practices guidance.

## 📄 License & Contributing

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Contributions welcome! Please run tests before submitting PRs:
```bash
python3 tests/check_permissions.py && python3 tests/test_memory_save.py
```

---

**For detailed documentation, see the [`docs/`](docs/) directory.**