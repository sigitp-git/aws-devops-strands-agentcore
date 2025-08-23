#!/bin/bash

# Deploy All MCP Servers as Lambda Functions
# This script deploys all MCP server Lambda functions following Lambda best practices

set -e

echo "🚀 Deploying All MCP Server Lambda Functions"
echo "=============================================="

# Configuration
REGION=${AWS_DEFAULT_REGION:-us-east-1}
LAMBDA_ROLE_NAME="MCPLambdaExecutionRole"
LAMBDA_TIMEOUT=300
LAMBDA_MEMORY=512
LAMBDA_RUNTIME="python3.11"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is configured
check_aws_config() {
    print_status "Checking AWS configuration..."
    
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        print_error "AWS CLI not configured or credentials invalid"
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS Account: $ACCOUNT_ID, Region: $REGION"
}

# Create or verify IAM role
create_iam_role() {
    print_status "Creating/verifying IAM execution role..."
    
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$LAMBDA_ROLE_NAME"
    
    # Check if role exists
    if aws iam get-role --role-name "$LAMBDA_ROLE_NAME" > /dev/null 2>&1; then
        print_success "IAM role already exists: $ROLE_ARN"
        return 0
    fi
    
    # Create trust policy
    cat > /tmp/trust-policy.json << EOF
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
    
    # Create role
    aws iam create-role \
        --role-name "$LAMBDA_ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "Execution role for MCP Lambda functions"
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name "$LAMBDA_ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    # Create and attach MCP-specific policy
    cat > /tmp/mcp-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:PutParameter",
                "bedrock:*",
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "pricing:*",
                "logs:*",
                "cloudwatch:*",
                "eks:*",
                "ec2:Describe*",
                "iam:GetRole",
                "iam:ListRoles",
                "location:*",
                "cloudformation:Describe*",
                "cloudformation:List*"
            ],
            "Resource": "*"
        }
    ]
}
EOF
    
    aws iam put-role-policy \
        --role-name "$LAMBDA_ROLE_NAME" \
        --policy-name "MCPServerPolicy" \
        --policy-document file:///tmp/mcp-policy.json
    
    print_success "Created IAM role: $ROLE_ARN"
    
    # Wait for role to be available
    print_status "Waiting for IAM role to be available..."
    sleep 10
}

# Deploy individual Lambda function
deploy_lambda_function() {
    local FUNCTION_FILE=$1
    local FUNCTION_NAME=$2
    local DESCRIPTION=$3
    
    print_status "Deploying $FUNCTION_NAME..."
    
    # Create deployment package
    TEMP_DIR=$(mktemp -d)
    
    # Copy function code
    cp "$FUNCTION_FILE" "$TEMP_DIR/lambda_function.py"
    
    # Install dependencies
    if [ -f "lambda_requirements.txt" ]; then
        pip install -r lambda_requirements.txt -t "$TEMP_DIR" --quiet
    fi
    
    # Create ZIP package
    cd "$TEMP_DIR"
    zip -r "../${FUNCTION_NAME}.zip" . > /dev/null
    cd - > /dev/null
    
    # Deploy or update function
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$LAMBDA_ROLE_NAME"
    
    if aws lambda get-function --function-name "$FUNCTION_NAME" > /dev/null 2>&1; then
        # Update existing function
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file "fileb://${TEMP_DIR}/../${FUNCTION_NAME}.zip" > /dev/null
        
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY" > /dev/null
        
        print_success "Updated $FUNCTION_NAME"
    else
        # Create new function
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime "$LAMBDA_RUNTIME" \
            --role "$ROLE_ARN" \
            --handler "lambda_function.lambda_handler" \
            --zip-file "fileb://${TEMP_DIR}/../${FUNCTION_NAME}.zip" \
            --description "$DESCRIPTION" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY" \
            --environment "Variables={MCP_SERVER_NAME=$FUNCTION_NAME,MCP_REGION=$REGION}" > /dev/null
        
        print_success "Created $FUNCTION_NAME"
    fi
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    rm -f "${TEMP_DIR}/../${FUNCTION_NAME}.zip"
}

