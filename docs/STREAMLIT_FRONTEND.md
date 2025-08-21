# AWS DevOps Agent - Streamlit Frontend

A user-friendly web interface for interacting with the AWS DevOps Agent, built with Streamlit for an intuitive chat-based experience.

## Features

### 🎨 **Modern Web Interface**
- Clean, responsive design with AWS-themed styling
- Real-time chat interface with message history
- Loading indicators and status updates
- Mobile-friendly responsive layout

### 💬 **Interactive Chat Experience**
- Natural conversation flow with the DevOps Agent
- Message history preservation within sessions
- Typing indicators and response timestamps
- Error handling with user-friendly messages

### ⚡ **Quick Actions & Examples**
- Pre-built example prompts for common DevOps questions
- One-click session management (new session, clear chat)
- Session information display
- Quick access to agent capabilities

### 🛠️ **Agent Integration**
- Direct integration with deployed AgentCore Runtime
- Automatic AWS region configuration
- Session management with unique identifiers
- Real-time agent response streaming

## Quick Start

### Prerequisites
- Python 3.8+
- AWS CLI configured with appropriate credentials
- Access to the deployed AWS DevOps Agent
- Streamlit library (automatically installed)

### Installation & Launch

**Option 1: Using the launch script (Recommended)**
```bash
# From project root - Launch the Streamlit app
./run_streamlit.sh

# Or from streamlit directory
cd streamlit && ./run_streamlit.sh
```

**Option 2: Manual launch**
```bash
# Install Streamlit if not already installed
pip install streamlit>=1.28.0

# Set AWS region
export AWS_DEFAULT_REGION=us-east-1

# Navigate to streamlit directory and run the app
cd streamlit
streamlit run streamlit_app.py
```

**Option 3: Custom configuration**
```bash
# Navigate to streamlit directory
cd streamlit

# Run with custom port and host
streamlit run streamlit_app.py --server.port 8502 --server.address localhost
```

### Access the Application
Once launched, the application will be available at:
- **Local access**: http://localhost:8501
- **Network access**: http://your-ip:8501 (if running with --server.address 0.0.0.0)

## User Interface Guide

### 🏠 **Main Chat Interface**
- **Chat Input**: Type your DevOps questions in the input box at the bottom
- **Message History**: View your conversation history with the agent
- **Loading Indicators**: See when the agent is processing your request
- **Response Details**: View timestamps and tools used by the agent

### 📋 **Sidebar Controls**

#### Session Information
- **Session ID**: Unique identifier for your current session
- **Region**: AWS region (us-east-1)
- **Message Count**: Number of messages in current session

#### Quick Actions
- **🔄 New Session**: Start a fresh conversation with the agent
- **📋 Clear Chat**: Clear the current chat history

#### Example Prompts
Pre-built questions to get you started:
- "What are AWS best practices for EC2 security?"
- "How do I set up a CI/CD pipeline with CodePipeline?"
- "Help me troubleshoot a CloudFormation stack error"
- "What's the difference between ALB and NLB?"
- "How do I optimize AWS costs for my infrastructure?"
- "Explain AWS Lambda cold starts and how to minimize them"

#### Agent Capabilities
Quick reference of what the DevOps Agent can help with:
- AWS Services & Infrastructure
- DevOps Best Practices
- CI/CD Pipeline Design
- Infrastructure as Code
- Security & Compliance
- Cost Optimization
- Troubleshooting & Debugging
- Performance Optimization

## Example Usage Scenarios

### 1. **Getting Started with AWS**
```
User: "I'm new to AWS. What are the essential services I should learn first?"
Agent: [Provides comprehensive overview of core AWS services with learning path]
```

### 2. **Troubleshooting Issues**
```
User: "My EC2 instance is running slowly. What should I check?"
Agent: [Provides systematic troubleshooting steps and monitoring recommendations]
```

### 3. **Architecture Design**
```
User: "How do I design a highly available web application on AWS?"
Agent: [Explains multi-AZ deployment, load balancing, and best practices]
```

