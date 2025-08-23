#!/bin/bash

# Deploy Prometheus Query Lambda Function
# Single responsibility: instant query operations only
# Optimized for fast response times (256MB, 30s timeout)

set -e

FUNCTION_NAME="prometheus-query"
REGION="${AWS_REGION:-us-east-1}"
ROLE_NAME="prometheus-lambda-execution-role"

echo "Deploying Prometheus Query Lambda Function..."

# Create deployment package
echo "Creating deployment package..."
rm -rf lambda_package
mkdir -p lambda_package

# Copy function code and utilities
cp lambda_query.py lambda_package/
cp prometheus_utils.py lambda_package/
cp consts.py lambda_package/

# Install dependencies
echo "Installing dependencies..."
pip install -r lambda_requirements.txt -t lambda_package/

# Create deployment zip
cd lambda_package
zip -r ../prometheus-query-deployment.zip .
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
        --zip-file fileb://prometheus-query-deployment.zip \
        --region $REGION
    
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --handler lambda_query.lambda_handler \
        --memory-size 256 \
        --timeout 30 \
        --region $REGION
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler lambda_query.lambda_handler \
        --zip-file fileb://prometheus-query-deployment.zip \
        --memory-size 256 \
        --timeout 30 \
        --description "Prometheus instant query Lambda function - optimized for fast response times" \
        --region $REGION
fi

# Clean up
rm -rf lambda_package prometheus-query-deployment.zip

echo "Prometheus Query Lambda function deployed successfully!"
echo "Function name: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Memory: 256MB"
echo "Timeout: 30s"