# Main deployment function
main() {
    print_status "Starting MCP Lambda deployment process..."
    
    # Check prerequisites
    check_aws_config
    
    # Create IAM role
    create_iam_role
    
    # Deploy each MCP server Lambda function
    print_status "Deploying MCP server Lambda functions..."
    
    # Core MCP Server
    deploy_lambda_function "core_lambda.py" "mcp-core-server" "Core MCP server functionality"
    
    # AWS Documentation Server
    deploy_lambda_function "aws_documentation_lambda.py" "mcp-aws-documentation-server" "AWS Documentation search and retrieval"
    
    # AWS Pricing Server
    deploy_lambda_function "aws_pricing_lambda.py" "mcp-aws-pricing-server" "AWS Pricing information and analysis"
    
    # CloudWatch Server
    deploy_lambda_function "cloudwatch_lambda.py" "mcp-cloudwatch-server" "CloudWatch logs and metrics"
    
    # EKS Server
    deploy_lambda_function "eks_lambda.py" "mcp-eks-server" "EKS cluster management and monitoring"
    
    # Terraform Server
    deploy_lambda_function "terraform_lambda.py" "mcp-terraform-server" "Terraform configuration and validation"
    
    # Git Repository Research Server
    deploy_lambda_function "git_repo_research_lambda.py" "mcp-git-repo-research-server" "Git repository research and analysis"
    
    # Frontend Server
    deploy_lambda_function "frontend_lambda.py" "mcp-frontend-server" "Frontend development guidance and React documentation"
    
    # AWS Location Server
    deploy_lambda_function "aws_location_lambda.py" "mcp-aws-location-server" "AWS Location Service operations"
    
    print_success "All MCP server Lambda functions deployed successfully!"
    
    # Save deployment information
    print_status "Saving deployment information to SSM..."
    
    DEPLOYMENT_INFO=$(cat << EOF
{
    "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "region": "$REGION",
    "account_id": "$ACCOUNT_ID",
    "lambda_role": "$LAMBDA_ROLE_NAME",
    "deployed_functions": [
        "mcp-core-server",
        "mcp-aws-documentation-server",
        "mcp-aws-pricing-server",
        "mcp-cloudwatch-server",
        "mcp-eks-server",
        "mcp-terraform-server",
        "mcp-git-repo-research-server",
        "mcp-frontend-server",
        "mcp-aws-location-server"
    ],
    "lambda_config": {
        "runtime": "$LAMBDA_RUNTIME",
        "timeout": $LAMBDA_TIMEOUT,
        "memory": $LAMBDA_MEMORY
    }
}
EOF
)
    
    aws ssm put-parameter \
        --name "/app/devopsagent/mcp/lambda_deployments" \
        --value "$DEPLOYMENT_INFO" \
        --type "String" \
        --tier "Advanced" \
        --overwrite > /dev/null
    
    print_success "Deployment information saved to SSM Parameter Store"
    
    # Display summary
    echo ""
    echo "🎉 Deployment Summary"
    echo "===================="
    echo "✅ 9 Lambda functions deployed successfully"
    echo "✅ IAM role configured: $LAMBDA_ROLE_NAME"
    echo "✅ Region: $REGION"
    echo "✅ Account: $ACCOUNT_ID"
    echo ""
    echo "💡 Next Steps:"
    echo "1. Configure AgentCore Gateway to use these Lambda functions"
    echo "2. Test the deployed functions using the test scripts"
    echo "3. Update your MCP configuration to use Lambda endpoints"
    echo ""
    echo "📋 Deployed Functions:"
    echo "  • mcp-core-server"
    echo "  • mcp-aws-documentation-server"
    echo "  • mcp-aws-pricing-server"
    echo "  • mcp-cloudwatch-server"
    echo "  • mcp-eks-server"
    echo "  • mcp-terraform-server"
    echo "  • mcp-git-repo-research-server"
    echo "  • mcp-frontend-server"
    echo "  • mcp-aws-location-server"
}

# Run main function
main "$@"