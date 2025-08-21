#!/usr/bin/env python3
"""
Simple test of BedrockAgentCoreApp to isolate issues.
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from typing import Dict, Any
from datetime import datetime

# Initialize the BedrockAgentCoreApp
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Simple test entrypoint."""
    try:
        user_message = payload.get("prompt", "")
        
        if not user_message:
            return {
                "error": "No prompt found in input",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
        
        # Simple echo response
        return {
            "message": f"Echo: {user_message}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": f"Processing failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error"
        }

if __name__ == "__main__":
    print("Starting simple runtime test server...")
    app.run()