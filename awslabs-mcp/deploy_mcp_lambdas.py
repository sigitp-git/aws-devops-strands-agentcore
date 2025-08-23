#!/usr/bin/env python3
"""
Deploy MCP servers as AWS Lambda functions for AgentCore Gateway integration.
"""

import json
import os
import subprocess
import sys
import boto3
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import sys
import os
# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_ssm_parameter, put_ssm_parameter

class MCPLambdaDeployer:
    """Deploy MCP servers as Lambda functions."""
    
    def __init__(self, region="us-east-1"):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.sts_client = boto3.client('sts', region_name=region)
        
        # Get account ID
        self.account_id = self.sts_client.get_caller_identity()['Account']
        
        # Lambda configuration
        self.lambda_role_name = "MCPLambdaExecutionRole"
        self.lambda_timeout = 300  # 5 minutes
        self.lambda_memory = 512   # MB
        
    def load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP configuration from SSM or local file."""
        # Try SSM first
        try:
            config_json = get_ssm_parameter("/app/devopsagent/mcp/config")
            if config_json:
                config = json.loads(config_json)
                print(f"✅ Loaded MCP configuration from SSM with {len(config.get('mcpServers', {}))} servers")
                return config
        except Exception as e:
            print(f"⚠️  Could not load from SSM: {e}")
        
        # Fallback to local file
        try:
            config_file = Path("mcp.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"✅ Loaded MCP configuration from file with {len(config.get('mcpServers', {}))} servers")
                return config
        except Exception as e:
            print(f"❌ Could not load from file: {e}")
        
        return {}
    
    def get_deployable_servers(self, config: Dict[str, Any]) -> Dict[str, Dict]:
        """Get servers that can be deployed as Lambda functions."""
        servers = config.get('mcpServers', {})
        deployable = {}
        
        for name, server_config in servers.items():
            if server_config.get('disabled', False):
                continue
                
            command = server_config.get('command', '')
            
            # Check if server can be deployed as Lambda
            if self._is_deployable_as_lambda(name, server_config):
                deployable[name] = server_config
                print(f"✅ {name} - Deployable as Lambda")
            else:
                print(f"⚠️  {name} - Not suitable for Lambda deployment ({command})")
        
        return deployable
    
    def _is_deployable_as_lambda(self, name: str, config: Dict) -> bool:
        """Check if a server can be deployed as Lambda."""
        command = config.get('command', '')
        
        # Skip Docker-based servers (require container runtime)
        if command == 'docker':
            return False
        
        # Skip servers that require complex setup
        skip_patterns = [
            'mcp-proxy',  # Proxy servers
            'ghcr.io',    # Container images
        ]
        
        args = config.get('args', [])
        for pattern in skip_patterns:
            if any(pattern in arg for arg in args):
                return False
        
        return True
    
    def create_lambda_execution_role(self) -> str:
        """Create or get Lambda execution role."""
        role_arn = f"arn:aws:iam::{self.account_id}:role/{self.lambda_role_name}"
        
        try:
            # Check if role exists
            self.iam_client.get_role(RoleName=self.lambda_role_name)
            print(f"✅ Using existing Lambda execution role: {role_arn}")
            return role_arn
        except self.iam_client.exceptions.NoSuchEntityException:
            pass
        
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            self.iam_client.create_role(
                RoleName=self.lambda_role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Execution role for MCP Lambda functions"
            )
            
            # Attach basic Lambda execution policy
            self.iam_client.attach_role_policy(
                RoleName=self.lambda_role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            
            # Attach additional permissions for MCP servers
            mcp_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ssm:GetParameter",
                            "ssm:GetParameters",
                            "bedrock:*",
                            "s3:GetObject",
                            "s3:PutObject"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            self.iam_client.put_role_policy(
                RoleName=self.lambda_role_name,
                PolicyName="MCPServerPolicy",
                PolicyDocument=json.dumps(mcp_policy)
            )
            
            print(f"✅ Created Lambda execution role: {role_arn}")
            return role_arn
            
        except Exception as e:
            print(f"❌ Failed to create Lambda execution role: {e}")
            raise
    
    def create_lambda_function_code(self, server_name: str, server_config: Dict) -> str:
        """Generate Lambda function code for MCP server."""
        command = server_config.get('command', '')
        args = server_config.get('args', [])
        env_vars = server_config.get('env', {})
        
        # Generate Lambda handler code
        lambda_code = f'''import json
import os
import subprocess
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for {server_name} MCP server.
    
    This function acts as a proxy to the MCP server functionality.
    """
    try:
        # Set environment variables
        env_vars = {json.dumps(env_vars, indent=8)}
        for key, value in env_vars.items():
            if value.startswith("${{") and value.endswith("}}"):
                # Resolve environment variable
                env_key = value[2:-2]
                os.environ[key] = os.environ.get(env_key, value)
            else:
                os.environ[key] = value
        
        # Extract operation and parameters from event
        operation = event.get('operation', 'default')
        parameters = event.get('parameters', {{}})
        
        logger.info(f"Processing {{operation}} for {server_name}")
        
        # Route to appropriate handler based on server type
        result = handle_mcp_operation(operation, parameters)
        
        return {{
            'statusCode': 200,
            'body': json.dumps({{
                'success': True,
                'server': '{server_name}',
                'operation': operation,
                'result': result
            }})
        }}
        
    except Exception as e:
        logger.error(f"Error in {server_name}: {{e}}")
        return {{
            'statusCode': 500,
            'body': json.dumps({{
                'success': False,
                'error': str(e),
                'server': '{server_name}'
            }})
        }}

