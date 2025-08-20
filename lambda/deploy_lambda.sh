#!/bin/bash

# AWS Lambda Deployment Script for Web Search Function
# This script packages and deploys the web search Lambda function

set -e

# Configuration
FUNCTION_NAME="devops-agent-websearch"
REGION="us-east-1"
RUNTIME="python3.11"
HANDLER="lambda_websearch.lambda_handler"
TIMEOUT=30
MEMORY_SIZE=256
PACKAGE_DIR="lambda_package"
ZIP_FILE="websearch_lambda.zip"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Lambda deployment for ${FUNCTION_NAME}${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}🔍 Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS credentials verified${NC}"

# Create package directory
echo -e "${YELLOW}📦 Creating package directory...${NC}"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Install dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install -r lambda_requirements.txt -t $PACKAGE_DIR --no-deps
pip install -r lambda_requirements.txt -t $PACKAGE_DIR

# Copy Lambda function
echo -e "${YELLOW}📋 Copying Lambda function...${NC}"
cp lambda_websearch.py $PACKAGE_DIR/

# Create deployment package
echo -e "${YELLOW}🗜️  Creating deployment package...${NC}"
cd $PACKAGE_DIR
zip -r ../$ZIP_FILE . -q
cd ..

echo -e "${GREEN}✅ Package created: ${ZIP_FILE}${NC}"

# Check if function exists
echo -e "${YELLOW}🔍 Checking if Lambda function exists...${NC}"
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &> /dev/null; then
    echo -e "${YELLOW}🔄 Function exists. Updating code...${NC}"
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://$ZIP_FILE \
        --region $REGION
    
    echo -e "${GREEN}✅ Function code updated successfully${NC}"
else
    echo -e "${YELLOW}🆕 Function doesn't exist. Creating new function...${NC}"
    
    # Create IAM role if it doesn't exist
    ROLE_NAME="lambda-websearch-role"
    ROLE_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/$ROLE_NAME"
    
    if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
        echo -e "${YELLOW}🔐 Creating IAM role...${NC}"
        
        # Create trust policy
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
        
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document file://trust-policy.json
        
        # Attach basic execution policy
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        rm trust-policy.json
        echo -e "${GREEN}✅ IAM role created${NC}"
        
        # Wait for role to be available
        echo -e "${YELLOW}⏳ Waiting for IAM role to be available...${NC}"
        sleep 10
    fi
    
    # Create Lambda function
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://$ZIP_FILE \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --region $REGION \
        --description "Web search function for DevOps Agent using DuckDuckGo"
    
    echo -e "${GREEN}✅ Lambda function created successfully${NC}"
fi

# Test the function
echo -e "${YELLOW}🧪 Testing the function...${NC}"
TEST_PAYLOAD='{"keywords": "AWS Lambda best practices", "region": "us-en", "max_results": 3}'

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --cli-binary-format raw-in-base64-out \
    --payload "$TEST_PAYLOAD" \
    --region $REGION \
    response.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Function test completed. Check response.json for results${NC}"
    echo -e "${YELLOW}📄 Test response:${NC}"
    cat response.json | python3 -m json.tool
else
    echo -e "${RED}❌ Function test failed${NC}"
fi

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -rf $PACKAGE_DIR
rm -f $ZIP_FILE

echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo -e "${YELLOW}📝 Function details:${NC}"
echo -e "   Function Name: ${FUNCTION_NAME}"
echo -e "   Region: ${REGION}"
echo -e "   Runtime: ${RUNTIME}"
echo -e "   Handler: ${HANDLER}"

echo -e "${YELLOW}💡 To invoke the function:${NC}"
echo -e "   aws lambda invoke --function-name ${FUNCTION_NAME} --payload '{\"keywords\":\"your search terms\"}' response.json"