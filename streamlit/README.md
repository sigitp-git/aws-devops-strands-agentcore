# Streamlit Frontend for AWS DevOps Agent

This directory contains the Streamlit web interface for the AWS DevOps Agent.

## Files

- **`streamlit_app.py`** - Main Streamlit application
- **`run_streamlit.sh`** - Launch script for the Streamlit app
- **`demo_streamlit.py`** - Demo script showcasing features

## Quick Start

### From Root Directory (Recommended)
```bash
# From the project root
./run_streamlit.sh
```

### From Streamlit Directory
```bash
# Navigate to streamlit directory
cd streamlit

# Launch the app
./run_streamlit.sh
```

### Manual Launch
```bash
# From streamlit directory
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

## Access

Once launched, access the web interface at:
- **Local**: http://localhost:8501
- **Network**: http://your-ip:8501

## Features

- 🎨 Modern web interface with AWS-themed styling
- 💬 Real-time chat with the DevOps Agent
- 🤖 Interactive model selector with 5 Claude models
- 📋 Pre-built example prompts
- 🔄 Session management controls
- 📱 Mobile-friendly responsive design
- ⚡ Direct integration with AgentCore Runtime
- 🔧 Real-time model switching with visual feedback

## Documentation

For complete documentation, see: [../docs/STREAMLIT_FRONTEND.md](../docs/STREAMLIT_FRONTEND.md)

## Requirements

- Python 3.8+
- Streamlit >= 1.28.0
- AWS credentials configured
- Access to deployed AWS DevOps Agent