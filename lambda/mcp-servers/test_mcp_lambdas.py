#!/usr/bin/env python3
"""
Test MCP Lambda Functions
"""
import json
import boto3
import sys
from typing import Dict, Any, List
import time

class MCPLambdaTester:
    """Test deployed MCP Lambda functions."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.test_results = []
    
    def test_function(self, function_name: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test a Lambda function with multiple test cases."""
        print(f"\n🧪 Testing {function_name}")
        print("=" * 50)
        
        function_results = {
            'function_name': function_name,
            'test_cases': [],
            'success_count': 0,
            'total_tests': len(test_cases)
        }
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"  Test {i}: {test_case.get('description', 'No description')}")
            
            try:
                # Invoke Lambda function
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_case['payload'])
                )
                
                # Parse response
                response_payload = json.loads(response['Payload'].read())
                status_code = response_payload.get('statusCode', 500)
                
                # Check if test passed
                success = status_code == 200
                if success:
                    function_results['success_count'] += 1
                    print(f"    ✅ PASSED")
                else:
                    print(f"    ❌ FAILED - Status: {status_code}")
                    if 'body' in response_payload:
                        body = json.loads(response_payload['body'])
                        if 'error' in body:
                            print(f"    Error: {body['error']}")
                
                # Store result
                test_result = {
                    'test_number': i,
                    'description': test_case.get('description', ''),
                    'success': success,
                    'status_code': status_code,
                    'response': response_payload
                }
                function_results['test_cases'].append(test_result)
                
            except Exception as e:
                print(f"    ❌ FAILED - Exception: {e}")
                function_results['test_cases'].append({
                    'test_number': i,
                    'description': test_case.get('description', ''),
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        success_rate = (function_results['success_count'] / function_results['total_tests']) * 100
        print(f"  📊 Results: {function_results['success_count']}/{function_results['total_tests']} ({success_rate:.1f}%)")
        
        return function_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all MCP Lambda functions."""
        print("🚀 Starting MCP Lambda Function Tests")
        print("=" * 60)
        
        # Test Core Server
        core_tests = [
            {
                'description': 'Test prompt understanding',
                'payload': {
                    'operation': 'prompt_understanding',
                    'parameters': {}
                }
            },
            {
                'description': 'Test AWS context',
                'payload': {
                    'operation': 'get_aws_context',
                    'parameters': {}
                }
            },
            {
                'description': 'Test system status',
                'payload': {
                    'operation': 'get_system_status',
                    'parameters': {}
                }
            }
        ]
        
        core_result = self.test_function('mcp-core-server', core_tests)
        self.test_results.append(core_result)
        
        # Test AWS Documentation Server
        docs_tests = [
            {
                'description': 'Search AWS documentation',
                'payload': {
                    'operation': 'search_documentation',
                    'parameters': {
                        'query': 'S3 bucket',
                        'limit': 5
                    }
                }
            },
            {
                'description': 'Read documentation (mock)',
                'payload': {
                    'operation': 'read_documentation',
                    'parameters': {
                        'url': 'https://docs.aws.amazon.com/s3/latest/userguide/creating-bucket.html',
                        'max_length': 1000
                    }
                }
            }
        ]
        
        docs_result = self.test_function('mcp-aws-documentation-server', docs_tests)
        self.test_results.append(docs_result)
        
        # Test AWS Pricing Server
        pricing_tests = [
            {
                'description': 'Get pricing service codes',
                'payload': {
                    'operation': 'get_pricing_service_codes',
                    'parameters': {}
                }
            },
            {
                'description': 'Get service attributes',
                'payload': {
                    'operation': 'get_pricing_service_attributes',
                    'parameters': {
                        'service_code': 'AmazonEC2'
                    }
                }
            }
        ]
        
        pricing_result = self.test_function('mcp-aws-pricing-server', pricing_tests)
        self.test_results.append(pricing_result)
        
        # Test CloudWatch Server
        cloudwatch_tests = [
            {
                'description': 'Describe log groups',
                'payload': {
                    'operation': 'describe_log_groups',
                    'parameters': {
                        'max_items': 5
                    }
                }
            },
            {
                'description': 'Get active alarms',
                'payload': {
                    'operation': 'get_active_alarms',
                    'parameters': {
                        'max_items': 10
                    }
                }
            }
        ]
        
        cloudwatch_result = self.test_function('mcp-cloudwatch-server', cloudwatch_tests)
        self.test_results.append(cloudwatch_result)
        
        # Test EKS Server
        eks_tests = [
            {
                'description': 'List EKS clusters',
                'payload': {
                    'operation': 'list_clusters',
                    'parameters': {}
                }
            }
        ]
        
        eks_result = self.test_function('mcp-eks-server', eks_tests)
        self.test_results.append(eks_result)
        
        # Test Terraform Server
        terraform_tests = [
            {
                'description': 'Search AWS provider docs',
                'payload': {
                    'operation': 'search_aws_provider_docs',
                    'parameters': {
                        'asset_name': 'aws_s3_bucket',
                        'asset_type': 'resource'
                    }
                }
            },
            {
                'description': 'Generate Terraform template',
                'payload': {
                    'operation': 'generate_terraform_template',
                    'parameters': {
                        'resource_type': 'aws_s3_bucket',
                        'resource_name': 'example_bucket',
                        'properties': {
                            'bucket': 'my-example-bucket',
                            'force_destroy': True
                        }
                    }
                }
            }
        ]
        
        terraform_result = self.test_function('mcp-terraform-server', terraform_tests)
        self.test_results.append(terraform_result)
        
        # Test Git Repository Research Server
        git_tests = [
            {
                'description': 'Search GitHub repositories',
                'payload': {
                    'operation': 'search_repos_on_github',
                    'parameters': {
                        'keywords': ['aws', 'lambda'],
                        'num_results': 3
                    }
                }
            },
            {
                'description': 'Access file (mock)',
                'payload': {
                    'operation': 'access_file',
                    'parameters': {
                        'filepath': 'test-repo/repository/README.md'
                    }
                }
            }
        ]
        
        git_result = self.test_function('mcp-git-repo-research-server', git_tests)
        self.test_results.append(git_result)
        
        # Test Frontend Server
        frontend_tests = [
            {
                'description': 'Get React documentation',
                'payload': {
                    'operation': 'get_react_docs_by_topic',
                    'parameters': {
                        'topic': 'essential-knowledge'
                    }
                }
            },
            {
                'description': 'Generate React component',
                'payload': {
                    'operation': 'generate_react_component',
                    'parameters': {
                        'component_name': 'TestComponent',
                        'component_type': 'functional',
                        'props': ['title', 'description']
                    }
                }
            }
        ]
        
        frontend_result = self.test_function('mcp-frontend-server', frontend_tests)
        self.test_results.append(frontend_result)
        
        # Test AWS Location Server
        location_tests = [
            {
                'description': 'Reverse geocode coordinates',
                'payload': {
                    'operation': 'reverse_geocode',
                    'parameters': {
                        'longitude': -122.4194,
                        'latitude': 37.7749
                    }
                }
            }
        ]
        
        location_result = self.test_function('mcp-aws-location-server', location_tests)
        self.test_results.append(location_result)
        
        return self.generate_summary()
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test summary."""
        total_functions = len(self.test_results)
        total_tests = sum(result['total_tests'] for result in self.test_results)
        total_successes = sum(result['success_count'] for result in self.test_results)
        
        success_rate = (total_successes / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n🎉 Test Summary")
        print("=" * 60)
        print(f"Functions Tested: {total_functions}")
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {total_successes}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📊 Function Results:")
        for result in self.test_results:
            function_success_rate = (result['success_count'] / result['total_tests']) * 100
            status = "✅" if function_success_rate == 100 else "⚠️" if function_success_rate >= 50 else "❌"
            print(f"  {status} {result['function_name']}: {result['success_count']}/{result['total_tests']} ({function_success_rate:.1f}%)")
        
        return {
            'total_functions': total_functions,
            'total_tests': total_tests,
            'total_successes': total_successes,
            'success_rate': success_rate,
            'function_results': self.test_results
        }

def main():
    """Main test function."""
    print("🧪 MCP Lambda Function Test Suite")
    print("=" * 60)
    
    try:
        tester = MCPLambdaTester()
        summary = tester.run_all_tests()
        
        # Save results to file
        with open('mcp_lambda_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved to: mcp_lambda_test_results.json")
        
        # Exit with appropriate code
        if summary['success_rate'] == 100:
            print(f"\n🎉 All tests passed!")
            sys.exit(0)
        elif summary['success_rate'] >= 80:
            print(f"\n⚠️  Most tests passed, but some issues found.")
            sys.exit(1)
        else:
            print(f"\n❌ Many tests failed. Please check the deployment.")
            sys.exit(2)
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()