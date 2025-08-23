#!/bin/bash
"""
Deploy MCP servers as AWS Lambda functions
"""

echo "🚀 Deploying MCP servers as Lambda functions..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "mcp.json" ]; then
    echo "❌ Error: mcp.json not found. Please run this script from the awslabs-mcp directory."
    exit 1
fi

# Check if utils.py exists in parent directory
if [ ! -f "../utils.py" ]; then
    echo "❌ Error: utils.py not found in parent directory."
    exit 1
fi

# Run the deployment script
python3 deploy_mcp_lambdas.py

echo "✅ Deployment script completed."