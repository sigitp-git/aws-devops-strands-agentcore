# AWS DevOps Agent

An intelligent AWS DevOps assistant built with Amazon Bedrock and AgentCore Memory.

## 📚 Documentation

All project documentation has been organized in the [`docs/`](docs/) directory:

### 📋 **Getting Started**
- **[Main Documentation](docs/README.md)** - Complete setup and usage guide
- **[System Overview](docs/SYSTEM_OVERVIEW.md)** - Architecture and system overview
- **[AgentCore Runtime](docs/README_RUNTIME.md)** - Cloud deployment guide

### 🔐 **Authentication & Security**
- **[Cognito Authentication](docs/cognito_authentication_documentation.md)** - Complete OAuth2 flow documentation

### 📊 **Status & Configuration**
- **[Functionality Status](docs/FUNCTIONALITY_STATUS.md)** - System status and verification
- **[Documentation Status](docs/DOCUMENTATION_STATUS.md)** - Documentation completeness
- **[Model Temperature](docs/model_temperature.md)** - Model configuration guide

### 🚀 **Runtime & Deployment**
- **[Runtime Summary](docs/AGENTCORE_RUNTIME_SUMMARY.md)** - AgentCore Runtime integration
- **[Runtime Status](docs/RUNTIME_STATUS_FINAL.md)** - Final deployment status

### 🔧 **Development**
- **[Development Notes](docs/notes.md)** - Development history and testing results

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set AWS region
export AWS_DEFAULT_REGION=us-east-1

# Run the agent locally
python3 agent.py

# Test AgentCore Runtime
python3 tests/test_runtime_local.py

# Deploy to AWS
python3 deploy_runtime.py
```

## Features

- ✅ **AWS Expertise** - Comprehensive AWS DevOps guidance
- ✅ **AgentCore Memory** - Persistent conversation context
- ✅ **MCP Gateway Integration** - Advanced tool access
- ✅ **Web Search** - Real-time information retrieval
- ✅ **AgentCore Runtime** - Scalable cloud deployment
- ✅ **Dual Deployment** - Local CLI and cloud HTTP API

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**For complete documentation, visit the [`docs/`](docs/) directory.**