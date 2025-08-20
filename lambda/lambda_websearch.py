import json
import logging
from typing import Dict, Any, List
from duckduckgo_search import DDGS

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for web search functionality.
    
    Expected event structure:
    {
        "keywords": "search terms",
        "region": "us-en",  # optional, defaults to us-en
        "max_results": 5    # optional, defaults to None
    }
    """
    try:
        # Extract parameters from event
        keywords = event.get('keywords', '').strip()
        region = event.get('region', 'us-en')
        max_results = event.get('max_results')
        
        # Validate input
        if not keywords:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Search keywords cannot be empty',
                    'success': False
                })
            }
        
        logger.info(f"Performing web search for: '{keywords}' in region: {region}")
        
        # Perform search
        results = websearch(keywords, region, max_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'results': results,
                'query': keywords,
                'region': region
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'success': False
            })
        }

def websearch(keywords: str, region: str = 'us-en', max_results: int = None) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo.
    
    Args:
        keywords: The search query keywords
        region: The search region (wt-wt, us-en, uk-en, ru-ru, etc.)
        max_results: The maximum number of results to return
        
    Returns:
        Dictionary with search results or error information
    """
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        
        if not results:
            logger.warning(f"No search results found for: {keywords}")
            return {
                'message': 'No results found',
                'results': [],
                'count': 0
            }
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append({
                'rank': i,
                'title': result.get('title', 'No title'),
                'body': result.get('body', 'No description'),
                'url': result.get('href', 'No URL')
            })
        
        logger.info(f"Found {len(formatted_results)} search results")
        return {
            'message': 'Search completed successfully',
            'results': formatted_results,
            'count': len(formatted_results)
        }
        
    except Exception as ddgs_error:
        # Handle DuckDuckGo specific errors
        error_msg = str(ddgs_error).lower()
        if 'rate limit' in error_msg or 'too many requests' in error_msg:
            logger.warning("DuckDuckGo rate limit exceeded")
            return {
                'error': 'Rate limit exceeded. Please try again after a short delay.',
                'results': [],
                'count': 0
            }
        logger.error(f"DuckDuckGo search error: {ddgs_error}")
        return {
            'error': f'Search service error: {str(ddgs_error)}',
            'results': [],
            'count': 0
        }
    except Exception as e:
        logger.error(f"Unexpected error during web search: {e}")
        return {
            'error': f'Search failed: {str(e)}',
            'results': [],
            'count': 0
        }