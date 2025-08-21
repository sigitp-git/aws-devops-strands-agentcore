# AWS DevOps Agent - Authentication Guide

## Overview

The AWS DevOps Agent uses Amazon Cognito User Pool for authentication to access AWS Bedrock AgentCore Gateway services. The authentication flow implements the OAuth 2.0 Client Credentials Grant pattern, which is designed for machine-to-machine authentication scenarios.

## Architecture Diagram

![Cognito Authentication Flow](./diagrams/cognito_auth_flow_diagram.png.png)

## Authentication Flow

### 1. Configuration Retrieval Phase

The agent retrieves authentication configuration from AWS Systems Manager (SSM) Parameter Store:

**SSM Parameters Retrieved:**
- `/app/devopsagent/agentcore/machine_client_id` - Cognito App Client ID
- `/app/devopsagent/agentcore/userpool_id` - Cognito User Pool ID  
- `/app/devopsagent/agentcore/cognito_token_url` - OAuth2 Token Endpoint
- `/app/devopsagent/agentcore/cognito_auth_scope` - OAuth2 Scope (default: "openid")
- `/app/devopsagent/agentcore/cognito_discovery_url` - OIDC Discovery URL

**Code Implementation:**
```python
# From agent.py - Configuration retrieval
scope_string = get_ssm_parameter("/app/devopsagent/agentcore/cognito_auth_scope") or "openid"
url = get_ssm_parameter("/app/devopsagent/agentcore/cognito_token_url") or "https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/token"
```

### 2. Client Secret Retrieval Phase

The agent dynamically retrieves the Cognito App Client Secret using the AWS Cognito Identity Provider API:

**Code Implementation:**
```python
# From utils.py - Dynamic client secret retrieval
def get_cognito_client_secret() -> str:
    client = boto3.client("cognito-idp")
    response = client.describe_user_pool_client(
        UserPoolId=get_ssm_parameter("/app/devopsagent/agentcore/userpool_id"),
        ClientId=get_ssm_parameter("/app/devopsagent/agentcore/machine_client_id"),
    )
    return response["UserPoolClient"]["ClientSecret"]
```

### 3. OAuth2 Token Request Phase

The agent performs an OAuth2 Client Credentials Grant request to obtain an access token:

**HTTP Request Details:**
- **Method:** POST
- **URL:** Cognito Token Endpoint
- **Headers:** `Content-Type: application/x-www-form-urlencoded`
- **Body Parameters:**
  - `grant_type`: "client_credentials"
  - `client_id`: Machine Client ID
  - `client_secret`: Retrieved Client Secret
  - `scope`: OAuth2 scope (typically "openid")

**Code Implementation:**
```python
# From agent.py - OAuth2 token request
def get_token(client_id: str, client_secret: str, scope_string: str = None, url: str = None) -> dict:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope_string,
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()
```

### 4. Token Response Processing

**Successful Response Format:**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "openid"
}
```

**Error Handling:**
```python
# Token validation and error handling
if 'error' in gateway_access_token:
    raise Exception(f"Failed to get access token: {gateway_access_token['error']}")

if 'access_token' not in gateway_access_token:
    raise Exception("No access_token in authentication response")
