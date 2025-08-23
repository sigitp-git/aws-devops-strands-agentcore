#!/bin/bash

# Master deployment script for all Prometheus functions
# Deploys all four specialized functions with proper IAM roles
# Follows Lambda best practices for deployment automation
# Comprehensive testing and validation

set -e

echo "=========================================="
echo "Deploying All Prometheus Lambda Functions"
echo "=========================================="

# Check AWS CLI configuration
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "Error: AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

REGION="${AWS_REGION:-us-east-1}"
echo "Using AWS region: $REGION"

# Check if IAM roles exist
ROLE_NAME="prometheus-lambda-execution-role"
if ! aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
    echo "Error: IAM role $ROLE_NAME not found."
    echo "Please create IAM roles first using:"
    echo "cd ../../iampolicies && ./create-iam-roles.sh"
    exit 1
fi

echo "IAM roles verified successfully."

# Make deployment scripts executable
chmod +x deploy_query.sh
chmod +x deploy_range_query.sh
chmod +x deploy_list_metrics.sh
chmod +x deploy_server_info.sh

# Deploy each function
echo ""
echo "1/4 Deploying Query Function..."
./deploy_query.sh

echo ""
echo "2/4 Deploying Range Query Function..."
./deploy_range_query.sh

echo ""
echo "3/4 Deploying List Metrics Function..."
./deploy_list_metrics.sh

echo ""
echo "4/4 Deploying Server Info Function..."
./deploy_server_info.sh

echo ""
echo "=========================================="
echo "All Prometheus Lambda Functions Deployed!"
echo "=========================================="

# Display function summary
echo ""
echo "Function Summary:"
echo "├── prometheus-query (256MB, 30s) - Instant queries"
echo "├── prometheus-range-query (512MB, 60s) - Range queries"
echo "├── prometheus-list-metrics (256MB, 30s) - Metric discovery"
echo "└── prometheus-server-info (256MB, 30s) - Server configuration"

echo ""
echo "Next Steps:"
echo "1. Test the functions using: python3 test_individual_functions.py"
echo "2. Configure Bedrock AgentCore Gateway integration"
echo "3. Update your agent.py to use the Lambda functions"

echo ""
echo "Integration with Bedrock AgentCore Gateway:"
echo "These functions are designed to be accessed through the MCP framework"
echo "via Bedrock AgentCore Gateway with JWT authentication."