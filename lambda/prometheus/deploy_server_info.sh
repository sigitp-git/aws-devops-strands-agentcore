#!/bin/bash

# Deploy Prometheus Server Info Lambda Function
# Handles server configuration and build information retrieval

set -e

FUNCTION_NAME="aws-devops-prometheus-server-info"
REGION="us-east-1"
ROLE_NAME="aws-devops-prometheus-server-info-role"

echo "Deploying Prometheus Server Info Lambda Function..."
echo "=================================================="

# Create IAM role if it doesn't exist
echo "Creating IAM role: $ROLE_NAME"
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }' \
    --region $REGION 2>/dev/null || echo "Role already exists"

# Attach basic Lambda execution policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    --region $REGION 2>/dev/null || echo "Policy already attached"

# Create and attach Prometheus access policy
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name PrometheusServerInfoAccess \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "aps:QueryMetrics",
                    "aps:GetLabels",
                    "aps:GetSeries",
                    "aps:GetMetricMetadata"
                ],
                "Resource": "*"
            }
        ]
    }' \
    --region $REGION

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text --region $REGION)
echo "Using role: $ROLE_ARN"

# Wait for role to be available
echo "Waiting for IAM role to be available..."
sleep 10

# Create deployment package
echo "Creating deployment package..."
rm -rf lambda_package
mkdir -p lambda_package

# Copy function code and utilities
cp lambda_server_info.py lambda_package/
cp prometheus_utils.py lambda_package/

# Install dependencies
pip install -r lambda_requirements.txt -t lambda_package/

# Create ZIP package
cd lambda_package
zip -r ../prometheus-server-info-deployment.zip .
cd ..

# Deploy or update Lambda function
echo "Deploying Lambda function: $FUNCTION_NAME"
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://prometheus-server-info-deployment.zip \
        --region $REGION
    
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --handler lambda_server_info.lambda_handler \
        --runtime python3.9 \
        --timeout 30 \
        --memory-size 256 \
        --region $REGION
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler lambda_server_info.lambda_handler \
        --zip-file fileb://prometheus-server-info-deployment.zip \
        --timeout 30 \
        --memory-size 256 \
        --description "Prometheus server info Lambda function" \
        --region $REGION
fi

# Clean up
rm -rf lambda_package prometheus-server-info-deployment.zip

echo ""
echo "Deployment completed successfully!"
echo "Function Name: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""
echo "Test the function with:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"workspace_url\":\"YOUR_WORKSPACE_URL\"}' response.json"
echo ""