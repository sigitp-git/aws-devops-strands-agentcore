"""
CloudWatch MCP Server as Lambda Function
"""
import json
import logging
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CloudWatchServer:
    """CloudWatch operations."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
    
    def describe_log_groups(self, log_group_name_prefix: Optional[str] = None, 
                           max_items: Optional[int] = None) -> List[Dict[str, Any]]:
        """List CloudWatch log groups."""
        try:
            kwargs = {}
            if log_group_name_prefix:
                kwargs['logGroupNamePrefix'] = log_group_name_prefix
            if max_items:
                kwargs['limit'] = max_items
            
            response = self.logs_client.describe_log_groups(**kwargs)
            return response.get('logGroups', [])
            
        except Exception as e:
            logger.error(f"Failed to describe log groups: {e}")
            return []
    
    def execute_log_insights_query(self, log_group_names: List[str], query_string: str,
                                  start_time: str, end_time: str, limit: Optional[int] = None,
                                  max_timeout: int = 30) -> Dict[str, Any]:
        """Execute CloudWatch Logs Insights query."""
        try:
            # Convert time strings to timestamps
            start_timestamp = int(datetime.fromisoformat(start_time.replace('Z', '+00:00')).timestamp())
            end_timestamp = int(datetime.fromisoformat(end_time.replace('Z', '+00:00')).timestamp())
            
            # Start query
            kwargs = {
                'logGroupNames': log_group_names,
                'startTime': start_timestamp,
                'endTime': end_timestamp,
                'queryString': query_string
            }
            if limit:
                kwargs['limit'] = limit
            
            response = self.logs_client.start_query(**kwargs)
            query_id = response['queryId']
            
            # Poll for results
            timeout = time.time() + max_timeout
            while time.time() < timeout:
                result = self.logs_client.get_query_results(queryId=query_id)
                status = result['status']
                
                if status == 'Complete':
                    return {
                        'status': status,
                        'results': result.get('results', []),
                        'statistics': result.get('statistics', {}),
                        'query_id': query_id
                    }
                elif status == 'Failed':
                    return {
                        'status': status,
                        'error': 'Query failed',
                        'query_id': query_id
                    }
                
                time.sleep(1)
            
            # Timeout reached
            return {
                'status': 'Timeout',
                'query_id': query_id,
                'message': f'Query did not complete within {max_timeout} seconds'
            }
            
        except Exception as e:
            logger.error(f"Failed to execute log insights query: {e}")
            return {
                'status': 'Error',
                'error': str(e)
            }
    
    def get_metric_data(self, namespace: str, metric_name: str, start_time: str,
                       end_time: Optional[str] = None, dimensions: Optional[List[Dict]] = None,
                       statistic: str = "Average", target_datapoints: int = 60) -> Dict[str, Any]:
        """Get CloudWatch metric data."""
        try:
            # Convert time strings
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if end_time:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                end_dt = datetime.utcnow()
            
            # Calculate period
            duration = (end_dt - start_dt).total_seconds()
            period = max(60, int(duration / target_datapoints))
            
            # Build metric query
            metric_stat = {
                'Metric': {
                    'Namespace': namespace,
                    'MetricName': metric_name
                },
                'Period': period,
                'Stat': statistic
            }
            
            if dimensions:
                metric_stat['Metric']['Dimensions'] = [
                    {'Name': d['name'], 'Value': d['value']} for d in dimensions
                ]
            
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=[{
                    'Id': 'm1',
                    'MetricStat': metric_stat,
                    'ReturnData': True
                }],
                StartTime=start_dt,
                EndTime=end_dt
            )
            
            results = response.get('MetricDataResults', [])
            if results:
                result = results[0]
                return {
                    'metric_name': metric_name,
                    'namespace': namespace,
                    'timestamps': [ts.isoformat() for ts in result.get('Timestamps', [])],
                    'values': result.get('Values', []),
                    'label': result.get('Label', ''),
                    'status_code': result.get('StatusCode', '')
                }
            else:
                return {
                    'metric_name': metric_name,
                    'namespace': namespace,
                    'timestamps': [],
                    'values': [],
                    'message': 'No data found'
                }
                
        except Exception as e:
            logger.error(f"Failed to get metric data: {e}")
            return {
                'metric_name': metric_name,
                'namespace': namespace,
                'error': str(e)
            }
    
    def get_active_alarms(self, max_items: Optional[int] = 50) -> Dict[str, Any]:
        """Get alarms currently in ALARM state."""
        try:
            kwargs = {
                'StateValue': 'ALARM'
            }
            if max_items:
                kwargs['MaxRecords'] = max_items
            
            response = self.cloudwatch.describe_alarms(**kwargs)
            
            metric_alarms = []
            composite_alarms = []
            
            for alarm in response.get('MetricAlarms', []):
                metric_alarms.append({
                    'alarm_name': alarm.get('AlarmName'),
                    'alarm_description': alarm.get('AlarmDescription'),
                    'state_reason': alarm.get('StateReason'),
                    'state_updated_timestamp': alarm.get('StateUpdatedTimestamp').isoformat() if alarm.get('StateUpdatedTimestamp') else None,
                    'metric_name': alarm.get('MetricName'),
                    'namespace': alarm.get('Namespace'),
                    'statistic': alarm.get('Statistic'),
                    'threshold': alarm.get('Threshold')
                })
            
            for alarm in response.get('CompositeAlarms', []):
                composite_alarms.append({
                    'alarm_name': alarm.get('AlarmName'),
                    'alarm_description': alarm.get('AlarmDescription'),
                    'state_reason': alarm.get('StateReason'),
                    'state_updated_timestamp': alarm.get('StateUpdatedTimestamp').isoformat() if alarm.get('StateUpdatedTimestamp') else None,
                    'alarm_rule': alarm.get('AlarmRule')
                })
            
            return {
                'metric_alarms': metric_alarms,
                'composite_alarms': composite_alarms,
                'total_alarms': len(metric_alarms) + len(composite_alarms)
            }
            
        except Exception as e:
            logger.error(f"Failed to get active alarms: {e}")
            return {
                'metric_alarms': [],
                'composite_alarms': [],
                'error': str(e)
            }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for CloudWatch MCP server."""
    try:
        operation = event.get('operation', 'describe_log_groups')
        parameters = event.get('parameters', {})
        region = parameters.get('region', 'us-east-1')
        
        server = CloudWatchServer(region=region)
        
        if operation == 'describe_log_groups':
            log_group_name_prefix = parameters.get('log_group_name_prefix')
            max_items = parameters.get('max_items')
            
            results = server.describe_log_groups(log_group_name_prefix, max_items)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'log_groups': results,
                    'region': region
                }, default=str)
            }
        
        elif operation == 'execute_log_insights_query':
            log_group_names = parameters.get('log_group_names', [])
            query_string = parameters.get('query_string', '')
            start_time = parameters.get('start_time', '')
            end_time = parameters.get('end_time', '')
            limit = parameters.get('limit')
            max_timeout = parameters.get('max_timeout', 30)
            
            if not all([log_group_names, query_string, start_time, end_time]):
                raise ValueError("log_group_names, query_string, start_time, and end_time are required")
            
            results = server.execute_log_insights_query(
                log_group_names, query_string, start_time, end_time, limit, max_timeout
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'query_results': results,
                    'region': region
                }, default=str)
            }
        
        elif operation == 'get_metric_data':
            namespace = parameters.get('namespace', '')
            metric_name = parameters.get('metric_name', '')
            start_time = parameters.get('start_time', '')
            end_time = parameters.get('end_time')
            dimensions = parameters.get('dimensions', [])
            statistic = parameters.get('statistic', 'Average')
            target_datapoints = parameters.get('target_datapoints', 60)
            
            if not all([namespace, metric_name, start_time]):
                raise ValueError("namespace, metric_name, and start_time are required")
            
            results = server.get_metric_data(
                namespace, metric_name, start_time, end_time, dimensions, statistic, target_datapoints
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'metric_data': results,
                    'region': region
                }, default=str)
            }
        
        elif operation == 'get_active_alarms':
            max_items = parameters.get('max_items', 50)
            
            results = server.get_active_alarms(max_items)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'alarms': results,
                    'region': region
                }, default=str)
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"CloudWatch Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }