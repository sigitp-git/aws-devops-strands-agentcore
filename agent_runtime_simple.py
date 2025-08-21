#!/usr/bin/env python3
"""
Simplified Amazon Bedrock AgentCore Runtime version for testing.
"""

import logging
from typing import Dict, Any
from datetime import datetime

# Import the BedrockAgentCoreApp wrapper
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the BedrockAgentCoreApp
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified entrypoint for testing.
    """
    try:
        logger.info(f"Received payload: {payload}")
        
        user_message = payload.get("prompt", "")
        
        if not user_message:
            return {
                "error": "No prompt found in input. Please provide a 'prompt' key in the payload.",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        
        # Simple response without using the full agent
        response_text = f"DevOps Agent Response: {user_message}\n\nThis is a simplified response for testing the AgentCore Runtime integration. The full agent functionality will be available once deployed."
        
        result = {
            "message": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
        logger.info("Request processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {
            "error": f"Processing failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error"
        }

if __name__ == "__main__":
    logger.info("Starting Simplified DevOps Agent Runtime Server...")
    logger.info("Server will start on http://0.0.0.0:8080")
    logger.info("Endpoints:")
    logger.info("  POST /invocations - Main processing")
    logger.info("  GET /ping - Health check")
    
    app.run()