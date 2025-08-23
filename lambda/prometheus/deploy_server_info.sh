#!/bin/bash

# Deploy Prometheus Server Info Lambda Function
# Single responsibility: server information only
# Optimized for configuration queries (256MB, 30s timeout)

set -e

FUNCTION_NAME="prometheus-server-info"
REGION="${AWS_REGION:-us-east-1}"
ROLE_NAME="prometheus-lambda-execution-role"

echo "Deploying Prometheus Server Info Lambda Function..."

# Create deployment package
echo "Creating deployment package..."
rm -rf lambda_package
mkdir -p lambda_package

# Copy function code and utilities
cp lambda_server_info.py lambda_package/
cp prometheus_utils.py lambda_package/
cp consts.py lambda_package/

# Install dependencies
echo "Installing dependencies..."
pip install -r lambda_requirements.txt -t lambda_package/

# Create deployment zip
cd lambda_package
zip -r ../prometheus-server-info-deployment.zip .
cd ..

# Get IAM role ARN
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "Error: IAM role $ROLE_NAME not found. Please create it first using:"
    echo "cd ../../iampolicies && ./create-iam-roles.sh"
    exit 1
fi

echo "Using IAM role: $ROLE_ARN"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://prometheus-server-info-deployment.zip \
        --region $REGION
    
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --handler lambda_server_info.lambda_handler \
        --memory-size 256 \
        --timeout 30 \
        --region $REGION
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler lambda_server_info.lambda_handler \
        --zip-file fileb://prometheus-server-info-deployment.zip \
        --memory-size 256 \
        --timeout 30 \
        --description "Prometheus server info Lambda function - configuration queries" \
        --region $REGION
fi

# Clean up
rm -rf lambda_package prometheus-server-info-deployment.zip

echo "Prometheus Server Info Lambda function deployed successfully!"
echo "Function name: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Memory: 256MB"
echo "Timeout: 30s"