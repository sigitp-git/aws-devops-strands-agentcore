#!/bin/bash
#
# Deployment script for AWS Lambda function: aws-devops-prometheus-integration
#
# This script deploys the Prometheus integration layer Lambda function that provides
# a unified interface to all Prometheus operations. It routes requests to the
# appropriate specialized Lambda function based on operation type.
#
# The integration layer enables:
# - Unified interface for all Prometheus operations
# - Automatic function selection and routing
# - Backward compatibility with existing applications
# - Easy integration with MCP and other systems

set -e

# Configuration
FUNCTION_NAME="aws-devops-prometheus-integration"
RUNTIME="python3.11"
HANDLER="lambda_integration.lambda_handler"
MEMORY_SIZE=256  # Lightweight function for routing
TIMEOUT=60       # Allow time for downstream function calls
DESCRIPTION="Prometheus Lambda integration layer - unified interface for all operations"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Prometheus Integration Layer Lambda Function${NC}"
echo -e "${BLUE}Function: ${FUNCTION_NAME}${NC}"
echo -e "${BLUE}Handler: ${HANDLER}${NC}"
echo -e "${BLUE}Memory: ${MEMORY_SIZE}MB, Timeout: ${TIMEOUT}s${NC}"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo -e "${BLUE}📍 AWS Account: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${BLUE}📍 AWS Region: ${AWS_REGION}${NC}"
echo ""

# Create IAM role for Lambda function
ROLE_NAME="aws-devops-prometheus-integration-role"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"

echo -e "${YELLOW}🔐 Creating IAM role: ${ROLE_NAME}${NC}"

# Trust policy for Lambda
cat > trust-policy.json << EOF
{
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
}
EOF

# Create role (ignore error if it already exists)
aws iam create-role \
    --role-name "${ROLE_NAME}" \
    --assume-role-policy-document file://trust-policy.json \
    --description "IAM role for Prometheus integration layer Lambda function" \
    2>/dev/null || echo -e "${YELLOW}⚠️  Role ${ROLE_NAME} already exists${NC}"

# Attach basic Lambda execution policy
aws iam attach-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

# Create custom policy for invoking other Lambda functions
cat > lambda-invoke-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:aws-devops-prometheus-*"
            ]
        }
    ]
}
EOF

# Create and attach custom policy
POLICY_NAME="aws-devops-prometheus-integration-policy"
POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"

aws iam create-policy \
    --policy-name "${POLICY_NAME}" \
    --policy-document file://lambda-invoke-policy.json \
    --description "Policy for Prometheus integration layer Lambda function" \
    2>/dev/null || echo -e "${YELLOW}⚠️  Policy ${POLICY_NAME} already exists${NC}"

aws iam attach-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-arn "${POLICY_ARN}"

# Clean up temporary files
rm -f trust-policy.json lambda-invoke-policy.json

echo -e "${GREEN}✅ IAM role and policies configured${NC}"

# Wait for role to be available
echo -e "${YELLOW}⏳ Waiting for IAM role to be available...${NC}"
sleep 10

# Create deployment package
echo -e "${YELLOW}📦 Creating deployment package...${NC}"

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
cp lambda_integration.py "${TEMP_DIR}/"

# Create ZIP package
cd "${TEMP_DIR}"
zip -r lambda_package.zip .
cd - > /dev/null

echo -e "${GREEN}✅ Deployment package created${NC}"

# Deploy Lambda function
echo -e "${YELLOW}🚀 Deploying Lambda function...${NC}"

# Check if function exists
if aws lambda get-function --function-name "${FUNCTION_NAME}" > /dev/null 2>&1; then
    echo -e "${YELLOW}🔄 Function exists, updating code...${NC}"
    
    # Update function code
    aws lambda update-function-code \
        --function-name "${FUNCTION_NAME}" \
        --zip-file "fileb://${TEMP_DIR}/lambda_package.zip"
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name "${FUNCTION_NAME}" \
        --runtime "${RUNTIME}" \
        --handler "${HANDLER}" \
        --memory-size "${MEMORY_SIZE}" \
        --timeout "${TIMEOUT}" \
        --description "${DESCRIPTION}"
        
else
    echo -e "${YELLOW}🆕 Creating new function...${NC}"
    
    # Create new function
    aws lambda create-function \
        --function-name "${FUNCTION_NAME}" \
        --runtime "${RUNTIME}" \
        --role "${ROLE_ARN}" \
        --handler "${HANDLER}" \
        --zip-file "fileb://${TEMP_DIR}/lambda_package.zip" \
        --memory-size "${MEMORY_SIZE}" \
        --timeout "${TIMEOUT}" \
        --description "${DESCRIPTION}"
fi

# Clean up
rm -rf "${TEMP_DIR}"

echo -e "${GREEN}✅ Lambda function deployed successfully${NC}"

# Test the function
echo -e "${YELLOW}🧪 Testing Lambda function...${NC}"

# Test payload for finding workspaces
cat > test_payload.json << EOF
{
    "operation": "find_workspace",
    "parameters": {
        "list_all": true,
        "region": "${AWS_REGION}"
    }
}
EOF

# Invoke function
echo -e "${BLUE}Testing with payload:${NC}"
cat test_payload.json | jq .

echo -e "${BLUE}Function response:${NC}"
aws lambda invoke \
    --function-name "${FUNCTION_NAME}" \
    --payload file://test_payload.json \
    response.json

if [ -f response.json ]; then
    cat response.json | jq .
    rm -f response.json
fi

# Clean up test file
rm -f test_payload.json

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}Function Name: ${FUNCTION_NAME}${NC}"
echo -e "${GREEN}Function ARN: arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNCTION_NAME}${NC}"
echo ""
echo -e "${BLUE}💡 Usage Examples:${NC}"
echo -e "${BLUE}# Execute query operation${NC}"
echo -e "${BLUE}aws lambda invoke --function-name ${FUNCTION_NAME} --payload '{\"operation\":\"query\",\"parameters\":{\"workspace_url\":\"...\",\"query\":\"up\"}}' response.json${NC}"
echo ""
echo -e "${BLUE}# Find workspace by alias${NC}"
echo -e "${BLUE}aws lambda invoke --function-name ${FUNCTION_NAME} --payload '{\"operation\":\"find_workspace\",\"parameters\":{\"alias\":\"production\"}}' response.json${NC}"
echo ""
echo -e "${BLUE}# List all metrics${NC}"
echo -e "${BLUE}aws lambda invoke --function-name ${FUNCTION_NAME} --payload '{\"operation\":\"list_metrics\",\"parameters\":{\"workspace_url\":\"...\"}}' response.json${NC}"