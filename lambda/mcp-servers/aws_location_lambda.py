"""
AWS Location MCP Server as Lambda Function
"""
import json
import logging
import boto3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AWSLocationServer:
    """AWS Location Service operations."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.location_client = boto3.client('location', region_name=region)
    
    def search_places(self, query: str, max_results: int = 5, mode: str = "summary") -> Dict[str, Any]:
        """Search for places using Amazon Location Service."""
        try:
            # First, try to geocode the query to get a bias position
            bias_position = None
            try:
                geocode_response = self.location_client.search_place_index_for_text(
                    IndexName='Esri',  # Default place index
                    Text=query,
                    MaxResults=1
                )
                if geocode_response.get('Results'):
                    geometry = geocode_response['Results'][0]['Place']['Geometry']
                    bias_position = geometry['Point']
            except Exception as e:
                logger.warning(f"Could not geocode query for bias position: {e}")
            
            # Search for places
            search_params = {
                'IndexName': 'Esri',
                'Text': query,
                'MaxResults': max_results
            }
            
            if bias_position:
                search_params['BiasPosition'] = bias_position
            
            response = self.location_client.search_place_index_for_text(**search_params)
            
            places = []
            for result in response.get('Results', []):
                place = result['Place']
                
                if mode == "summary":
                    place_info = {
                        'place_id': place.get('PlaceId', ''),
                        'label': place.get('Label', ''),
                        'address': {
                            'street': place.get('AddressNumber', '') + ' ' + place.get('Street', ''),
                            'city': place.get('Municipality', ''),
                            'state': place.get('Region', ''),
                            'postal_code': place.get('PostalCode', ''),
                            'country': place.get('Country', '')
                        },
                        'coordinates': {
                            'longitude': place['Geometry']['Point'][0],
                            'latitude': place['Geometry']['Point'][1]
                        },
                        'categories': place.get('Categories', []),
                        'contact': {
                            'phone': place.get('Phone', ''),
                            'website': place.get('Website', '')
                        }
                    }
                else:  # raw mode
                    place_info = place
                
                places.append(place_info)
            
            return {
                'success': True,
                'query': query,
                'places': places,
                'total_results': len(places),
                'mode': mode
            }
            
        except Exception as e:
            logger.error(f"Failed to search places: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e)
            }
    
    def get_place(self, place_id: str, mode: str = "summary") -> Dict[str, Any]:
        """Get details for a specific place."""
        try:
            response = self.location_client.get_place(
                IndexName='Esri',
                PlaceId=place_id
            )
            
            place = response['Place']
            
            if mode == "summary":
                place_info = {
                    'place_id': place.get('PlaceId', ''),
                    'label': place.get('Label', ''),
                    'address': {
                        'street': place.get('AddressNumber', '') + ' ' + place.get('Street', ''),
                        'city': place.get('Municipality', ''),
                        'state': place.get('Region', ''),
                        'postal_code': place.get('PostalCode', ''),
                        'country': place.get('Country', '')
                    },
                    'coordinates': {
                        'longitude': place['Geometry']['Point'][0],
                        'latitude': place['Geometry']['Point'][1]
                    },
                    'categories': place.get('Categories', []),
                    'contact': {
                        'phone': place.get('Phone', ''),
                        'website': place.get('Website', '')
                    },
                    'opening_hours': place.get('OpeningHours', {}),
                    'time_zone': place.get('TimeZone', {})
                }
            else:  # raw mode
                place_info = place
            
            return {
                'success': True,
                'place_id': place_id,
                'place': place_info,
                'mode': mode
            }
            
        except Exception as e:
            logger.error(f"Failed to get place {place_id}: {e}")
            return {
                'success': False,
                'place_id': place_id,
                'error': str(e)
            }
    
    def reverse_geocode(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """Reverse geocode coordinates to an address."""
        try:
            response = self.location_client.search_place_index_for_position(
                IndexName='Esri',
                Position=[longitude, latitude],
                MaxResults=1
            )
            
            if response.get('Results'):
                place = response['Results'][0]['Place']
                
                address_info = {
                    'formatted_address': place.get('Label', ''),
                    'address_components': {
                        'street_number': place.get('AddressNumber', ''),
                        'street': place.get('Street', ''),
                        'city': place.get('Municipality', ''),
                        'state': place.get('Region', ''),
                        'postal_code': place.get('PostalCode', ''),
                        'country': place.get('Country', '')
                    },
                    'coordinates': {
                        'longitude': longitude,
                        'latitude': latitude
                    }
                }
                
                return {
                    'success': True,
                    'coordinates': [longitude, latitude],
                    'address': address_info
                }
            else:
                return {
                    'success': False,
                    'coordinates': [longitude, latitude],
                    'error': 'No address found for coordinates'
                }
                
        except Exception as e:
            logger.error(f"Failed to reverse geocode: {e}")
            return {
                'success': False,
                'coordinates': [longitude, latitude],
                'error': str(e)
            }
    
    def search_nearby(self, longitude: float, latitude: float, query: Optional[str] = None,
                     radius: int = 500, max_results: int = 5) -> Dict[str, Any]:
        """Search for places near a location."""
        try:
            search_params = {
                'IndexName': 'Esri',
                'Position': [longitude, latitude],
                'MaxResults': max_results
            }
            
            if query:
                search_params['FilterCategories'] = [query]
            
            response = self.location_client.search_place_index_for_position(**search_params)
            
            places = []
            for result in response.get('Results', []):
                place = result['Place']
                
                # Calculate distance (simplified)
                place_coords = place['Geometry']['Point']
                distance = self._calculate_distance(
                    latitude, longitude,
                    place_coords[1], place_coords[0]
                )
                
                if distance <= radius:
                    place_info = {
                        'place_id': place.get('PlaceId', ''),
                        'label': place.get('Label', ''),
                        'address': {
                            'street': place.get('AddressNumber', '') + ' ' + place.get('Street', ''),
                            'city': place.get('Municipality', ''),
                            'state': place.get('Region', ''),
                            'country': place.get('Country', '')
                        },
                        'coordinates': {
                            'longitude': place_coords[0],
                            'latitude': place_coords[1]
                        },
                        'distance_meters': int(distance),
                        'categories': place.get('Categories', [])
                    }
                    places.append(place_info)
            
            return {
                'success': True,
                'center_coordinates': [longitude, latitude],
                'query': query,
                'radius_meters': radius,
                'places': places,
                'total_results': len(places)
            }
            
        except Exception as e:
            logger.error(f"Failed to search nearby: {e}")
            return {
                'success': False,
                'center_coordinates': [longitude, latitude],
                'error': str(e)
            }
    
    def calculate_route(self, departure_position: List[float], destination_position: List[float],
                       travel_mode: str = "Car", optimize_for: str = "FastestRoute") -> Dict[str, Any]:
        """Calculate a route between two positions."""
        try:
            response = self.location_client.calculate_route(
                CalculatorName='Esri',
                DeparturePosition=departure_position,
                DestinationPosition=destination_position,
                TravelMode=travel_mode,
                OptimizeFor=optimize_for
            )
            
            summary = response['Summary']
            legs = response.get('Legs', [])
            
            # Extract turn-by-turn directions
            directions = []
            for leg in legs:
                for step in leg.get('Steps', []):
                    directions.append({
                        'instruction': step.get('Instruction', ''),
                        'distance_meters': step.get('Distance', 0),
                        'duration_seconds': step.get('DurationSeconds', 0),
                        'start_position': step.get('StartPosition', []),
                        'end_position': step.get('EndPosition', [])
                    })
            
            route_info = {
                'distance_meters': summary.get('Distance', 0),
                'duration_seconds': summary.get('DurationSeconds', 0),
                'travel_mode': travel_mode,
                'optimize_for': optimize_for,
                'departure_position': departure_position,
                'destination_position': destination_position,
                'turn_by_turn': directions
            }
            
            return {
                'success': True,
                'route': route_info
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate route: {e}")
            return {
                'success': False,
                'departure_position': departure_position,
                'destination_position': destination_position,
                'error': str(e)
            }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        import math
        
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Lambda handler for AWS Location MCP server."""
    try:
        operation = event.get('operation', 'search_places')
        parameters = event.get('parameters', {})
        region = parameters.get('region', 'us-east-1')
        
        server = AWSLocationServer(region=region)
        
        if operation == 'search_places':
            query = parameters.get('query', '')
            max_results = parameters.get('max_results', 5)
            mode = parameters.get('mode', 'summary')
            
            if not query:
                raise ValueError("query parameter is required")
            
            results = server.search_places(query, max_results, mode)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'results': results
                })
            }
        
        elif operation == 'get_place':
            place_id = parameters.get('place_id', '')
            mode = parameters.get('mode', 'summary')
            
            if not place_id:
                raise ValueError("place_id parameter is required")
            
            results = server.get_place(place_id, mode)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'results': results
                })
            }
        
        elif operation == 'reverse_geocode':
            longitude = parameters.get('longitude')
            latitude = parameters.get('latitude')
            
            if longitude is None or latitude is None:
                raise ValueError("longitude and latitude parameters are required")
            
            results = server.reverse_geocode(longitude, latitude)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'results': results
                })
            }
        
        elif operation == 'search_nearby':
            longitude = parameters.get('longitude')
            latitude = parameters.get('latitude')
            query = parameters.get('query')
            radius = parameters.get('radius', 500)
            max_results = parameters.get('max_results', 5)
            
            if longitude is None or latitude is None:
                raise ValueError("longitude and latitude parameters are required")
            
            results = server.search_nearby(longitude, latitude, query, radius, max_results)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'results': results
                })
            }
        
        elif operation == 'calculate_route':
            departure_position = parameters.get('departure_position', [])
            destination_position = parameters.get('destination_position', [])
            travel_mode = parameters.get('travel_mode', 'Car')
            optimize_for = parameters.get('optimize_for', 'FastestRoute')
            
            if not departure_position or not destination_position:
                raise ValueError("departure_position and destination_position parameters are required")
            
            results = server.calculate_route(departure_position, destination_position, travel_mode, optimize_for)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'operation': operation,
                    'results': results
                })
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        logger.error(f"AWS Location Lambda error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'operation': event.get('operation', 'unknown')
            })
        }