def handle_mcp_operation(operation: str, parameters: Dict[str, Any]) -> Any:
    """Handle MCP server operations."""
    # This is a placeholder - actual implementation would depend on the specific MCP server
    # For now, return a success response
    return {{
        'message': f'MCP server {server_name} operation {{operation}} completed',
        'parameters': parameters
    }}
'''
        
        return lambda_code
    
    def create_deployment_package(self, server_name: str, server_config: Dict) -> str:
        """Create deployment package for Lambda function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Lambda function code
            lambda_code = self.create_lambda_function_code(server_name, server_config)
            lambda_file = temp_path / "lambda_function.py"
            lambda_file.write_text(lambda_code)
            
            # Create requirements.txt if needed
            requirements = self._get_requirements_for_server(server_name, server_config)
            if requirements:
                req_file = temp_path / "requirements.txt"
                req_file.write_text("\\n".join(requirements))
                
                # Install dependencies
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "-r", str(req_file), "-t", str(temp_path)
                ], check=True)
            
            # Create ZIP package
            zip_path = temp_path / f"{server_name}-lambda.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file() and not file_path.name.endswith('.zip'):
                        arcname = file_path.relative_to(temp_path)
                        zipf.write(file_path, arcname)
            
            # Read ZIP content
            with open(zip_path, 'rb') as f:
                return f.read()
    
    def _get_requirements_for_server(self, server_name: str, server_config: Dict) -> List[str]:
        """Get Python requirements for specific MCP server."""
        # Map server names to their Python dependencies
        requirements_map = {
            'awslabs.aws-pricing-mcp-server': ['boto3', 'requests'],
            'awslabs.aws-documentation-mcp-server': ['boto3', 'requests', 'beautifulsoup4'],
            'awslabs.cloudwatch-mcp-server': ['boto3'],
            'awslabs.eks-mcp-server': ['boto3', 'kubernetes'],
            'awslabs.terraform-mcp-server': ['boto3', 'requests'],
            'awslabs.git-repo-research-mcp-server': ['boto3', 'requests', 'gitpython'],
        }
        
        return requirements_map.get(server_name, ['boto3', 'requests'])
    
    def deploy_lambda_function(self, server_name: str, server_config: Dict, role_arn: str) -> str:
        """Deploy individual Lambda function."""
        function_name = f"mcp-{server_name.replace('.', '-').replace('_', '-')}"
        
        try:
            # Create deployment package
            print(f"📦 Creating deployment package for {server_name}...")
            zip_content = self.create_deployment_package(server_name, server_config)
            
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                # Update existing function
                print(f"🔄 Updating existing Lambda function: {function_name}")
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                print(f"🚀 Creating new Lambda function: {function_name}")
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.11',
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_content},
                    Description=f'MCP server: {server_name}',
                    Timeout=self.lambda_timeout,
                    MemorySize=self.lambda_memory,
                    Environment={
                        'Variables': {
                            'MCP_SERVER_NAME': server_name,
                            **server_config.get('env', {})
                        }
                    }
                )
            
            function_arn = response['FunctionArn']
            print(f"✅ Lambda function deployed: {function_arn}")
            
            return function_arn
            
        except Exception as e:
            print(f"❌ Failed to deploy Lambda function for {server_name}: {e}")
            raise
    
    def deploy_all_servers(self) -> Dict[str, str]:
        """Deploy all deployable MCP servers as Lambda functions."""
        print("🚀 Starting MCP Lambda deployment...")
        
        # Load configuration
        config = self.load_mcp_config()
        if not config:
            print("❌ No MCP configuration found")
            return {}
        
        # Get deployable servers
        deployable_servers = self.get_deployable_servers(config)
        if not deployable_servers:
            print("❌ No deployable servers found")
            return {}
        
        print(f"📋 Found {len(deployable_servers)} deployable servers")
        
        # Create execution role
        role_arn = self.create_lambda_execution_role()
        
        # Deploy each server
        deployed_functions = {}
        for server_name, server_config in deployable_servers.items():
            try:
                function_arn = self.deploy_lambda_function(server_name, server_config, role_arn)
                deployed_functions[server_name] = function_arn
            except Exception as e:
                print(f"⚠️  Failed to deploy {server_name}: {e}")
                continue
        
        # Save deployment info to SSM
        if deployed_functions:
            deployment_info = {
                'deployed_functions': deployed_functions,
                'deployment_timestamp': str(subprocess.check_output(['date'], text=True).strip()),
                'region': self.region
            }
            put_ssm_parameter(
                "/app/devopsagent/mcp/lambda_deployments", 
                json.dumps(deployment_info, indent=2),
                tier="Advanced"
            )
        
        return deployed_functions

def main():
    """Main deployment function."""
    print("🚀 MCP Lambda Deployment")
    print("=" * 50)
    
    deployer = MCPLambdaDeployer()
    deployed_functions = deployer.deploy_all_servers()
    
    if deployed_functions:
        print(f"\\n🎉 Successfully deployed {len(deployed_functions)} Lambda functions:")
        for server_name, function_arn in deployed_functions.items():
            print(f"  • {server_name}: {function_arn}")
        
        print("\\n💡 Next steps:")
        print("1. Configure the AgentCore Gateway to use these Lambda functions")
        print("2. Test the deployed functions")
        print("3. Update the runtime to use the new Lambda-based MCP servers")
    else:
        print("\\n❌ No functions were deployed successfully")

if __name__ == "__main__":
    main()