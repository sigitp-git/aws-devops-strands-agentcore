#!/usr/bin/env python3
"""
Script to check AWS IAM permissions for the DevOps agent
"""
import boto3
import json
import os
from typing import Tuple, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from bedrock_agentcore.memory import MemoryClient


class PermissionChecker:
    """AWS Permission checker with centralized configuration and error handling."""
    
    def __init__(self):
        self.region = self._get_aws_region()
        self.access_denied_codes = ['AccessDenied', 'UnauthorizedOperation']
        
    def _get_aws_region(self) -> str:
        """Get AWS region from environment or session."""
        region = os.environ.get('AWS_DEFAULT_REGION')
        if not region:
            session = boto3.Session()
            region = session.region_name
        return region or 'us-east-1'
    
    def _handle_client_error(self, e: ClientError, service: str, action: str) -> Tuple[bool, str]:
        """Centralized error handling for AWS client errors."""
        error_code = e.response['Error']['Code']
        
        if error_code in self.access_denied_codes:
            return False, f"❌ {service} {action} permission: DENIED"
        else:
            return True, f"⚠️  {service} {action} permission: Unknown error - {e}"
    
    def _print_result(self, success: bool, message: str) -> None:
        """Print formatted result message."""
        print(message)

    def check_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured"""
        print("🔍 Checking AWS credentials...")
        try:
            sts = boto3.client('sts', region_name=self.region)
            identity = sts.get_caller_identity()
            print("✅ AWS credentials configured")
            print(f"   Account ID: {identity['Account']}")
            print(f"   User/Role ARN: {identity['Arn']}")
            print(f"   User ID: {identity['UserId']}")
            return True
        except NoCredentialsError:
            print("❌ AWS credentials not configured")
            print("   Run 'aws configure' or set environment variables")
            return False
        except Exception as e:
            print(f"❌ Error checking credentials: {e}")
            return False

    def _test_ssm_get_parameter(self, ssm_client) -> bool:
        """Test SSM GetParameter permission."""
        try:
            ssm_client.get_parameter(Name='/test/nonexistent/parameter')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                print("✅ SSM GetParameter permission: OK")
                return True
            elif e.response['Error']['Code'] in self.access_denied_codes:
                print("❌ SSM GetParameter permission: DENIED")
                return False
            else:
                print(f"⚠️  SSM GetParameter permission: Unknown error - {e}")
                return False
        except Exception as e:
            print(f"❌ SSM GetParameter permission: Error - {e}")
            return False
    
    def _test_ssm_put_delete_parameter(self, ssm_client) -> bool:
        """Test SSM PutParameter and DeleteParameter permissions."""
        test_param_name = '/test/permission/check'
        
        try:
            ssm_client.put_parameter(
                Name=test_param_name,
                Value='test',
                Type='String',
                Overwrite=True
            )
            print("✅ SSM PutParameter permission: OK")
            
            # Clean up test parameter
            try:
                ssm_client.delete_parameter(Name=test_param_name)
                print("✅ SSM DeleteParameter permission: OK")
            except Exception:
                print("⚠️  Could not clean up test parameter")
            
            return True
        except ClientError as e:
            success, message = self._handle_client_error(e, "SSM", "PutParameter")
            print(message)
            return success
        except Exception as e:
            print(f"❌ SSM PutParameter permission: Error - {e}")
            return False

    def check_ssm_permissions(self) -> bool:
        """Check SSM Parameter Store permissions"""
        print("\n🔍 Checking SSM Parameter Store permissions...")
        ssm = boto3.client('ssm', region_name=self.region)
        
        get_success = self._test_ssm_get_parameter(ssm)
        put_success = self._test_ssm_put_delete_parameter(ssm)
        
        return get_success and put_success

    def check_bedrock_permissions(self) -> bool:
        """Check Bedrock service permissions"""
        print("\n🔍 Checking Bedrock service permissions...")
        bedrock = boto3.client('bedrock', region_name=self.region)
        
        try:
            response = bedrock.list_foundation_models()
            print("✅ Bedrock ListFoundationModels permission: OK")
            
            # Check if Claude model is available
            claude_models = [model for model in response['modelSummaries'] 
                            if 'claude' in model['modelId'].lower()]
            if claude_models:
                print(f"✅ Claude models available: {len(claude_models)} found")
            else:
                print("⚠️  No Claude models found")
            
            return True
        except ClientError as e:
            success, message = self._handle_client_error(e, "Bedrock", "ListFoundationModels")
            print(message)
            return success
        except Exception as e:
            print(f"❌ Bedrock permission: Error - {e}")
            return False

    def check_bedrock_runtime_permissions(self) -> bool:
        """Check Bedrock Runtime permissions"""
        print("\n🔍 Checking Bedrock Runtime permissions...")
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.region)
        
        try:
            # Test with a simple invoke (this will fail due to validation, but tests permission)
            bedrock_runtime.invoke_model(
                modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "test"}]
                })
            )
            print("✅ Bedrock Runtime InvokeModel permission: OK")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in self.access_denied_codes:
                print("❌ Bedrock Runtime permission: DENIED")
                return False
            elif error_code == 'ValidationException':
                print("✅ Bedrock Runtime InvokeModel permission: OK (validation error expected)")
                return True
            else:
                print(f"⚠️  Bedrock Runtime permission: Unknown error - {e}")
                return True  # Assume OK if not access denied
        except Exception as e:
            print(f"❌ Bedrock Runtime permission: Error - {e}")
            return False

    def _check_existing_memory(self, memories: list, memory_client: MemoryClient) -> bool:
        """Check if DevOpsAgentMemory exists and test GetMemory permission."""
        for memory in memories.get('memories', []):
            if memory.get('name') == 'DevOpsAgentMemory':
                print(f"✅ Found existing DevOpsAgentMemory: {memory.get('id')}")
                
                try:
                    memory_client.gmcp_client.get_memory(memoryId=memory.get('id'))
                    print("✅ AgentCore Memory GetMemory permission: OK")
                    return True
                except Exception as e:
                    print(f"❌ AgentCore Memory GetMemory permission: {e}")
                    return False
        return True

    def check_agentcore_memory_permissions(self) -> bool:
        """Check AgentCore Memory service permissions"""
        print("\n🔍 Checking AgentCore Memory service permissions...")
        
        try:
            memory_client = MemoryClient(region_name=self.region)
            
            try:
                memories = memory_client.gmcp_client.list_memories()
                print("✅ AgentCore Memory ListMemories permission: OK")
                print(f"   Found {len(memories.get('memories', []))} existing memories")
                
                return self._check_existing_memory(memories, memory_client)
                
            except ClientError as e:
                success, message = self._handle_client_error(e, "AgentCore Memory", "ListMemories")
                print(message)
                return success
        except Exception as e:
            print(f"❌ AgentCore Memory service: Error - {e}")
            print("   This might indicate the service is not available in your region")
            return False

    def check_region_availability(self) -> bool:
        """Check current AWS region"""
        print("\n🔍 Checking AWS region...")
        
        if not self.region:
            print("❌ No AWS region configured")
            print("   Set AWS_DEFAULT_REGION environment variable or configure AWS CLI")
            return False
        
        print(f"✅ Current region: {self.region}")
        
        # Check if region supports required services
        supported_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        if self.region not in supported_regions:
            print("⚠️  Warning: Some AWS services might not be available in this region")
            print(f"   Consider using: {', '.join(supported_regions)}")
        
        return True

def main():
    """Main function to run all permission checks"""
    print("🚀 AWS DevOps Agent - Permission Checker")
    print("=" * 50)
    
    checker = PermissionChecker()
    all_checks_passed = True
    
    # Define checks with their methods
    checks = [
        ("AWS Credentials", checker.check_aws_credentials),
        ("Region Availability", checker.check_region_availability),
        ("SSM Permissions", checker.check_ssm_permissions),
        ("Bedrock Permissions", checker.check_bedrock_permissions),
        ("Bedrock Runtime Permissions", checker.check_bedrock_runtime_permissions),
        ("AgentCore Memory Permissions", checker.check_agentcore_memory_permissions),
    ]
    
    for check_name, check_method in checks:
        try:
            if not check_method():
                all_checks_passed = False
        except Exception as e:
            print(f"❌ Unexpected error in {check_name}: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All permission checks passed! Your agent should work correctly.")
    else:
        print("⚠️  Some permission checks failed. Please review the issues above.")
        print("\n📋 Required IAM permissions:")
        print("   SSM: ssm:GetParameter, ssm:PutParameter, ssm:DeleteParameter")
        print("   Bedrock: bedrock:ListFoundationModels, bedrock:InvokeModel")
        print("   AgentCore: bedrock:ListMemories, bedrock:GetMemory, bedrock:CreateMemory")
        print("   STS: sts:GetCallerIdentity")

if __name__ == "__main__":
    main()