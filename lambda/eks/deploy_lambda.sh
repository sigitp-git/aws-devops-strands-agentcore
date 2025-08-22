#!/bin/bash

# AWS Lambda deployment script for EKS functions
# Deploys multiple single-purpose Lambda functions following best practices

set -e

# Configuration
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
RUNTIME="python3.9"
TIMEOUT=30
MEMORY_SIZE=256
ARCHITECTURE="arm64"  # Use ARM64 for better price-performance

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AWS Lambda deployment for EKS functions...${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}Error: AWS CLI not configured or no valid credentials${NC}"
    exit 1
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}Deploying to AWS Account: ${ACCOUNT_ID}${NC}"

# Define Lambda functions to deploy
declare -A FUNCTIONS=(
    ["aws-devops-eks-list-clusters"]="lambda_list_clusters.py"
    ["aws-devops-eks-get-cluster"]="lambda_get_cluster.py"
    ["aws-devops-eks-cluster-health"]="lambda_cluster_health.py"
)

# Create IAM role for Lambda if it doesn't exist
ROLE_NAME="lambda-eks-execution-role"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo -e "${YELLOW}Checking if IAM role exists...${NC}"
if ! aws iam get-role --role-name ${ROLE_NAME} > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating IAM role: ${ROLE_NAME}${NC}"
    
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

    # Create the role
    aws iam create-role \
        --role-name ${ROLE_NAME} \
        --assume-role-policy-document file://trust-policy.json

    # Create execution policy with least privilege
    cat > execution-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "eks:DescribeCluster",
                "eks:ListClusters",
                "eks:ListNodegroups",
                "eks:DescribeNodegroup",
                "eks:ListFargateProfiles",
                "eks:DescribeFargateProfile",
                "eks:ListAddons",
                "eks:DescribeAddon"
            ],
            "Resource": "*"
        }
    ]
}
EOF

    # Attach execution policy
    aws iam put-role-policy \
        --role-name ${ROLE_NAME} \
        --policy-name lambda-eks-execution-policy \
        --policy-document file://execution-policy.json

    # Clean up temporary files
    rm -f trust-policy.json execution-policy.json
    
    echo -e "${GREEN}IAM role created successfully${NC}"
    
    # Wait for role to be available
    echo -e "${YELLOW}Waiting for IAM role to be available...${NC}"
    sleep 10
else
    echo -e "${GREEN}IAM role already exists${NC}"
fi

# Function to create deployment package
create_deployment_package() {
    local function_file=$1
    local package_name=$2
    
    echo -e "${YELLOW}Creating deployment package for ${function_file}...${NC}"
    
    # Clean up any existing package
    rm -rf ${package_name}
    rm -f ${package_name}.zip
    
    # Create package directory
    mkdir -p ${package_name}
    
    # Copy Lambda function
    cp ${function_file} ${package_name}/lambda_function.py
    
    # Install dependencies if requirements file exists
    if [ -f lambda_requirements.txt ]; then
        echo -e "${YELLOW}Installing Python dependencies...${NC}"
        pip install -r lambda_requirements.txt -t ${package_name}/ --quiet
    fi
    
    # Create ZIP package
    cd ${package_name}
    zip -r ../${package_name}.zip . -q
    cd ..
    
    echo -e "${GREEN}Deployment package created: ${package_name}.zip${NC}"
}

# Function to deploy or update Lambda function
deploy_function() {
    local function_name=$1
    local package_name=$2
    local description=$3
    
    echo -e "${YELLOW}Deploying Lambda function: ${function_name}${NC}"
    
    if aws lambda get-function --function-name ${function_name} > /dev/null 2>&1; then
        echo -e "${YELLOW}Updating existing Lambda function...${NC}"
        aws lambda update-function-code \
            --function-name ${function_name} \
            --zip-file fileb://${package_name}.zip
        
        aws lambda update-function-configuration \
            --function-name ${function_name} \
            --timeout ${TIMEOUT} \
            --memory-size ${MEMORY_SIZE} \
            --environment Variables="{LOG_LEVEL=INFO}"
    else
        echo -e "${YELLOW}Creating new Lambda function...${NC}"
        aws lambda create-function \
            --function-name ${function_name} \
            --runtime ${RUNTIME} \
            --role ${ROLE_ARN} \
            --handler lambda_function.lambda_handler \
            --zip-file fileb://${package_name}.zip \
            --timeout ${TIMEOUT} \
            --memory-size ${MEMORY_SIZE} \
            --architectures ${ARCHITECTURE} \
            --environment Variables="{LOG_LEVEL=INFO}" \
            --description "${description}"
    fi
    
    # Wait for function to be active
    echo -e "${YELLOW}Waiting for function to be active...${NC}"
    aws lambda wait function-active --function-name ${function_name}
    
    echo -e "${GREEN}Lambda function deployed successfully: ${function_name}${NC}"
}

# Deploy each function
for function_name in "${!FUNCTIONS[@]}"; do
    function_file="${FUNCTIONS[$function_name]}"
    package_name="${function_name}-package"
    
    # Determine description based on function name
    case $function_name in
        *list-clusters*)
            description="List EKS clusters with pagination support"
            ;;
        *get-cluster*)
            description="Get detailed information about a specific EKS cluster"
            ;;
        *cluster-health*)
            description="Check EKS cluster health status and provide recommendations"
            ;;
        *)
            description="EKS management function"
            ;;
    esac
    
    echo -e "\n${GREEN}Processing ${function_name}...${NC}"
    
    # Create deployment package
    create_deployment_package ${function_file} ${package_name}
    
    # Deploy function
    deploy_function ${function_name} ${package_name} "${description}"
    
    # Test the function
    echo -e "${YELLOW}Testing Lambda function...${NC}"
    
    # Create appropriate test payload based on function type
    case $function_name in
        *list-clusters*)
            test_payload='{"max_results":5,"region":"'${REGION}'"}'
            ;;
        *get-cluster*)
            test_payload='{"cluster_name":"test-cluster","region":"'${REGION}'"}'
            ;;
        *cluster-health*)
            test_payload='{"cluster_name":"test-cluster","region":"'${REGION}'"}'
            ;;
    esac
    
    # Invoke function
    aws lambda invoke \
        --function-name ${function_name} \
        --payload "${test_payload}" \
        --cli-binary-format raw-in-base64-out \
        response-${function_name}.json > /dev/null
    
    # Check response
    if [ -f response-${function_name}.json ]; then
        echo -e "${GREEN}Test response received${NC}"
        # Show first 200 characters of response
        head -c 200 response-${function_name}.json
        echo ""
    else
        echo -e "${RED}No response file generated${NC}"
    fi
    
    # Clean up
    rm -rf ${package_name}
    rm -f ${package_name}.zip
done

echo -e "\n${GREEN}All Lambda functions deployed successfully!${NC}"
echo -e "${GREEN}Deployed functions:${NC}"

for function_name in "${!FUNCTIONS[@]}"; do
    echo -e "  • ${function_name}: arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${function_name}"
done

echo -e "\n${YELLOW}Usage Examples:${NC}"
echo "1. List Clusters:"
echo "   aws lambda invoke --function-name aws-devops-eks-list-clusters --payload '{\"max_results\":10}' response.json"
echo ""
echo "2. Get Cluster Details:"
echo "   aws lambda invoke --function-name aws-devops-eks-get-cluster --payload '{\"cluster_name\":\"my-cluster\"}' response.json"
echo ""
echo "3. Check Cluster Health:"
echo "   aws lambda invoke --function-name aws-devops-eks-cluster-health --payload '{\"cluster_name\":\"my-cluster\"}' response.json"

# Clean up response files
rm -f response-*.json

echo -e "\n${GREEN}Deployment completed successfully!${NC}"