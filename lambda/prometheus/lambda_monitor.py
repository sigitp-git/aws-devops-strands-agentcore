#!/usr/bin/env python3
"""
AWS Lambda function for monitoring Prometheus Lambda functions performance.

This function monitors the health, performance, and usage metrics of all
Prometheus Lambda functions, providing insights into:
- Function execution times and success rates
- Error patterns and troubleshooting information
- Cost analysis and optimization recommendations
- Usage patterns and scaling insights

Features:
- CloudWatch metrics analysis for all Prometheus functions
- Performance benchmarking and comparison
- Error rate monitoring and alerting
- Cost optimization recommendations
- Health check dashboard data
"""

import json
import boto3
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import statistics

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class PrometheusLambdaMonitor:
    """Monitor for Prometheus Lambda functions."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize the monitor.
        
        Args:
            region: AWS region
        """
        self.region = region
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
        # Function names to monitor
        self.function_names = [
            "aws-devops-prometheus-query",
            "aws-devops-prometheus-range-query",
            "aws-devops-prometheus-list-metrics",
            "aws-devops-prometheus-server-info",
            "aws-devops-prometheus-find-workspace",
            "aws-devops-prometheus-integration"
        ]
    
    def get_function_metrics(self, function_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for a specific function.
        
        Args:
            function_name: Name of the Lambda function
            hours: Number of hours to look back
            
        Returns:
            Dictionary containing metrics data
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        metrics = {}
        
        try:
            # Get invocation count
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            invocations = [point['Sum'] for point in response['Datapoints']]
            metrics['invocations'] = {
                'total': sum(invocations),
                'hourly_average': statistics.mean(invocations) if invocations else 0,
                'peak_hour': max(invocations) if invocations else 0
            }
            
            # Get error count
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            errors = [point['Sum'] for point in response['Datapoints']]
            total_errors = sum(errors)
            total_invocations = metrics['invocations']['total']
            
            metrics['errors'] = {
                'total': total_errors,
                'error_rate': (total_errors / total_invocations * 100) if total_invocations > 0 else 0
            }
            
            # Get duration metrics
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            if response['Datapoints']:
                durations_avg = [point['Average'] for point in response['Datapoints']]
                durations_max = [point['Maximum'] for point in response['Datapoints']]
                
                metrics['duration'] = {
                    'average_ms': statistics.mean(durations_avg) if durations_avg else 0,
                    'max_ms': max(durations_max) if durations_max else 0,
                    'p95_ms': statistics.quantiles(durations_avg, n=20)[18] if len(durations_avg) > 5 else 0
                }
            else:
                metrics['duration'] = {
                    'average_ms': 0,
                    'max_ms': 0,
                    'p95_ms': 0
                }
            
            # Get throttle count
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Throttles',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            throttles = [point['Sum'] for point in response['Datapoints']]
            metrics['throttles'] = {
                'total': sum(throttles),
                'throttle_rate': (sum(throttles) / total_invocations * 100) if total_invocations > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics for {function_name}: {str(e)}")
            metrics['error'] = str(e)
        
        return metrics
    
    def get_function_configuration(self, function_name: str) -> Dict[str, Any]:
        """
        Get function configuration details.
        
        Args:
            function_name: Name of the Lambda function
            
        Returns:
            Function configuration
        """
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            config = response['Configuration']
            
            return {
                'memory_size': config['MemorySize'],
                'timeout': config['Timeout'],
                'runtime': config['Runtime'],
                'code_size': config['CodeSize'],
                'last_modified': config['LastModified'],
                'state': config['State']
            }
        except Exception as e:
            logger.error(f"Error getting configuration for {function_name}: {str(e)}")
            return {'error': str(e)}
    
    def analyze_performance(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze performance of all Prometheus Lambda functions.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance analysis report
        """
        report = {
            'analysis_period': f"{hours} hours",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'functions': {},
            'summary': {},
            'recommendations': []
        }
        
        all_metrics = {}
        
        # Collect metrics for all functions
        for function_name in self.function_names:
            logger.info(f"Analyzing function: {function_name}")
            
            metrics = self.get_function_metrics(function_name, hours)
            config = self.get_function_configuration(function_name)
            
            all_metrics[function_name] = metrics
            
            report['functions'][function_name] = {
                'metrics': metrics,
                'configuration': config,
                'health_status': self._assess_health(metrics, config)
            }
        
        # Generate summary
        report['summary'] = self._generate_summary(all_metrics)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report['functions'])
        
        return report
    
    def _assess_health(self, metrics: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Assess the health status of a function.
        
        Args:
            metrics: Function metrics
            config: Function configuration
            
        Returns:
            Health status (healthy, warning, critical)
        """
        if 'error' in metrics or 'error' in config:
            return 'critical'
        
        error_rate = metrics.get('errors', {}).get('error_rate', 0)
        throttle_rate = metrics.get('throttles', {}).get('throttle_rate', 0)
        avg_duration = metrics.get('duration', {}).get('average_ms', 0)
        timeout = config.get('timeout', 30) * 1000  # Convert to ms
        
        # Critical conditions
        if error_rate > 5 or throttle_rate > 1 or avg_duration > (timeout * 0.8):
            return 'critical'
        
        # Warning conditions
        if error_rate > 1 or throttle_rate > 0.1 or avg_duration > (timeout * 0.5):
            return 'warning'
        
        return 'healthy'
    
    def _generate_summary(self, all_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics across all functions.
        
        Args:
            all_metrics: Metrics for all functions
            
        Returns:
            Summary statistics
        """
        total_invocations = 0
        total_errors = 0
        durations = []
        
        for function_name, metrics in all_metrics.items():
            if 'error' not in metrics:
                total_invocations += metrics.get('invocations', {}).get('total', 0)
                total_errors += metrics.get('errors', {}).get('total', 0)
                avg_duration = metrics.get('duration', {}).get('average_ms', 0)
                if avg_duration > 0:
                    durations.append(avg_duration)
        
        return {
            'total_invocations': total_invocations,
            'total_errors': total_errors,
            'overall_error_rate': (total_errors / total_invocations * 100) if total_invocations > 0 else 0,
            'average_duration_ms': statistics.mean(durations) if durations else 0,
            'functions_monitored': len(self.function_names)
        }
    
    def _generate_recommendations(self, functions: Dict[str, Any]) -> List[str]:
        """
        Generate optimization recommendations.
        
        Args:
            functions: Function analysis data
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        for function_name, data in functions.items():
            metrics = data.get('metrics', {})
            config = data.get('configuration', {})
            health = data.get('health_status', 'unknown')
            
            if health == 'critical':
                error_rate = metrics.get('errors', {}).get('error_rate', 0)
                if error_rate > 5:
                    recommendations.append(f"🚨 {function_name}: High error rate ({error_rate:.1f}%) - investigate logs and error patterns")
                
                throttle_rate = metrics.get('throttles', {}).get('throttle_rate', 0)
                if throttle_rate > 1:
                    recommendations.append(f"🚨 {function_name}: High throttle rate ({throttle_rate:.1f}%) - consider increasing concurrency limits")
                
                avg_duration = metrics.get('duration', {}).get('average_ms', 0)
                timeout = config.get('timeout', 30) * 1000
                if avg_duration > (timeout * 0.8):
                    recommendations.append(f"🚨 {function_name}: Duration approaching timeout ({avg_duration:.0f}ms vs {timeout}ms) - optimize code or increase timeout")
            
            elif health == 'warning':
                recommendations.append(f"⚠️ {function_name}: Performance degradation detected - monitor closely")
            
            # Memory optimization
            memory_size = config.get('memory_size', 0)
            avg_duration = metrics.get('duration', {}).get('average_ms', 0)
            if memory_size < 512 and avg_duration > 5000:
                recommendations.append(f"💡 {function_name}: Consider increasing memory from {memory_size}MB to improve performance")
            
            # Cost optimization
            invocations = metrics.get('invocations', {}).get('total', 0)
            if invocations == 0:
                recommendations.append(f"💰 {function_name}: No invocations in analysis period - consider removing if unused")
        
        if not recommendations:
            recommendations.append("✅ All functions are performing well - no immediate action required")
        
        return recommendations

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for the monitoring function.
    
    Expected event format:
    {
        "hours": 24,  // Optional: hours to analyze (default: 24)
        "region": "us-east-1"  // Optional: AWS region
    }
    """
    try:
        # Extract parameters
        hours = event.get('hours', 24)
        region = event.get('region', 'us-east-1')
        
        # Initialize monitor
        monitor = PrometheusLambdaMonitor(region)
        
        # Perform analysis
        report = monitor.analyze_performance(hours)
        
        return {
            'statusCode': 200,
            'body': report
        }
        
    except Exception as e:
        logger.error(f"Monitoring error: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'message': 'Monitoring function error'
        }

# Example usage
if __name__ == "__main__":
    # Example usage of the monitoring function
    monitor = PrometheusLambdaMonitor()
    
    print("Analyzing Prometheus Lambda functions performance...")
    report = monitor.analyze_performance(24)
    
    print(json.dumps(report, indent=2, default=str))