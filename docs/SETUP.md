# AWS DevOps Agent - Quick Setup Guide

This guide provides step-by-step instructions to get your AWS DevOps Agent up and running quickly.

## Prerequisites

- **AWS Account** with appropriate permissions
- **AWS CLI** configured (`aws configure`)
- **Python 3.8+** installed
- **Docker** with buildx support (for deployment)
- **Git** for cloning the repository

## Quick Start (5 Minutes)

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/sigitp-git/aws-devops-strands-agentcore.git
cd aws-devops-strands-agentcore

# Install dependencies
pip install -r requirements.txt

# Set AWS region
export AWS_DEFAULT_REGION=us-east-1
```

### 2. Create IAM Roles
```bash
# Navigate to IAM policies directory
cd iampolicies

# Create all required IAM roles
./create-iam-roles.sh

# Return to project root
cd ..
```

### 3. Deploy the Agent
```bash
# Deploy to AgentCore Runtime
python3 deploy_runtime.py

# Deploy Lambda web search function
cd lambda/websearch && ./deploy_lambda.sh && cd ../..
```

### 4. Test the Deployment
```bash
# Test with command line interface
python3 invoke_runtime.py

# Or launch web interface
./run_streamlit.sh
# Access at http://localhost:8501
```

## Detailed Setup Options

### Option 1: Web Interface (Recommended)
Perfect for users who prefer graphical interfaces:

```bash
# Launch Streamlit web interface
./run_streamlit.sh

# Access the web interface
open http://localhost:8501
```

**Features:**
- Modern chat interface
- Pre-built example prompts
- Session management
- Mobile-friendly design

### Option 2: Command Line Interface
Great for developers and automation:

```bash
# Interactive CLI mode
python3 agent.py

# Test deployed agent
python3 invoke_runtime.py

# Single query mode
python3 invoke_runtime.py invoke "What are AWS best practices?"
```

### Option 3: Local Runtime Server
For API integration and testing:

```bash
# Start local runtime server
python3 agent_runtime.py

# Test endpoints
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello"}'
```

## Verification Steps

### 1. Check AWS Permissions
```bash
python3 tests/check_permissions.py
```

### 2. Test Memory Functionality
```bash
python3 tests/test_memory_save.py
```

### 3. Validate Runtime Deployment
```bash
python3 tests/test_runtime_local.py
```

## Configuration Files

### IAM Policies (`../iampolicies/`)
- **`agentcore-policy.json`** - Runtime execution permissions
- **`trust-policy.json`** - Service trust relationships
- **`developer-policy.json`** - Developer deployment permissions
- **`lambda-execution-policy.json`** - Lambda function permissions

### Documentation (`docs/`)
- **[Deployment Guide](DEPLOYMENT.md)** - Complete deployment options
- **[Streamlit Frontend](STREAMLIT_FRONTEND.md)** - Web interface guide
- **[Authentication Guide](AUTHENTICATION.md)** - Security configuration
- **[Development Guide](DEVELOPMENT.md)** - Development setup

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Configured**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret, and Region (us-east-1)
   ```

2. **Permission Denied Errors**
   ```bash
   # Check your AWS permissions
   python3 tests/check_permissions.py
   
   # Ensure IAM roles are created
   cd iampolicies && ./create-iam-roles.sh
   ```

3. **Region Mismatch**
   ```bash
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **Memory Issues**
   ```bash
   # Debug memory problems
   python3 tests/debug_memory.py
   ```

### Getting Help

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report problems on GitHub Issues
- **Testing**: Use the comprehensive test suite in `tests/`

## Next Steps

Once your agent is running:

1. **Explore Capabilities**: Try the example prompts in the web interface
2. **Customize**: Modify agent behavior and add new features
3. **Integrate**: Use the API endpoints for your applications
4. **Monitor**: Check CloudWatch logs for performance insights
5. **Scale**: Deploy additional instances as needed

## Security Best Practices

- **IAM Roles**: Use least-privilege permissions
- **Credentials**: Never hardcode AWS credentials
- **Network**: Use VPC endpoints for production
- **Monitoring**: Enable CloudTrail for audit logging
- **Updates**: Keep dependencies updated regularly

## Support

For additional help:
- **Documentation**: Complete guides in `docs/` directory
- **Examples**: Sample code and configurations included
- **Testing**: Comprehensive test suite for validation
- **Community**: GitHub repository for issues and discussions

---

**🚀 Your AWS DevOps Agent is ready to help with infrastructure, DevOps practices, and AWS best practices!**