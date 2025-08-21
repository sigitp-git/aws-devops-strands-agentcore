#!/bin/bash
"""
Script to create IAM roles for AWS DevOps Agent deployment.
"""

set -e

echo "🔐 Creating IAM Roles for AWS DevOps Agent"
echo "=========================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "📋 Account ID: $ACCOUNT_ID"
echo "🌍 Region: $REGION"
echo ""

# Create AgentCore Runtime Execution Role
echo "1️⃣ Creating AgentCore Runtime Execution Role..."

if aws iam get-role --role-name AgentRuntimeExecutionRole >/dev/null 2>&1; then
    echo "✅ AgentRuntimeExecutionRole already exists"
else
    echo "📝 Creating role with trust policy..."
    aws iam create-role \
        --role-name AgentRuntimeExecutionRole \
        --assume-role-policy-document file://trust-policy.json \
        --description "Execution role for AWS DevOps Agent AgentCore Runtime"
    
    echo "✅ AgentRuntimeExecutionRole created"
fi

echo "📋 Attaching permissions policy..."
aws iam put-role-policy \
    --role-name AgentRuntimeExecutionRole \
    --policy-name AgentCorePolicy \
    --policy-document file://agentcore-policy.json

echo "✅ Permissions policy attached"

# Get and store the role ARN
ROLE_ARN=$(aws iam get-role --role-name AgentRuntimeExecutionRole --query 'Role.Arn' --output text)
echo "📝 Role ARN: $ROLE_ARN"

# Store in SSM Parameter Store
echo "💾 Storing role ARN in SSM Parameter Store..."
aws ssm put-parameter \
    --name "/app/devopsagent/agentcore/execution_role_arn" \
    --value "$ROLE_ARN" \
    --type "String" \
    --overwrite

echo "✅ Role ARN stored in SSM: /app/devopsagent/agentcore/execution_role_arn"
echo ""

# Create Lambda Execution Role for Web Search Function
echo "2️⃣ Creating Lambda Execution Role..."

if aws iam get-role --role-name devops-agent-lambda-execution-role >/dev/null 2>&1; then
    echo "✅ devops-agent-lambda-execution-role already exists"
else
    echo "📝 Creating Lambda execution role..."
    aws iam create-role \
        --role-name devops-agent-lambda-execution-role \
        --assume-role-policy-document file://lambda-trust-policy.json \
        --description "Execution role for DevOps Agent Lambda functions"
    
    echo "✅ devops-agent-lambda-execution-role created"
fi

echo "📋 Attaching Lambda execution policy..."
aws iam put-role-policy \
    --role-name devops-agent-lambda-execution-role \
    --policy-name LambdaExecutionPolicy \
    --policy-document file://lambda-execution-policy.json

echo "✅ Lambda execution policy attached"

# Get Lambda role ARN
LAMBDA_ROLE_ARN=$(aws iam get-role --role-name devops-agent-lambda-execution-role --query 'Role.Arn' --output text)
echo "📝 Lambda Role ARN: $LAMBDA_ROLE_ARN"

echo ""
echo "🎉 IAM Roles Created Successfully!"
echo "=================================="
echo "✅ AgentCore Runtime Role: $ROLE_ARN"
echo "✅ Lambda Execution Role: $LAMBDA_ROLE_ARN"
echo ""
echo "📋 Next Steps:"
echo "1. Deploy the AgentCore Runtime: python3 deploy_runtime.py"
echo "2. Deploy Lambda functions: cd lambda/websearch && ./deploy_lambda.sh"
echo "3. Test the deployment: python3 invoke_runtime.py"
echo ""
echo "💡 Role ARNs are stored in SSM Parameter Store for automatic use by deployment scripts."put-parameter \
    --name "/app/devopsagent/agentcore/execution_role_arn" \
    --value "$ROLE_ARN" \
    --type "String" \
    --overwrite

echo "✅ Role ARN stored in SSM"
echo ""

# Create Lambda Execution Role (optional)
echo "2️⃣ Creating Lambda Execution Role (optional)..."

if aws iam get-role --role-name devops-agent-lambda-role >/dev/null 2>&1; then
    echo "✅ devops-agent-lambda-role already exists"
else
    echo "📝 Creating Lambda execution role..."
    aws iam create-role \
        --role-name devops-agent-lambda-role \
        --assume-role-policy-document file://lambda-trust-policy.json \
        --description "Execution role for DevOps Agent Lambda functions"
    
    echo "✅ devops-agent-lambda-role created"
fi

echo "📋 Attaching Lambda execution policy..."
aws iam put-role-policy \
    --role-name devops-agent-lambda-role \
    --policy-name LambdaExecutionPolicy \
    --policy-document file://lambda-execution-policy.json

echo "✅ Lambda execution policy attached"

# Summary
echo ""
echo "🎉 IAM Roles Created Successfully!"
echo "=================================="
echo "✅ AgentRuntimeExecutionRole: $ROLE_ARN"
echo "✅ devops-agent-lambda-role: arn:aws:iam::$ACCOUNT_ID:role/devops-agent-lambda-role"
echo ""
echo "📋 Next Steps:"
echo "1. Deploy the AgentCore Runtime: python3 deploy_runtime.py"
echo "2. Deploy Lambda functions: cd lambda/websearch && ./deploy_lambda.sh"
echo "3. Test the deployment: python3 invoke_runtime.py"
echo ""
echo "🔍 Verify roles in AWS Console:"
echo "https://console.aws.amazon.com/iam/home?region=$REGION#/roles"