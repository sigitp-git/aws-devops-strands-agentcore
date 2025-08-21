#!/bin/bash
"""
Launch script for the AWS DevOps Agent Streamlit frontend.
"""

echo "🚀 Starting AWS DevOps Agent Streamlit Frontend..."
echo "📍 Make sure you have AWS credentials configured"
echo "🌐 The app will be available at http://localhost:8501"
echo ""

# Set AWS region if not already set
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Install dependencies if needed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit..."
    pip install streamlit>=1.28.0
fi

# Run the Streamlit app
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0