### 4. **Cost Optimization**
```
User: "My AWS bill is higher than expected. How can I optimize costs?"
Agent: [Provides cost analysis strategies and optimization recommendations]
```

## Configuration

### Environment Variables
The application automatically configures the following:
- `AWS_DEFAULT_REGION=us-east-1` (if not already set)

### AWS Credentials
Ensure your AWS credentials are configured via:
- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- IAM roles (if running on EC2)
- AWS profiles

### Required Permissions
The application needs access to:
- Amazon Bedrock AgentCore Runtime
- SSM Parameter Store (for agent configuration)
- AWS STS (for credential validation)

## Customization

### Styling
The application includes custom CSS for:
- AWS-themed color scheme (#FF9900 orange)
- Responsive chat bubbles
- Professional sidebar styling
- Mobile-friendly layout

### Adding Custom Prompts
To add your own example prompts, edit the `example_prompts` list in `streamlit_app.py`:

```python
example_prompts = [
    "Your custom prompt here",
    "Another custom prompt",
    # Add more prompts as needed
]
```

### Modifying the Interface
Key customization points:
- **Page title and icon**: Modify `st.set_page_config()`
- **CSS styling**: Update the `st.markdown()` CSS section
- **Sidebar content**: Modify the sidebar sections
- **Chat styling**: Update the chat message HTML templates

## Troubleshooting

### Common Issues

1. **"Failed to get agent runtime ARN"**
   - Ensure AWS credentials are configured
   - Verify access to SSM Parameter Store
   - Check that the agent is deployed

2. **"Agent invocation failed"**
   - Verify the agent runtime is active
   - Check AWS region configuration
   - Ensure proper IAM permissions

3. **Streamlit not found**
   - Install Streamlit: `pip install streamlit>=1.28.0`
   - Or run the installation script: `./run_streamlit.sh`

4. **Port already in use**
   - Use a different port: `streamlit run streamlit_app.py --server.port 8502`
   - Or stop the existing Streamlit process

### Debug Mode
To run in debug mode with more verbose output:
```bash
streamlit run streamlit_app.py --logger.level debug
```

### Logs and Monitoring
- Streamlit logs appear in the terminal where you launched the app
- AWS API calls are logged through boto3
- Agent responses include timestamps and tool usage information

## Performance Considerations

### Response Times
- **Simple queries**: 2-5 seconds
- **Complex queries**: 5-15 seconds
- **Web search queries**: 30-60 seconds
- **Error responses**: <1 second

### Session Management
- Each browser session gets a unique session ID
- Message history is preserved within the browser session
- Sessions are isolated between different browser tabs/windows

### Resource Usage
- **Memory**: ~50-100MB for the Streamlit app
- **CPU**: Minimal when idle, moderate during agent interactions
- **Network**: Depends on agent response size and frequency

## Security Best Practices

### Data Handling
- No conversation data is stored permanently
- Session data exists only in browser memory
- AWS credentials are handled securely through boto3

### Network Security
- Run on localhost for development
- Use HTTPS in production deployments
- Consider VPN or private networks for sensitive environments

### Access Control
- Relies on AWS IAM for backend access control
- No built-in authentication (add if needed for production)
- Consider adding authentication middleware for multi-user scenarios

## Deployment Options

### Local Development
```bash
# Standard local development
streamlit run streamlit_app.py
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0"]
```

### Cloud Deployment
- **AWS EC2**: Deploy on EC2 instance with security groups
- **AWS ECS**: Containerized deployment with load balancing
- **Streamlit Cloud**: Direct deployment from GitHub repository

## Contributing

To contribute improvements to the Streamlit frontend:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/streamlit-enhancement`
3. **Make your changes** to `streamlit_app.py`
4. **Test thoroughly** with different scenarios
5. **Update documentation** if needed
6. **Submit a pull request**

### Development Guidelines
- Follow Streamlit best practices
- Maintain responsive design
- Add error handling for new features
- Update example prompts as needed
- Test with different screen sizes

## License

This Streamlit frontend is part of the AWS DevOps Agent project and is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.