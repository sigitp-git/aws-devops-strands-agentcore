#!/usr/bin/env python3
"""
Script to invoke the deployed DevOps Agent in Amazon Bedrock AgentCore Runtime.
"""

import boto3
import json
import time
import uuid
from datetime import datetime
from utils import get_ssm_parameter

class AgentRuntimeInvoker:
    """Invoke the deployed agent runtime."""
    
    def __init__(self, region="us-east-1"):
        self.region = region
        self.client = boto3.client('bedrock-agentcore', region_name=region)
        
    def get_agent_runtime_arn(self):
        """Get the agent runtime ARN from SSM or user input."""
        # Try SSM first
        arn = get_ssm_parameter("/app/devopsagent/agentcore/runtime_arn")
        
        if arn:
            print(f"✅ Using agent runtime ARN from SSM: {arn}")
            return arn
        
        # Ask user for ARN
        print("⚠️  No agent runtime ARN found in SSM parameter: /app/devopsagent/agentcore/runtime_arn")
        arn = input("Enter agent runtime ARN: ").strip()
        
        if not arn:
            print("❌ No ARN provided")
            return None
        
        return arn
    
    def invoke_agent(self, prompt, session_id=None):
        """Invoke the agent with a prompt."""
        try:
            agent_runtime_arn = self.get_agent_runtime_arn()
            if not agent_runtime_arn:
                return None
            
            if not session_id:
                session_id = f"session-{uuid.uuid4()}"
            
            # Prepare payload
            payload = {
                "prompt": prompt,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"🚀 Invoking agent...")
            print(f"   Prompt: {prompt}")
            print(f"   Session: {session_id}")
            
            # Invoke the agent
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=agent_runtime_arn,
                runtimeSessionId=session_id,
                payload=json.dumps(payload).encode('utf-8'),
                qualifier="DEFAULT"
            )
            
            # Parse response
            response_body = response['response'].read()
            response_data = json.loads(response_body)
            
            print(f"✅ Response received:")
            
            if "error" in response_data:
                print(f"❌ Error: {response_data['error']}")
                return response_data
            
            message = response_data.get('message', 'No message')
            print(f"💬 Message: {message}")
            
            # Show additional info
            if 'tools_used' in response_data:
                print(f"🔧 Tools used: {', '.join(response_data['tools_used'])}")
            
            if 'timestamp' in response_data:
                print(f"⏰ Timestamp: {response_data['timestamp']}")
            
            return response_data
            
        except Exception as e:
            print(f"❌ Invocation failed: {e}")
            return None
    
    def interactive_mode(self):
        """Interactive chat mode with the agent."""
        print("🤖 DevOps Agent Interactive Mode")
        print("=" * 40)
        print("Type 'quit' or 'exit' to end the session")
        print("Type 'help' for usage tips")
        print()
        
        session_id = f"interactive-{int(time.time())}"
        
        while True:
            try:
                prompt = input("You: ").strip()
                
                if prompt.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if prompt.lower() == 'help':
                    self.show_help()
                    continue
                
                if not prompt:
                    continue
                
                print()
                response = self.invoke_agent(prompt, session_id)
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show help information."""
        print("""
💡 DevOps Agent Help:

Example prompts:
• "What are AWS best practices for EC2 security?"
• "How do I set up a CI/CD pipeline with CodePipeline?"
• "Search for the latest AWS Lambda pricing updates"
• "Help me troubleshoot a CloudFormation stack error"
• "What's the difference between ALB and NLB?"

Features:
• Web search for current information
• Memory of conversation context
• AWS expertise and best practices
• DevOps workflow guidance

Commands:
• 'quit' or 'exit' - End session
• 'help' - Show this help
        """)
    
    def run_test_scenarios(self):
        """Run predefined test scenarios."""
        test_scenarios = [
            {
                "name": "Basic AWS Question",
                "prompt": "What is Amazon S3 and what are its main use cases?"
            },
            {
                "name": "DevOps Best Practices",
                "prompt": "What are the key principles of Infrastructure as Code?"
            },
            {
                "name": "Web Search Test",
                "prompt": "Search for the latest AWS re:Invent 2024 announcements"
            },
            {
                "name": "Troubleshooting Help",
                "prompt": "My EC2 instance is running slowly. What should I check?"
            }
        ]
        
        print("🧪 Running Test Scenarios")
        print("=" * 30)
        
        session_id = f"test-{int(time.time())}"
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Test {i}: {scenario['name']}")
            print("-" * 40)
            
            response = self.invoke_agent(scenario['prompt'], session_id)
            
            if response and 'error' not in response:
                results.append({"test": scenario['name'], "status": "success"})
                print("✅ Test passed")
            else:
                results.append({"test": scenario['name'], "status": "failed"})
                print("❌ Test failed")
        
        # Summary
        print(f"\n📊 Test Results Summary")
        print("=" * 30)
        successful = sum(1 for r in results if r['status'] == 'success')
        print(f"Passed: {successful}/{len(results)} tests")
        
        for result in results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_icon} {result['test']}")

def main():
    """Main function."""
    import sys
    
    invoker = AgentRuntimeInvoker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            invoker.run_test_scenarios()
        elif command == 'interactive':
            invoker.interactive_mode()
        elif command == 'invoke':
            if len(sys.argv) > 2:
                prompt = ' '.join(sys.argv[2:])
                invoker.invoke_agent(prompt)
            else:
                print("❌ Please provide a prompt: python invoke_runtime.py invoke 'your prompt here'")
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python invoke_runtime.py [test|interactive|invoke 'prompt']")
    else:
        # Default to interactive mode
        invoker.interactive_mode()

if __name__ == "__main__":
    main()