```

### 5. Authenticated Service Access

The agent uses the Bearer token to authenticate requests to AWS Bedrock AgentCore Gateway:

**Code Implementation:**
```python
# MCP client setup with Bearer token authentication
mcp_client = MCPClient(
    lambda: streamablehttp_client(
        gateway['gateway_url'],
        headers={"Authorization": f"Bearer {gateway_access_token['access_token']}"},
    )
)
```

## Authentication Parameters Exchange

### Request Parameters

| Parameter | Source | Description | Example Value |
|-----------|--------|-------------|---------------|
| `grant_type` | Hardcoded | OAuth2 grant type | `"client_credentials"` |
| `client_id` | SSM Parameter | Cognito App Client ID | `"7example123456789"` |
| `client_secret` | Cognito API | App Client Secret | `"secret123...abc"` |
| `scope` | SSM Parameter | OAuth2 scope | `"openid"` |

### Response Parameters

| Parameter | Description | Usage |
|-----------|-------------|-------|
| `access_token` | JWT Bearer token | Used in Authorization header |
| `token_type` | Token type identifier | Always "Bearer" |
| `expires_in` | Token lifetime in seconds | Token expiration tracking |
| `scope` | Granted scopes | Scope validation |

## Configuration Requirements

### Cognito User Pool Setup

1. **User Pool Configuration:**
   - User Pool must be created in the same AWS region as the agent
   - Domain must be configured for OAuth2 endpoints
   - OIDC discovery must be enabled

2. **App Client Configuration:**
   - App client must support Client Credentials flow
   - Client secret must be generated
   - Appropriate OAuth2 scopes must be configured

3. **Domain Configuration:**
   - Custom domain or Cognito domain must be configured
   - OIDC discovery endpoint must be accessible: `{domain}/.well-known/openid_configuration`

### SSM Parameter Store Setup

All authentication parameters must be stored in SSM Parameter Store with appropriate IAM permissions:

```bash
# Example parameter setup
aws ssm put-parameter --name "/app/devopsagent/agentcore/machine_client_id" --value "your-client-id" --type "String"
aws ssm put-parameter --name "/app/devopsagent/agentcore/userpool_id" --value "your-user-pool-id" --type "String"
aws ssm put-parameter --name "/app/devopsagent/agentcore/cognito_token_url" --value "https://your-domain.auth.region.amazoncognito.com/oauth2/token" --type "String"
aws ssm put-parameter --name "/app/devopsagent/agentcore/cognito_auth_scope" --value "openid" --type "String"
aws ssm put-parameter --name "/app/devopsagent/agentcore/cognito_discovery_url" --value "https://your-domain.auth.region.amazoncognito.com/.well-known/openid_configuration" --type "String"
```

## Security Considerations

### Token Security
- Access tokens are short-lived (typically 1 hour)
- Tokens are stored in memory only, never persisted to disk
- Token refresh is handled automatically by re-authentication

### Network Security
- All authentication requests use HTTPS
- Client secrets are retrieved dynamically, not stored in code
- SSM parameters can be encrypted using KMS

### IAM Permissions
The agent requires the following IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:PutParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/app/devopsagent/agentcore/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cognito-idp:DescribeUserPoolClient"
            ],
            "Resource": "arn:aws:cognito-idp:*:*:userpool/*"
        }
    ]
}
```

## Error Handling and Troubleshooting

### Common Authentication Errors

1. **Invalid Client Credentials**
   - **Error:** `invalid_client`
   - **Cause:** Incorrect client_id or client_secret
   - **Solution:** Verify SSM parameters and Cognito configuration

2. **Invalid Grant Type**
   - **Error:** `unsupported_grant_type`
   - **Cause:** App client not configured for client_credentials flow
   - **Solution:** Enable client_credentials in Cognito App Client settings

3. **Invalid Scope**
   - **Error:** `invalid_scope`
   - **Cause:** Requested scope not configured for the app client
   - **Solution:** Configure appropriate scopes in Cognito App Client

4. **Discovery URL Issues**
   - **Error:** Connection timeout or 404
   - **Cause:** Cognito domain not configured or incorrect URL
   - **Solution:** Configure Cognito domain and verify OIDC discovery endpoint

### Debugging Steps

1. **Verify SSM Parameters:**
   ```bash
   aws ssm get-parameter --name "/app/devopsagent/agentcore/machine_client_id"
   ```

2. **Test Token Endpoint:**
   ```bash
   curl -X POST https://your-domain.auth.region.amazoncognito.com/oauth2/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&scope=openid"
   ```

3. **Validate OIDC Discovery:**
   ```bash
   curl https://your-domain.auth.region.amazoncognito.com/.well-known/openid_configuration
   ```

## Implementation Notes

### Graceful Degradation
The agent implements graceful degradation when authentication fails:
- MCP client functionality is disabled
- Core agent functionality continues without gateway features
- Clear error messages guide troubleshooting

### Token Lifecycle Management
- Tokens are obtained on-demand during MCP client initialization
- No automatic token refresh (relies on short session duration)
- New tokens are obtained for each agent session

### Configuration Validation
The agent validates configuration before attempting authentication:
- Checks for required SSM parameters
- Validates OIDC discovery URL format and accessibility
- Provides detailed error messages for configuration issues

This authentication system provides secure, scalable machine-to-machine authentication for the AWS DevOps Agent while maintaining flexibility and proper error handling.