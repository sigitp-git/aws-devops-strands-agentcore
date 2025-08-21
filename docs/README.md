# AWS DevOps Agent

An intelligent AWS DevOps assistant built with Amazon Bedrock and AgentCore Memory. The agent provides expert guidance on AWS infrastructure, operations, and DevOps best practices while maintaining conversation context through persistent memory.

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Complete deployment options (local, cloud, Lambda)
- **[Authentication Guide](AUTHENTICATION.md)** - OAuth2 flow and security configuration  
- **[Development Guide](DEVELOPMENT.md)** - Setup, testing, and technical implementation
- **[System Status](STATUS.md)** - Current functionality and performance status

## ✨ Key Features

- **🧠 Intelligent Memory**: Cross-session persistence with semantic search and preference learning
- **🔐 Secure Authentication**: OAuth2 Client Credentials flow with Amazon Cognito and JWT tokens
- **🚀 Dual Deployment**: Local CLI mode and scalable cloud deployment via AgentCore Runtime
- **🔍 Real-time Search**: DuckDuckGo integration with deployable Lambda function
- **⚡ AWS Expertise**: Specialized knowledge powered by Claude Sonnet 4 (temperature 0.3)
- **🛠️ MCP Integration**: Advanced tool access through Bedrock AgentCore Gateway
- **🎯 Kiro IDE Integration**: Automated code quality analysis and documentation sync

## 🚀 Quick Start

### Prerequisites
- Python 3.8+, AWS CLI configured, Access to Amazon Bedrock
- AWS region: `us-east-1` (default)

### Installation
```bash
git clone https://github.com/sigitp-git/aws-devops-strands-agentcore.git
cd aws-devops-strands-agentcore
pip install -r requirements.txt
aws configure  # Set AWS_DEFAULT_REGION=us-east-1
```

### Usage
```bash
# Local interactive mode
python3 agent.py

# Test functionality
python3 tests/check_permissions.py
python3 tests/test_memory_save.py
```

> 📖 **For detailed setup, deployment options, and troubleshooting, see the [Deployment Guide](DEPLOYMENT.md)**

## 💡 Usage Examples

### Memory Functionality
The agent remembers your preferences across sessions:

```bash
# Session 1: Set preference
You > my favorite aws service is amazon bedrock
Agent > That's awesome! Amazon Bedrock is a fantastic choice...

# Session 2: Recall preference  
You > what is my favorite aws service?
Agent > Your favorite AWS service is Amazon Bedrock!
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

> 📖 **For comprehensive examples, testing guides, and troubleshooting, see the [Development Guide](DEVELOPMENT.md)**

## 🏗️ Architecture

### Core Components
- **Claude Sonnet 4**: AI model (temperature 0.3 for technical accuracy)
- **AgentCore Memory**: 90-day persistent memory with semantic search
- **Cognito Authentication**: OAuth2 JWT tokens for secure access
- **MCP Gateway**: Advanced tool integration
- **Lambda Functions**: Scalable web search capability

### AWS Services
Amazon Bedrock • AgentCore Memory • Cognito • SSM Parameter Store • Lambda • IAM • CloudWatch

> 📖 **For detailed architecture, configuration, and AWS services, see the [Development Guide](DEVELOPMENT.md)**

## 🎯 Target Users

DevOps engineers, cloud architects, and AWS practitioners seeking intelligent assistance with AWS infrastructure management, DevOps workflows, troubleshooting, and best practices guidance.

## 🔧 Troubleshooting

### Common Issues
1. **Permission Errors**: Run `python3 tests/check_permissions.py`
2. **Memory Issues**: Use `python3 tests/debug_memory.py`  
3. **Region Mismatch**: Ensure `AWS_DEFAULT_REGION=us-east-1`

> 📖 **For comprehensive troubleshooting, debugging guides, and technical details, see the [Development Guide](DEVELOPMENT.md)**

## 📊 Current Status

✅ **ALL SYSTEMS OPERATIONAL** - Production ready with comprehensive testing  
✅ **AWS Integration** - 25 Claude models, all permissions verified  
✅ **Memory System** - Cross-session persistence with 100% success rate  
✅ **Authentication** - OAuth2 JWT tokens with secure gateway access  
✅ **Performance** - 2-3s startup, 1-5s response time, <1s memory retrieval  

> 📖 **For detailed status, performance metrics, and test results, see the [System Status](STATUS.md)**

## 📄 License & Contributing

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

Contributions welcome! Please run tests before submitting PRs:
```bash
python3 tests/check_permissions.py && python3 tests/test_memory_save.py
```

> 📖 **For development setup and contribution guidelines, see the [Development Guide](DEVELOPMENT.md)**