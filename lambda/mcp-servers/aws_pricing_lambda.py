"""
AWS Pricing MCP Server as Lambda Function
"""
import json
import logging
import boto3
from typing import Dict, Any, List, Optional
from decimal import Decimal
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class AWSPricingServer:
    """AWS Pricing service operations."""
    
    def __init__(self, region: str = "us-east-1"):
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')  # Pricing API only in us-east-1
        self.region = region
    
    def get_pricing_service_codes(self) -> List[str]:
        """Get all available AWS service codes."""
        try:
            response = self.pricing_client.describe_services()
            services = response.get('Services', [])
            return [service['ServiceCode'] for service in services]
        except Exception as e:
            logger.error(f"Failed to get service codes: {e}")
            return []
    
    def get_pricing_service_attributes(self, service_code: str) -> List[str]:
        """Get filterable attributes for a service."""
        try:
            response = self.pricing_client.describe_services(ServiceCode=service_code)
            services = response.get('Services', [])
            if not services:
                return []
            
            attributes = services[0].get('AttributeNames', [])
            return attributes
        except Exception as e:
            logger.error(f"Failed to get service attributes for {service_code}: {e}")
            return []
    
    def get_pricing_attribute_values(self, service_code: str, attribute_names: List[str]) -> Dict[str, List[str]]:
        """Get valid values for pricing attributes."""
        result = {}
        
        for attribute_name in attribute_names:
            try:
                response = self.pricing_client.get_attribute_values(
                    ServiceCode=service_code,
                    AttributeName=attribute_name
                )
                values = [item['Value'] for item in response.get('AttributeValues', [])]
                result[attribute_name] = values
            except Exception as e:
                logger.error(f"Failed to get attribute values for {service_code}.{attribute_name}: {e}")
                result[attribute_name] = []
        
        return result
    
    def get_pricing(self, service_code: str, region: str, filters: Optional[List[Dict]] = None, 
                   max_results: int = 100) -> Dict[str, Any]:
        """Get pricing information for a service."""
        try:
            # Build filters
            pricing_filters = []
            
            # Add region filter
            if region:
                pricing_filters.append({
                    'Type': 'TERM_MATCH',
                    'Field': 'location',
                    'Value': self._region_to_location(region)
                })
            
            # Add custom filters
            if filters:
                for f in filters:
                    pricing_filters.append({
                        'Type': f.get('Type', 'TERM_MATCH'),
                        'Field': f['Field'],
                        'Value': f['Value']
                    })
            
            # Get products
            response = self.pricing_client.get_products(
                ServiceCode=service_code,
                Filters=pricing_filters,
                MaxResults=max_results
            )
            
            products = []
            for price_list in response.get('PriceList', []):
                product_data = json.loads(price_list)
                products.append(product_data)
            
            return {
                'service_code': service_code,
                'region': region,
                'products': products,
                'total_results': len(products)
            }
            
        except Exception as e:
            logger.error(f"Failed to get pricing for {service_code}: {e}")
            return {
                'service_code': service_code,
                'region': region,
                'products': [],
                'error': str(e)
            }
    
    def _region_to_location(self, region: str) -> str:
        """Convert AWS region to pricing location name."""
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-west-2': 'Europe (London)',
            'eu-central-1': 'Europe (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
        }
        return region_mapping.get(region, region)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for AWS Pricing MCP server."""
    try:
        operation = event.get('operation', 'get_pricing_service_codes')
        parameters = event.get('parameters', {})
        
        server = AWSPricingServer(region=parameters.get('region', 'us-east-1'))
        
        if operation == 'get_pricing_service_codes':
            results = server.get_pricing_service_codes()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'service_codes': results
                })
            }
        
        elif operation == 'get_pricing_service_attributes':
            service_code = parameters.get('service_code', '')
            if not service_code:
                raise ValueError("service_code parameter is required")
            
            results = server.get_pricing_service_attributes(service_code)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'service_code': service_code,
                    'attributes': results
                })
            }
        
        elif operation == 'get_pricing_attribute_values':
            service_code = parameters.get('service_code', '')
            attribute_names = parameters.get('attribute_names', [])
            
            if not service_code or not attribute_names:
                raise ValueError("service_code and attribute_names parameters are required")
            
            results = server.get_pricing_attribute_values(service_code, attribute_names)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'service_code': service_code,
                    'attribute_values': results
                })
            }
        
        elif operation == 'get_pricing':
            service_code = parameters.get('service_code', '')
            region = parameters.get('region', 'us-east-1')
            filters = parameters.get('filters', [])
            max_results = parameters.get('max_results', 100)
            
            if not service_code:
                raise ValueError("service_code parameter is required")
            
            results = server.get_pricing(service_code, region, filters, max_results)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'pricing_data': results
                }, cls=DecimalEncoder)
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"AWS Pricing Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }