# IAM Policies for AWS DevOps Agent

This directory contains IAM policies required for the AWS DevOps Agent deployment and operation.

## Policy Files

### Core Policies

#### `agentcore-policy.json`
**Purpose**: IAM permissions policy for the AgentCore Runtime execution role

**Permissions Included**:
- **Amazon Bedrock**: Model invocation and foundation model listing
- **AgentCore Services**: Full access to Bedrock AgentCore resources
- **CloudWatch Logs**: Log group and stream management
- **SSM Parameter Store**: Configuration parameter access
- **Amazon Cognito**: User pool and client management
- **AWS Lambda**: Function invocation for web search
- **Amazon ECR**: Container image access for deployment

**Usage**: Attach to the AgentCore Runtime execution role

#### `trust-policy.json`
**Purpose**: Trust relationship policy for the AgentCore Runtime execution role

**Trusted Entities**:
- `bedrock-agentcore.amazonaws.com` - Allows AgentCore service to assume the role

**Usage**: Used as the trust policy when creating the execution role

## Policy Details

### AgentCore Policy Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/app/devopsagent/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:devops-agent-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    }
  ]
}
```

### Trust Policy Configuration

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Usage Instructions

### Creating the IAM Role

#### Using AWS CLI

1. **Create the execution role**:
```bash
aws iam create-role \
  --role-name AgentRuntimeExecutionRole \
  --assume-role-policy-document file://iampolicies/trust-policy.json
```

2. **Attach the permissions policy**:
```bash
aws iam put-role-policy \
  --role-name AgentRuntimeExecutionRole \
  --policy-name AgentCorePolicy \
  --policy-document file://iampolicies/agentcore-policy.json
```

3. **Get the role ARN**:
```bash
aws iam get-role --role-name AgentRuntimeExecutionRole --query 'Role.Arn' --output text
```

#### Using AWS Console

1. **Navigate to IAM Console** → Roles → Create role
2. **Select trusted entity**: Custom trust policy
3. **Paste trust policy** from `trust-policy.json`
4. **Create inline policy** using content from `agentcore-policy.json`
5. **Name the role**: `AgentRuntimeExecutionRole`
6. **Copy the role ARN** for deployment

### Deployment Integration

The `deploy_runtime.py` script automatically:
- Creates the IAM role using these policies
- Stores the role ARN in SSM Parameter Store
- Uses the role for AgentCore Runtime deployment

## Security Best Practices

### Principle of Least Privilege
- Policies grant only necessary permissions for agent operation
- SSM parameter access is scoped to `/app/devopsagent/*` path
- Lambda invocation is limited to `devops-agent-*` functions

### Resource Scoping
- **Bedrock**: Full access required for model operations
- **AgentCore**: Full access required for runtime management
- **SSM**: Scoped to application-specific parameters
- **Lambda**: Scoped to agent-related functions
- **ECR**: Read-only access for container images

### Regular Review
- Review permissions periodically
- Remove unused permissions
- Monitor CloudTrail for policy usage
- Update policies as features evolve

## Troubleshooting

### Common Issues

1. **Role Creation Fails**
   - Verify AWS credentials have IAM permissions
   - Check trust policy JSON syntax
   - Ensure unique role name

2. **Permission Denied Errors**
   - Verify role is attached to AgentCore Runtime
   - Check policy JSON syntax and permissions
   - Confirm resource ARN patterns match

3. **SSM Parameter Access Issues**
   - Verify parameter path matches policy scope
   - Check parameter exists and has correct permissions
   - Confirm region consistency

### Validation Commands

```bash
# Verify role exists
aws iam get-role --role-name AgentRuntimeExecutionRole

# List attached policies
aws iam list-role-policies --role-name AgentRuntimeExecutionRole

# Get policy document
aws iam get-role-policy --role-name AgentRuntimeExecutionRole --policy-name AgentCorePolicy

# Test SSM access
aws ssm get-parameter --name "/app/devopsagent/agentcore/memory_id"
```

## Policy Maintenance

### Version Control
- All policy changes should be committed to version control
- Document reasons for permission changes
- Test policy changes in development environment first

### Updates and Changes
- Update policies when adding new AWS services
- Remove permissions for deprecated features
- Maintain backward compatibility when possible

### Compliance
- Ensure policies meet organizational security requirements
- Document any exceptions or elevated permissions
- Regular security reviews and audits

## Related Documentation

- [Deployment Guide](../docs/DEPLOYMENT.md) - Complete deployment instructions
- [Authentication Guide](../docs/AUTHENTICATION.md) - OAuth2 and security configuration
- [Development Guide](../docs/DEVELOPMENT.md) - Development setup and testing

## Support

For issues with IAM policies:
1. Check AWS CloudTrail for permission errors
2. Validate policy syntax with AWS Policy Simulator
3. Review AWS documentation for service-specific permissions
4. Test with minimal permissions and expand as needed