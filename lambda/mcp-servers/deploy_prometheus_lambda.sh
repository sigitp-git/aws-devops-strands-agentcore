#!/bin/bash

# Deploy Prometheus MCP Server Lambda Function
# This script deploys the Prometheus Lambda function with proper IAM permissions

set -e

echo "🚀 Deploying Prometheus MCP Server Lambda Function"
echo "=================================================="

# Configuration
REGION=${AWS_DEFAULT_REGION:-us-east-1}
FUNCTION_NAME="mcp-prometheus-server"
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
        
        # Update the role policy to include Prometheus permissions
        print_status "Updating IAM role policy for Prometheus..."
        
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
                "cloudformation:List*",
                "aps:*",
                "amp:*"
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
        
        print_success "Updated IAM role policy with Prometheus permissions"
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
    
    # Create and attach MCP-specific policy with Prometheus permissions
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
                "cloudformation:List*",
                "aps:*",
                "amp:*"
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

# Deploy Prometheus Lambda function
deploy_prometheus_lambda() {
    print_status "Deploying Prometheus Lambda function..."
    
    # Create deployment package
    TEMP_DIR=$(mktemp -d)
    
    # Copy function code
    cp "prometheus_lambda.py" "$TEMP_DIR/lambda_function.py"
    
    # Install dependencies
    if [ -f "lambda_requirements.txt" ]; then
        print_status "Installing dependencies..."
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
        print_status "Updating existing function..."
        
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file "fileb://${TEMP_DIR}/../${FUNCTION_NAME}.zip" > /dev/null
        
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY" \
            --environment "Variables={MCP_SERVER_NAME=$FUNCTION_NAME,MCP_REGION=$REGION}" > /dev/null
        
        print_success "Updated $FUNCTION_NAME"
    else
        # Create new function
        print_status "Creating new function..."
        
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime "$LAMBDA_RUNTIME" \
            --role "$ROLE_ARN" \
            --handler "lambda_function.lambda_handler" \
            --zip-file "fileb://${TEMP_DIR}/../${FUNCTION_NAME}.zip" \
            --description "Prometheus MCP server for monitoring and metrics" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY" \
            --environment "Variables={MCP_SERVER_NAME=$FUNCTION_NAME,MCP_REGION=$REGION}" > /dev/null
        
        print_success "Created $FUNCTION_NAME"
    fi
    
    # Get function info
    FUNCTION_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --query 'Configuration.FunctionArn' --output text)
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    rm -f "${TEMP_DIR}/../${FUNCTION_NAME}.zip"
    
    print_success "Function ARN: $FUNCTION_ARN"
}

# Test the deployed function
test_function() {
    print_status "Testing deployed function..."
    
    # Create test payload
    cat > /tmp/test-payload.json << EOF
{
    "operation": "get_available_workspaces",
    "region": "$REGION"
}
EOF
    
    # Invoke function
    print_status "Invoking function with test payload..."
    
    aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --payload file:///tmp/test-payload.json \
        --cli-binary-format raw-in-base64-out \
        /tmp/response.json > /dev/null
    
    # Check response
    if [ -f "/tmp/response.json" ]; then
        RESPONSE=$(cat /tmp/response.json)
        if echo "$RESPONSE" | grep -q '"success": true'; then
            print_success "Function test passed!"
            print_status "Response: $(echo "$RESPONSE" | jq -r '.body' | jq -r '.data.count // "No workspaces"') workspaces found"
        else
            print_warning "Function test completed but may have issues"
            print_status "Response: $RESPONSE"
        fi
    else
        print_warning "No response file generated"
    fi
    
    # Cleanup test files
    rm -f /tmp/test-payload.json /tmp/response.json
}

# Main deployment function
main() {
    print_status "Starting Prometheus Lambda deployment..."
    
    # Check prerequisites
    check_aws_config
    
    # Create IAM role
    create_iam_role
    
    # Deploy function
    deploy_prometheus_lambda
    
    # Test function
    test_function
    
    # Save deployment information
    print_status "Saving deployment information..."
    
    DEPLOYMENT_INFO=$(cat << EOF
{
    "function_name": "$FUNCTION_NAME",
    "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "region": "$REGION",
    "account_id": "$ACCOUNT_ID",
    "lambda_role": "$LAMBDA_ROLE_NAME",
    "function_arn": "$(aws lambda get-function --function-name "$FUNCTION_NAME" --query 'Configuration.FunctionArn' --output text)",
    "lambda_config": {
        "runtime": "$LAMBDA_RUNTIME",
        "timeout": $LAMBDA_TIMEOUT,
        "memory": $LAMBDA_MEMORY
    }
}
EOF
)
    
    aws ssm put-parameter \
        --name "/app/devopsagent/mcp/prometheus_lambda" \
        --value "$DEPLOYMENT_INFO" \
        --type "String" \
        --tier "Advanced" \
        --overwrite > /dev/null
    
    print_success "Deployment information saved to SSM Parameter Store"
    
    # Display summary
    echo ""
    echo "🎉 Prometheus Lambda Deployment Complete!"
    echo "========================================"
    echo "✅ Function: $FUNCTION_NAME"
    echo "✅ Region: $REGION"
    echo "✅ Account: $ACCOUNT_ID"
    echo "✅ IAM Role: $LAMBDA_ROLE_NAME"
    echo ""
    echo "💡 Next Steps:"
    echo "1. Configure AgentCore Gateway to use this Lambda function"
    echo "2. Test with your Prometheus workspace ID"
    echo "3. Update MCP configuration if needed"
    echo ""
    echo "🔧 Available Operations:"
    echo "  • execute_query - Instant PromQL queries"
    echo "  • execute_range_query - Range queries over time"
    echo "  • list_metrics - Discover available metrics"
    echo "  • get_server_info - Server configuration info"
    echo "  • get_available_workspaces - List workspaces"
    echo ""
    echo "📋 Function Details:"
    echo "  Function Name: $FUNCTION_NAME"
    echo "  Runtime: $LAMBDA_RUNTIME"
    echo "  Memory: ${LAMBDA_MEMORY}MB"
    echo "  Timeout: ${LAMBDA_TIMEOUT}s"
}

# Run main function
main "$@"