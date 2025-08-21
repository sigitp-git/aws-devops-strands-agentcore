#!/usr/bin/env python3
"""
Local testing script for the AgentCore Runtime version.
Tests the runtime endpoints before deployment.
"""

import requests
import json
import time
import subprocess
import sys
import os
import threading
from datetime import datetime

class RuntimeTester:
    """Test the runtime version locally."""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.server_process = None
    
    def start_server(self):
        """Start the runtime server in background."""
        try:
            print("🚀 Starting runtime server...")
            self.server_process = subprocess.Popen(
                [sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_runtime.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{self.base_url}/ping", timeout=2)
                    if response.status_code == 200:
                        print("✅ Server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
            
            print("❌ Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the runtime server."""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ Server stopped")
    
    def test_ping_endpoint(self):
        """Test the /ping health check endpoint."""
        try:
            print("\n🏥 Testing /ping endpoint...")
            response = requests.get(f"{self.base_url}/ping", timeout=10)
            
            if response.status_code == 200:
                print("✅ /ping endpoint working")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ /ping endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ /ping test failed: {e}")
            return False
    
    def test_invocations_endpoint(self):
        """Test the /invocations endpoint with various payloads."""
        test_cases = [
            {
                "name": "Basic greeting",
                "payload": {"prompt": "Hello! Can you help me with AWS?"}
            },
            {
                "name": "DevOps question",
                "payload": {"prompt": "What are AWS best practices for EC2 security?"}
            },
            {
                "name": "Web search request",
                "payload": {"prompt": "Search for the latest AWS Lambda pricing updates"}
            },
            {
                "name": "Empty prompt (error case)",
                "payload": {}
            },
            {
                "name": "Invalid payload (error case)",
                "payload": {"invalid": "data"}
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                print(f"\n🧪 Testing: {test_case['name']}")
                
                response = requests.post(
                    f"{self.base_url}/invocations",
                    json=test_case['payload'],
                    headers={"Content-Type": "application/json"},
                    timeout=60  # Longer timeout for agent processing
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if "error" in response_data:
                        print(f"⚠️  Expected error: {response_data['error']}")
                        results.append({"test": test_case['name'], "status": "expected_error"})
                    else:
                        message = response_data.get('message', 'No message')
                        print(f"✅ Success: {message[:100]}...")
                        results.append({"test": test_case['name'], "status": "success"})
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    results.append({"test": test_case['name'], "status": "http_error"})
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                results.append({"test": test_case['name'], "status": "exception"})
        
        return results
    
    def test_concurrent_requests(self):
        """Test concurrent requests to check stability."""
        print("\n🔄 Testing concurrent requests...")
        
        def make_request(request_id):
            try:
                payload = {"prompt": f"Request {request_id}: What is AWS?"}
                response = requests.post(
                    f"{self.base_url}/invocations",
                    json=payload,
                    timeout=30
                )
                return {"id": request_id, "status": response.status_code, "success": response.status_code == 200}
            except Exception as e:
                return {"id": request_id, "status": "error", "error": str(e), "success": False}
        
        # Create 3 concurrent requests
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda i=i: results.append(make_request(i)))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        successful = sum(1 for r in results if r.get('success', False))
        print(f"✅ Concurrent test: {successful}/3 requests successful")
        
        return results
    
    def run_all_tests(self):
        """Run all tests."""
        print("🧪 DevOps Agent Runtime Local Testing")
        print("=" * 50)
        
        # Start server
        if not self.start_server():
            return False
        
        try:
            # Test ping
            ping_success = self.test_ping_endpoint()
            
            # Test invocations
            invocation_results = self.test_invocations_endpoint()
            
            # Test concurrent requests
            concurrent_results = self.test_concurrent_requests()
            
            # Summary
            print("\n📊 Test Summary")
            print("=" * 30)
            print(f"Ping endpoint: {'✅ Pass' if ping_success else '❌ Fail'}")
            
            successful_invocations = sum(1 for r in invocation_results if r['status'] in ['success', 'expected_error'])
            print(f"Invocation tests: ✅ {successful_invocations}/{len(invocation_results)} passed")
            
            successful_concurrent = sum(1 for r in concurrent_results if r.get('success', False))
            print(f"Concurrent tests: ✅ {successful_concurrent}/{len(concurrent_results)} passed")
            
            overall_success = ping_success and successful_invocations == len(invocation_results)
            
            if overall_success:
                print("\n🎉 All tests passed! Runtime is ready for deployment.")
            else:
                print("\n⚠️  Some tests failed. Check the output above.")
            
            return overall_success
            
        finally:
            self.stop_server()

def main():
    """Main testing function."""
    tester = RuntimeTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n💡 Next steps:")
        print("   1. Run 'python deploy_runtime.py' to deploy to AgentCore Runtime")
        print("   2. Or use 'docker build -f Dockerfile.runtime -t devops-agent .' for manual deployment")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Please fix issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()