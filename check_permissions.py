#!/usr/bin/env python3
"""
Script to check AWS IAM permissions for the DevOps bot
"""
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError
from bedrock_agentcore.memory import MemoryClient

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print("🔍 Checking AWS credentials...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured")
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

def check_ssm_permissions():
    """Check SSM Parameter Store permissions"""
    print("\n🔍 Checking SSM Parameter Store permissions...")
    import os
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    ssm = boto3.client('ssm', region_name=region)
    
    # Test GetParameter permission
    try:
        # Try to get a non-existent parameter to test permission
        ssm.get_parameter(Name='/test/nonexistent/parameter')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            print("✅ SSM GetParameter permission: OK")
        elif e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
            print("❌ SSM GetParameter permission: DENIED")
            return False
        else:
            print(f"⚠️  SSM GetParameter permission: Unknown error - {e}")
    except Exception as e:
        print(f"❌ SSM GetParameter permission: Error - {e}")
        return False
    
    # Test PutParameter permission
    try:
        # Try to put a test parameter
        test_param_name = '/test/permission/check'
        ssm.put_parameter(
            Name=test_param_name,
            Value='test',
            Type='String',
            Overwrite=True
        )
        print("✅ SSM PutParameter permission: OK")
        
        # Clean up test parameter
        try:
            ssm.delete_parameter(Name=test_param_name)
            print("✅ SSM DeleteParameter permission: OK")
        except:
            print("⚠️  Could not clean up test parameter")
        
        return True
    except ClientError as e:
        if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
            print("❌ SSM PutParameter permission: DENIED")
            return False
        else:
            print(f"⚠️  SSM PutParameter permission: Unknown error - {e}")
            return False
    except Exception as e:
        print(f"❌ SSM PutParameter permission: Error - {e}")
        return False

def check_bedrock_permissions():
    """Check Bedrock service permissions"""
    print("\n🔍 Checking Bedrock service permissions...")
    import os
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    bedrock = boto3.client('bedrock', region_name=region)
    
    try:
        # Test basic Bedrock access by listing foundation models
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
        if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
            print("❌ Bedrock permission: DENIED")
            return False
        else:
            print(f"⚠️  Bedrock permission: Unknown error - {e}")
            return False
    except Exception as e:
        print(f"❌ Bedrock permission: Error - {e}")
        return False

def check_bedrock_runtime_permissions():
    """Check Bedrock Runtime permissions"""
    print("\n🔍 Checking Bedrock Runtime permissions...")
    import os
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
    
    try:
        # Test with a simple invoke (this will fail due to no body, but tests permission)
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
        if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
            print("❌ Bedrock Runtime permission: DENIED")
            return False
        elif e.response['Error']['Code'] == 'ValidationException':
            print("✅ Bedrock Runtime InvokeModel permission: OK (validation error expected)")
            return True
        else:
            print(f"⚠️  Bedrock Runtime permission: Unknown error - {e}")
            return True  # Assume OK if not access denied
    except Exception as e:
        print(f"❌ Bedrock Runtime permission: Error - {e}")
        return False

def check_agentcore_memory_permissions():
    """Check AgentCore Memory service permissions"""
    print("\n🔍 Checking AgentCore Memory service permissions...")
    
    try:
        import os
        region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        memory_client = MemoryClient(region_name=region)
        
        # Test list memories permission
        try:
            memories = memory_client.gmcp_client.list_memories()
            print("✅ AgentCore Memory ListMemories permission: OK")
            print(f"   Found {len(memories.get('memories', []))} existing memories")
            
            # Check if our specific memory exists
            for memory in memories.get('memories', []):
                if memory.get('name') == 'DevOpsAgentMemory':
                    print(f"✅ Found existing DevOpsAgentMemory: {memory.get('id')}")
                    
                    # Test get memory permission
                    try:
                        memory_client.gmcp_client.get_memory(memoryId=memory.get('id'))
                        print("✅ AgentCore Memory GetMemory permission: OK")
                    except Exception as e:
                        print(f"❌ AgentCore Memory GetMemory permission: {e}")
                        return False
            
            return True
        except ClientError as e:
            if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                print("❌ AgentCore Memory permission: DENIED")
                return False
            else:
                print(f"⚠️  AgentCore Memory permission: Unknown error - {e}")
                return False
    except Exception as e:
        print(f"❌ AgentCore Memory service: Error - {e}")
        print("   This might indicate the service is not available in your region")
        return False

def check_region_availability():
    """Check current AWS region"""
    print("\n🔍 Checking AWS region...")
    import os
    
    # Check environment variable first
    region = os.environ.get('AWS_DEFAULT_REGION')
    if not region:
        session = boto3.Session()
        region = session.region_name
    
    if not region:
        print("❌ No AWS region configured")
        print("   Set AWS_DEFAULT_REGION environment variable or configure AWS CLI")
        return False
    
    print(f"✅ Current region: {region}")
    
    # Check if region supports required services
    if region not in ['us-east-1', 'us-west-2', 'eu-west-1']:
        print("⚠️  Warning: Some AWS services might not be available in this region")
        print("   Consider using us-east-1, us-west-2, or eu-west-1")
    
    return True

def main():
    """Main function to run all permission checks"""
    print("🚀 AWS DevOps Bot - Permission Checker")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        check_aws_credentials,
        check_region_availability,
        check_ssm_permissions,
        check_bedrock_permissions,
        check_bedrock_runtime_permissions,
        check_agentcore_memory_permissions,
    ]
    
    for check in checks:
        try:
            if not check():
                all_checks_passed = False
        except Exception as e:
            print(f"❌ Unexpected error in {check.__name__}: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All permission checks passed! Your bot should work correctly.")
    else:
        print("⚠️  Some permission checks failed. Please review the issues above.")
        print("\n📋 Required IAM permissions:")
        print("   SSM: ssm:GetParameter, ssm:PutParameter, ssm:DeleteParameter")
        print("   Bedrock: bedrock:ListFoundationModels, bedrock:InvokeModel")
        print("   AgentCore: bedrock:ListMemories, bedrock:GetMemory, bedrock:CreateMemory")
        print("   STS: sts:GetCallerIdentity")

if __name__ == "__main__":
    main()