#!/usr/bin/env python3
"""
Local agent connecting to Amazon Bedrock AgentCore Memory and Gateway
"""

import logging
import os
import uuid
import sys
import json
import requests

# Import boto libraries and AWS tools
import boto3
from boto3.session import Session
from utils import get_ssm_parameter, put_ssm_parameter, load_api_spec, get_cognito_client_secret

# Import DDGS
from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException

# Import Strands, BedrockModel, MCP libraries
from strands.agent import Agent
from strands.tools import tool
from strands.hooks import AfterInvocationEvent, HookProvider, HookRegistry, MessageAddedEvent
from strands.models.bedrock import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Import AgentCore Memory
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType

# Import AgentCore Identity
from bedrock_agentcore.identity.auth import requires_access_token

sts_client = boto3.client('sts')

class AgentConfig:
    """Configuration settings for the DevOps Agent."""
    
    # AWS Settings
    DEFAULT_REGION = 'us-east-1'
    
    # Available Models
    AVAILABLE_MODELS = {
        'claude-sonnet-4': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
        'claude-3-7-sonnet': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        'claude-3-5-sonnet-v2': 'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        'claude-3-5-sonnet-v1': 'us.anthropic.claude-3-5-sonnet-20240620-v1:0',
        'claude-3-5-haiku': 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
    }
    
    # Default model selection
    SELECTED_MODEL = 'claude-3-5-haiku'
    
    @classmethod
    def get_model_id(cls):
        """Get the currently selected model ID."""
        return cls.AVAILABLE_MODELS.get(cls.SELECTED_MODEL, cls.AVAILABLE_MODELS['claude-3-5-sonnet-v2'])
    
    @classmethod
    def set_model(cls, model_key):
        """Set the model by key."""
        if model_key in cls.AVAILABLE_MODELS:
            cls.SELECTED_MODEL = model_key
            return True
        return False
    
    @classmethod
    def list_models(cls):
        """List available models with descriptions."""
        return {
            'claude-sonnet-4': 'Claude Sonnet 4 (Latest, Most Capable)',
            'claude-3-7-sonnet': 'Claude 3.7 Sonnet (Enhanced Reasoning)',
            'claude-3-5-sonnet-v2': 'Claude 3.5 Sonnet v2 (Balanced Performance)',
            'claude-3-5-sonnet-v1': 'Claude 3.5 Sonnet v1 (Stable)',
            'claude-3-5-haiku': 'Claude 3.5 Haiku (Fast & Efficient)'
        }
    
    # Model Settings
    MODEL_TEMPERATURE = 0.3
    
    # Memory Settings
    MEMORY_NAME = "DevOpsAgentMemory"
    SSM_MEMORY_ID_PATH = "/app/devopsagent/agentcore/memory_id"
    MEMORY_EXPIRY_DAYS = 90
    CONTEXT_RETRIEVAL_TOP_K = 3
    DEVOPS_USER_ID = "devops_001"
    
    # Search Settings
    SEARCH_REGION = "us-en"
    
    @classmethod
    def setup_aws_region(cls):
        """Setup AWS region configuration."""
        os.environ['AWS_DEFAULT_REGION'] = cls.DEFAULT_REGION
        return Session().region_name

def select_model_interactive():
    """Interactive model selection for CLI usage."""
    print("\n🤖 Available Claude Models:")
    print("=" * 50)
    
    models = AgentConfig.list_models()
    model_keys = list(models.keys())
    
    for i, (key, description) in enumerate(models.items(), 1):
        current = " (CURRENT)" if key == AgentConfig.SELECTED_MODEL else ""
        print(f"{i}. {description}{current}")
    
    print(f"\n0. Use current selection: {models[AgentConfig.SELECTED_MODEL]}")
    
    try:
        choice = input("\nSelect model (0-5): ").strip()
        
        if choice == '0' or choice == '':
            print(f"✅ Using current model: {models[AgentConfig.SELECTED_MODEL]}")
            return
        
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(model_keys):
            selected_key = model_keys[choice_idx]
            AgentConfig.set_model(selected_key)
            print(f"✅ Selected model: {models[selected_key]}")
        else:
            print("❌ Invalid selection. Using current model.")
    except (ValueError, KeyboardInterrupt):
        print(f"✅ Using current model: {models[AgentConfig.SELECTED_MODEL]}")

# Check for command line arguments
if len(sys.argv) > 1:
    if sys.argv[1] == '--select-model':
        select_model_interactive()
        sys.exit(0)
    elif sys.argv[1] in ['--help', '-h']:
        print("\n🤖 AWS DevOps Agent - Usage")
        print("=" * 40)
        print("python3 agent.py                 # Run agent with current model")
        print("python3 agent.py --select-model  # Interactive model selection")
        print("python3 select_model.py          # Standalone model selector")
        print("\nAvailable Models:")
        for key, desc in AgentConfig.list_models().items():
            current = " (CURRENT)" if key == AgentConfig.SELECTED_MODEL else ""
            print(f"  • {desc}{current}")
        print()
        sys.exit(0)

# Initialize configuration
REGION = AgentConfig.setup_aws_region()

def validate_discovery_url(url):
    """Validate that the discovery URL is accessible and returns valid OIDC configuration."""
    try:
        import requests
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            config = response.json()
            required_fields = ['issuer', 'authorization_endpoint', 'token_endpoint', 'jwks_uri']
            if all(field in config for field in required_fields):
                return True, "Valid OIDC configuration"
            else:
                return False, f"Missing required OIDC fields: {[f for f in required_fields if f not in config]}"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def validate_gateway_configuration():
    """Validate gateway configuration parameters before creation."""
    required_params = {
        "/app/devopsagent/agentcore/machine_client_id": "Machine Client ID",
        "/app/devopsagent/agentcore/cognito_discovery_url": "Cognito Discovery URL",
        "/app/devopsagent/agentcore/gateway_iam_role": "Gateway IAM Role"
    }
    
    missing_params = []
    invalid_params = []
    
    for param_path, param_name in required_params.items():
        value = get_ssm_parameter(param_path)
        if not value:
            missing_params.append(f"{param_name} ({param_path})")
        elif param_path.endswith("cognito_discovery_url"):
            # Validate discovery URL format and accessibility
            if not value.endswith("/.well-known/openid_configuration"):
                invalid_params.append(f"{param_name}: Must end with '/.well-known/openid_configuration'")
            elif "example.com" in value:
                invalid_params.append(f"{param_name}: Appears to be a placeholder")
            else:
                # Test if the URL is accessible and returns valid OIDC config
                is_valid, message = validate_discovery_url(value)
                if not is_valid:
                    invalid_params.append(f"{param_name}: {message}")
                    print(f"💡 The discovery URL {value} is not accessible or doesn't return valid OIDC configuration")
                    print("   This might be because:")
                    print("   1. Cognito User Pool doesn't have a domain configured")
                    print("   2. The domain is not set up for OIDC discovery")
                    print("   3. You need to use a different OIDC provider")
    
    if missing_params:
        print(f"❌ Missing required SSM parameters: {', '.join(missing_params)}")
        return False
    
    if invalid_params:
        print(f"❌ Invalid SSM parameters:")
        for param in invalid_params:
            print(f"   • {param}")
        return False
    
    return True

def use_manual_gateway():
    """Use manually created gateway from AWS Management Console."""
    # Manually created gateway ID from AWS Management Console
    manual_gateway_id = "devopsagent-agentcore-gw-1xgl5imapz"
    
    print(f"🔍 Using manually created gateway: {manual_gateway_id}")
    
    gateway_client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    
    try:
        # Get gateway details
        gateway_response = gateway_client.get_gateway(gatewayIdentifier=manual_gateway_id)
        gateway = {
            "id": manual_gateway_id,
            "name": gateway_response["name"],
            "gateway_url": gateway_response["gatewayUrl"],
            "gateway_arn": gateway_response["gatewayArn"],
        }
        
        # Store gateway ID in SSM for reference
        put_ssm_parameter("/app/devopsagent/agentcore/gateway_id", manual_gateway_id)
        
        print(f"✅ Successfully connected to manual gateway: {manual_gateway_id}")
        print(f"   Gateway URL: {gateway['gateway_url']}")
        return gateway, manual_gateway_id
        
    except Exception as e:
        print(f"⚠️  Could not connect to manual gateway {manual_gateway_id}: {e}")
        print("🔄 Continuing without gateway functionality...")
        return None, None

# Commented out automatic gateway creation - using manually created gateway instead
# def create_gateway_if_configured():
#     """Create gateway only if properly configured."""
#     print("🔍 Checking gateway configuration...")
#     
#     if not validate_gateway_configuration():
#         print("🔄 Gateway functionality disabled due to configuration issues")
#         print("💡 The agent will continue to work without gateway functionality")
#         print("   Gateway is only needed for advanced MCP integrations")
#         return None, None
#     
#     gateway_client = boto3.client("bedrock-agentcore-control", region_name=REGION)
#     gateway_name = "devopsagent-agentcore-gw"
#     
#     # Get configuration
#     discovery_url = get_ssm_parameter("/app/devopsagent/agentcore/cognito_discovery_url")
#     client_id = get_ssm_parameter("/app/devopsagent/agentcore/machine_client_id")
#     
#     auth_config = {
#         "customJWTAuthorizer": {
#             "allowedClients": [client_id],
#             "discoveryUrl": discovery_url
#         }
#     }
#     
#     try:
#         print(f"✅ Configuration valid - creating gateway in region {REGION}")
#         
#         create_response = gateway_client.create_gateway(
#             name=gateway_name,
#             roleArn=get_ssm_parameter("/app/devopsagent/agentcore/gateway_iam_role"),
#             protocolType="MCP",
#             authorizerType="CUSTOM_JWT",
#             authorizerConfiguration=auth_config,
#             description="DevOps Agent AgentCore Gateway",
#         )
#         
#         gateway_id = create_response["gatewayId"]
#         gateway = {
#             "id": gateway_id,
#             "name": gateway_name,
#             "gateway_url": create_response["gatewayUrl"],
#             "gateway_arn": create_response["gatewayArn"],
#         }
#         put_ssm_parameter("/app/devopsagent/agentcore/gateway_id", gateway_id)
#         print(f"✅ Gateway created successfully with ID: {gateway_id}")
#         return gateway, gateway_id
#         
#     except Exception as e:
#         print(f"⚠️  Gateway creation failed: {e}")
#         return try_existing_gateway(gateway_client)

def try_existing_gateway(gateway_client):
    """Try to use existing gateway if available."""
    existing_gateway_id = get_ssm_parameter("/app/devopsagent/agentcore/gateway_id")
    
    if existing_gateway_id:
        print(f"Found existing gateway with ID: {existing_gateway_id}")
        try:
            gateway_response = gateway_client.get_gateway(gatewayIdentifier=existing_gateway_id)
            gateway = {
                "id": existing_gateway_id,
                "name": gateway_response["name"],
                "gateway_url": gateway_response["gatewayUrl"],
                "gateway_arn": gateway_response["gatewayArn"],
            }
            print(f"✅ Using existing gateway: {existing_gateway_id}")
            return gateway, existing_gateway_id
        except Exception as get_error:
            print(f"⚠️  Could not retrieve existing gateway: {get_error}")
    
    print("🔄 Continuing without gateway functionality...")
    return None, None

# Initialize gateway - using manually created gateway
gateway, gateway_id = use_manual_gateway()

# Using the AgentCore Gateway for MCP server (only if gateway is available)
def get_token(client_id: str, client_secret: str, scope_string: str = None, url: str = None) -> dict:
    try:
        # Use default values if not provided
        if scope_string is None:
            scope_string = get_ssm_parameter("/app/devopsagent/agentcore/cognito_auth_scope") or "openid"
        if url is None:
            url = get_ssm_parameter("/app/devopsagent/agentcore/cognito_token_url") or "https://REDACTED_COGNITO_ID.auth.us-east-1.amazoncognito.com/oauth2/token"
            
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope_string,

        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as err:
        return {"error": str(err)}

# Initialize MCP client only if gateway is available
mcp_client = None
if gateway and gateway_id:
    try:
        print(f"🔗 Setting up MCP client for gateway: {gateway_id}")
        
        gateway_access_token = get_token(
            get_ssm_parameter("/app/devopsagent/agentcore/machine_client_id"),
            get_cognito_client_secret(),
            get_ssm_parameter("/app/devopsagent/agentcore/cognito_auth_scope"),
            get_ssm_parameter("/app/devopsagent/agentcore/cognito_token_url")
        )
        
        print(f"🔍 Debug - Token response: {gateway_access_token}")
        
        # Check if we got a valid token
        if 'error' in gateway_access_token:
            print(f"❌ Token error: {gateway_access_token['error']}")
            raise Exception(f"Failed to get access token: {gateway_access_token['error']}")
        
        if 'access_token' not in gateway_access_token:
            print(f"❌ No access_token in response. Available keys: {list(gateway_access_token.keys())}")
            raise Exception("No access_token in authentication response")

        print(f"Gateway Endpoint - MCP URL: {gateway['gateway_url']}")

        # Set up MCP client
        mcp_client = MCPClient(
            lambda: streamablehttp_client(
                gateway['gateway_url'],
                headers={"Authorization": f"Bearer {gateway_access_token['access_token']}"},
            )
        )
        print("✅ MCP client configured successfully")
        
    except Exception as e:
        print(f"⚠️  MCP client setup failed: {e}")
        print("🔄 Continuing without MCP client functionality...")
        mcp_client = None
else:
    print("ℹ️  No gateway available - MCP client functionality disabled")

# Initialize MCP client if available
if mcp_client:
    try:
        mcp_client.start()
        print("✅ MCP client started successfully")
    except Exception as e:
        print(f"⚠️  MCP client start failed: {str(e)}")
        print("🔄 Continuing without MCP client functionality...")
        mcp_client = None

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


# Define a websearch tool
@tool
def list_mcp_tools() -> str:
    """List all available MCP tools and their descriptions.
    
    Returns:
        Formatted list of MCP tools with descriptions
    """
    if not mcp_client:
        return "❌ MCP client is not available. No MCP tools are currently accessible."
    
    try:
        mcp_tools = get_full_tools_list(mcp_client)
        
        if not mcp_tools:
            return "ℹ️  No MCP tools are currently available through the gateway."
        
        result = f"🔧 **Available MCP Tools ({len(mcp_tools)} total):**\n\n"
        
        for i, tool in enumerate(mcp_tools, 1):
            tool_name = getattr(tool, 'name', 'Unknown')
            tool_description = getattr(tool, 'description', 'No description available')
            
            # Try to get input schema if available
            input_schema = getattr(tool, 'inputSchema', None)
            parameters = ""
            if input_schema and hasattr(input_schema, 'properties'):
                param_names = list(input_schema.properties.keys()) if input_schema.properties else []
                if param_names:
                    parameters = f" (Parameters: {', '.join(param_names)})"
            
            result += f"{i}. **{tool_name}**{parameters}\n"
            result += f"   {tool_description}\n\n"
        
        result += "💡 These tools are available through the MCP gateway integration and can be used for advanced functionality."
        return result
        
    except Exception as e:
        return f"❌ Error retrieving MCP tools: {str(e)}"

@tool
def websearch(
    keywords: str, region: str = AgentConfig.SEARCH_REGION, max_results: int | None = None
) -> str:
    """Search the web to get updated information using DuckDuckGo.
    
    Args:
        keywords: The search query keywords
        region: The search region (wt-wt, us-en, uk-en, ru-ru, etc.)
        max_results: The maximum number of results to return
        
    Returns:
        Search results as formatted string or error message
    """
    if not keywords or not keywords.strip():
        return "Error: Search keywords cannot be empty."
    
    try:
        logger.info(f"Performing web search for: '{keywords}' in region: {region}")
        results = DDGS().text(keywords, region=region, max_results=max_results)
        
        if not results:
            logger.warning(f"No search results found for: {keywords}")
            return "No results found."
        
        logger.info(f"Found {len(results)} search results")
        return _format_search_results(results)
        
    except RatelimitException:
        logger.warning("DuckDuckGo rate limit exceeded")
        return "Rate limit exceeded. Please try again after a short delay."
    except DDGSException as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return f"Search service error: {e}"
    except Exception as e:
        logger.error(f"Unexpected error during web search: {e}")
        return f"Search failed: {e}"

def _format_search_results(results: list) -> str:
    """Format search results for better readability."""
    if not results:
        return "No results found."
    
    formatted = []
    for i, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        body = result.get('body', 'No description')
        href = result.get('href', 'No URL')
        
        formatted.append(f"{i}. **{title}**\n   {body}\n   URL: {href}\n")
    
    return "\n".join(formatted)


# Create a Bedrock model instance with temperature control
# Temperature 0.3: Focused and consistent responses, ideal for technical accuracy
# Adjust temperature: 0.1-0.3 (very focused), 0.4-0.7 (balanced), 0.8-1.0 (creative)
current_model_id = AgentConfig.get_model_id()
print(f"🤖 Using MODEL_ID: {current_model_id}")
print(f"📝 Model Description: {AgentConfig.list_models()[AgentConfig.SELECTED_MODEL]}")
model = BedrockModel(
    model_id=current_model_id, 
    temperature=AgentConfig.MODEL_TEMPERATURE
)

# AgentCore Memory section
memory_client = MemoryClient(region_name=REGION)
memory_name = AgentConfig.MEMORY_NAME



class MemoryManager:
    """Manages AgentCore Memory resource lifecycle."""
    
    def __init__(self, client: MemoryClient, memory_name: str):
        self.client = client
        self.memory_name = memory_name
        
    def get_or_create_memory(self) -> str | None:
        """Get existing memory or create new one."""
        logger.info("Attempting to retrieve or create AgentCore Memory resource...")
        
        # Try SSM first, then search, then create
        memory_id = self._get_memory_from_ssm()
        if memory_id:
            return memory_id
            
        memory_id = self._find_existing_memory()
        if memory_id:
            return memory_id
            
        return self._create_new_memory()
    
    def _get_memory_from_ssm(self) -> str | None:
        """Retrieve and verify memory ID from SSM."""
        try:
            memory_id = get_ssm_parameter(AgentConfig.SSM_MEMORY_ID_PATH)
            if memory_id:
                logger.info(f"Found memory ID in SSM: {memory_id}")
                # Verify the memory exists
                try:
                    self.client.gmcp_client.get_memory(memoryId=memory_id)
                    logger.info("Memory verified successfully")
                    return memory_id
                except Exception as verify_error:
                    logger.warning(f"Memory ID from SSM is invalid: {verify_error}")
        except Exception as e:
            logger.warning(f"Could not retrieve memory ID from SSM: {e}")
        return None
    
    def _find_existing_memory(self) -> str | None:
        """Search for existing memory by name or pattern."""
        try:
            logger.info("Searching for existing memory...")
            memories = self.client.gmcp_client.list_memories()
            logger.info(f"Found {len(memories.get('memories', []))} total memories")
            
            for memory in memories.get('memories', []):
                memory_id = memory.get('id')
                memory_name_from_api = memory.get('name')
                memory_status = memory.get('status')
                
                logger.debug(f"Memory ID: {memory_id}, Name: {memory_name_from_api}, Status: {memory_status}")
                
                if memory_status == 'DELETING':
                    continue
                
                # Check by name or ID pattern
                if (memory_name_from_api == self.memory_name or 
                    (memory_name_from_api is None and self.memory_name in memory_id and memory_status == 'ACTIVE')):
                    logger.info(f"Found existing memory: {memory_id}")
                    self._save_memory_id_to_ssm(memory_id)
                    return memory_id
            
            logger.info("No existing memory found")
        except Exception as e:
            logger.error(f"Could not list existing memories: {e}")
        return None
    
    def _create_new_memory(self) -> str | None:
        """Create a new memory resource."""
        try:
            logger.info("Creating new AgentCore Memory resource...")
            strategies = self._create_memory_strategies()
            
            logger.info("Creating AgentCore Memory resources. This can take a couple of minutes...")
            response = self.client.create_memory_and_wait(
                name=self.memory_name,
                description="DevOps Agent memory",
                strategies=strategies,
                event_expiry_days=AgentConfig.MEMORY_EXPIRY_DAYS,
            )
            memory_id = response["id"]
            logger.info(f"Successfully created memory: {memory_id}")
            
            self._save_memory_id_to_ssm(memory_id)
            return memory_id
        except Exception as e:
            logger.error(f"Failed to create memory: {e}")
            return None
    
    def _create_memory_strategies(self) -> list:
        """Create memory strategies configuration."""
        return [
            {
                StrategyType.USER_PREFERENCE.value: {
                    "name": "DevOpsPreferences",
                    "description": "Captures DevOps preferences and behavior",
                    "namespaces": ["agent/devops/{actorId}/preferences"],
                }
            },
            {
                StrategyType.SEMANTIC.value: {
                    "name": "DevOpsAgentSemantic",
                    "description": "Stores facts from conversations",
                    "namespaces": ["agent/devops/{actorId}/semantic"],
                }
            },
        ]
    
    def _save_memory_id_to_ssm(self, memory_id: str) -> None:
        """Save memory ID to SSM Parameter Store."""
        try:
            put_ssm_parameter(AgentConfig.SSM_MEMORY_ID_PATH, memory_id)
            logger.info("Saved memory ID to SSM")
        except Exception as e:
            logger.warning(f"Could not save memory ID to SSM: {e}")

def create_or_get_memory_resource():
    """Factory function for memory resource creation."""
    memory_manager = MemoryManager(memory_client, memory_name)
    return memory_manager.get_or_create_memory()

def initialize_memory() -> str | None:
    """Initialize memory with proper error handling."""
    try:
        memory_id = create_or_get_memory_resource()
        if memory_id:
            logger.info(f"AgentCore Memory ready with ID: {memory_id}")
            return memory_id
        else:
            _log_memory_initialization_error()
            return None
    except Exception as e:
        logger.error(f"Unexpected error during memory initialization: {e}")
        _log_memory_initialization_error()
        return None

def _log_memory_initialization_error():
    """Log memory initialization error with helpful information."""
    error_messages = [
        "Failed to create or retrieve memory resource",
        "Possible causes:",
        "1. AWS credentials not configured or insufficient permissions",
        "2. AgentCore Memory service not available in your region",
        "3. Network connectivity issues",
        "4. SSM parameter store access issues",
        "The agent will continue without memory functionality..."
    ]
    for msg in error_messages:
        logger.warning(msg)

memory_id = initialize_memory()

class DevOpsAgentMemoryHooks(HookProvider):
    """Memory hooks for DevOps Agent"""

    def __init__(
        self, memory_id: str, client: MemoryClient, actor_id: str, session_id: str
    ):
        self.memory_id = memory_id
        self.client = client
        self.actor_id = actor_id
        self.session_id = session_id
        self.namespaces = {
            i["type"]: i["namespaces"][0]
            for i in self.client.get_memory_strategies(self.memory_id)
        }

    def retrieve_devops_context(self, event: MessageAddedEvent):
        """Retrieve DevOps context before processing query"""
        messages = event.agent.messages
        if (
            messages[-1]["role"] == "user"
            and "toolResult" not in messages[-1]["content"][0]
        ):
            user_query = messages[-1]["content"][0]["text"]

            try:
                all_context = []

                for context_type, namespace in self.namespaces.items():
                    # *** AGENTCORE MEMORY USAGE *** - Retrieve DevOps context from each namespace
                    memories = self.client.retrieve_memories(
                        memory_id=self.memory_id,
                        namespace=namespace.format(actorId=self.actor_id),
                        query=user_query,
                        top_k=AgentConfig.CONTEXT_RETRIEVAL_TOP_K,
                    )
                    # Post-processing: Format memories into context strings
                    for memory in memories:
                        if isinstance(memory, dict):
                            content = memory.get("content", {})
                            if isinstance(content, dict):
                                text = content.get("text", "").strip()
                                if text:
                                    all_context.append(
                                        f"[{context_type.upper()}] {text}"
                                    )

                # Inject DevOps context into the query
                if all_context:
                    context_text = "\n".join(all_context)
                    original_text = messages[-1]["content"][0]["text"]
                    messages[-1]["content"][0][
                        "text"
                    ] = f"DevOps Context:\n{context_text}\n\n{original_text}"
                    logger.info(f"Retrieved {len(all_context)} DevOps context items")

            except Exception as e:
                logger.error(f"Failed to retrieve DevOps context: {e}")

    def save_devops_interaction(self, event: AfterInvocationEvent):
        """Save DevOps Agent interaction after agent response"""
        try:
            messages = event.agent.messages
            if len(messages) >= 2 and messages[-1]["role"] == "agent":
                # Get last user query and agent response
                user_query = None
                agent_response = None

                for msg in reversed(messages):
                    if msg["role"] == "agent" and not agent_response:
                        agent_response = msg["content"][0]["text"]
                    elif (
                        msg["role"] == "user"
                        and not user_query
                        and "toolResult" not in msg["content"][0]
                    ):
                        user_query = msg["content"][0]["text"]
                        break

                if user_query and agent_response:
                    # *** AGENTCORE MEMORY USAGE *** - Save the DevOps interaction
                    # Note: AgentCore Memory requires "ASSISTANT" role, not "AGENT"
                    self.client.create_event(
                        memory_id=self.memory_id,
                        actor_id=self.actor_id,
                        session_id=self.session_id,
                        messages=[
                            (user_query, "USER"),
                            (agent_response, "ASSISTANT"),
                        ],
                    )
                    logger.info("Saved DevOps interaction to memory")

        except Exception as e:
            logger.error(f"Failed to save DevOps interaction: {e}")

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register DevOps Agent memory hooks"""
        registry.add_callback(MessageAddedEvent, self.retrieve_devops_context)
        registry.add_callback(AfterInvocationEvent, self.save_devops_interaction)
        logger.info("DevOps Agent memory hooks registered")

SESSION_ID = str(uuid.uuid4())

def create_agent_hooks(memory_id: str | None) -> list:
    """Create agent hooks based on memory availability."""
    if not memory_id:
        logger.info("Running without memory functionality")
        return []
    
    session_id = str(uuid.uuid4())
    memory_hooks = DevOpsAgentMemoryHooks(
        memory_id, memory_client, AgentConfig.DEVOPS_USER_ID, session_id
    )
    logger.info("Memory hooks enabled")
    return [memory_hooks]

def get_full_tools_list(client):
    """
    List tools w/ support for pagination
    """
    try:
        more_tools = True
        tools = []
        pagination_token = None
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while more_tools and iteration < max_iterations:
            iteration += 1
            print(f"🔍 Fetching MCP tools (iteration {iteration})...")
            
            tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
            
            if hasattr(tmp_tools, '__iter__'):
                # If tmp_tools is a list/iterable of tools
                tools.extend(tmp_tools)
                more_tools = False  # Assume no pagination if we get a simple list
            elif hasattr(tmp_tools, 'tools'):
                # If tmp_tools has a tools attribute
                tools.extend(tmp_tools.tools)
                if hasattr(tmp_tools, 'pagination_token') and tmp_tools.pagination_token:
                    pagination_token = tmp_tools.pagination_token
                else:
                    more_tools = False
            else:
                # Fallback - treat as single tool or list
                if tmp_tools:
                    tools.extend([tmp_tools] if not hasattr(tmp_tools, '__iter__') else tmp_tools)
                more_tools = False
                
        print(f"✅ Retrieved {len(tools)} MCP tools total")
        return tools
        
    except Exception as e:
        print(f"⚠️  Error in get_full_tools_list: {e}")
        # Fallback to simple list_tools_sync
        try:
            simple_tools = client.list_tools_sync()
            return simple_tools if hasattr(simple_tools, '__iter__') else [simple_tools] if simple_tools else []
        except Exception as fallback_error:
            print(f"⚠️  Fallback also failed: {fallback_error}")
            return []

def create_tools_list():
    """Create the list of tools for the agent."""
    tools_list = [websearch, list_mcp_tools]
    
    # Add MCP tools if available
    if mcp_client:
        try:
            mcp_tools = get_full_tools_list(mcp_client)
            tools_list.extend(mcp_tools)
            print(f"✅ Added {len(mcp_tools)} MCP tools (with pagination support)")
        except Exception as e:
            print(f"⚠️  Could not get MCP tools: {e}")
    
    return tools_list

def create_devops_agent() -> Agent:
    """Create and configure the DevOps agent."""
    hooks = create_agent_hooks(memory_id)
    
    return Agent(
        model=model,
        hooks=hooks,
        system_prompt="""You are AWS DevOps agent. Help with AWS infrastructure and operations.

CRITICAL EFFICIENCY RULES:
- Answer from knowledge FIRST before using tools
- Use tools ONLY when you need current/specific data
- MAXIMUM 1 tool call per response
- Keep responses under 300 words
- Be direct and actionable

NON-FUNCTIONAL RULES:
- Be friendly, patient, and understanding with users
- Always offer additional help after answering questions
- If you can't help with something, direct users to the appropriate contact
""",
        tools=create_tools_list(),
    )

class ConversationManager:
    """Manages the interactive conversation loop."""
    
    def __init__(self, agent: Agent, bot_name: str = "AWS-DevOps-agent"):
        self.agent = agent
        self.bot_name = bot_name
        self.exit_commands = {'exit', 'quit', 'bye'}
    
    def start_conversation(self):
        """Start the interactive conversation loop."""
        print(f"\n🚀 {self.bot_name}: Ask me about DevOps on AWS! Type 'exit' to quit.\n")
        
        try:
            while True:
                try:
                    user_input = input("\nYou > ").strip()
                    
                    if user_input.lower() in self.exit_commands:
                        print("Happy DevOpsing!")
                        break
                        
                    if not user_input:
                        print(f"\n{self.bot_name} > Please ask me something about DevOps on AWS!")
                        continue
                    
                    response = self.agent(user_input)
                    print(f"\n{self.bot_name} > {response}")
                    
                except KeyboardInterrupt:
                    print("\n\nGoodbye! Happy DevOpsing!")
                    break
                except Exception as e:
                    logger.error(f"Error processing user input: {e}")
                    print(f"\n{self.bot_name} > Sorry, I encountered an error: {e}")
                    
        except Exception as e:
            logger.error(f"Fatal error in conversation loop: {e}")
            print(f"Fatal error: {e}")

def setup_gateway_parameters():
    """Interactive setup for gateway SSM parameters."""
    print("\n🔧 Gateway Configuration Setup")
    print("=" * 50)
    print("ℹ️  Using manually created gateway: devopsagent-agentcore-gw-1xgl5imapz")
    print("   Gateway was created via AWS Management Console")
    
    # Check current gateway status
    manual_gateway_id = "devopsagent-agentcore-gw-1xgl5imapz"
    gateway_client = boto3.client("bedrock-agentcore-control", region_name=REGION)
    
    try:
        gateway_response = gateway_client.get_gateway(gatewayIdentifier=manual_gateway_id)
        print(f"\n✅ Manual Gateway Status:")
        print(f"   Gateway ID: {manual_gateway_id}")
        print(f"   Name: {gateway_response['name']}")
        print(f"   Status: {gateway_response.get('status', 'ACTIVE')}")
        print(f"   URL: {gateway_response['gatewayUrl']}")
    except Exception as e:
        print(f"\n⚠️  Could not retrieve manual gateway details: {e}")
    
    # Check current parameters
    params_to_check = {
        "/app/devopsagent/agentcore/machine_client_id": "Cognito Machine Client ID",
        "/app/devopsagent/agentcore/cognito_discovery_url": "OIDC Discovery URL",
        "/app/devopsagent/agentcore/gateway_iam_role": "Gateway IAM Role ARN",
        "/app/devopsagent/agentcore/gateway_id": "Gateway ID (Auto-managed)"
    }
    
    for param_path, description in params_to_check.items():
        current_value = get_ssm_parameter(param_path)
        print(f"\n{description}:")
        print(f"  Parameter: {param_path}")
        print(f"  Current value: {current_value or 'NOT SET'}")
        
        if param_path.endswith("cognito_discovery_url") and current_value:
            if "example.com" in current_value:
                print("  ❌ This appears to be a placeholder value")
            else:
                # Test the URL
                is_valid, message = validate_discovery_url(current_value)
                if is_valid:
                    print("  ✅ URL is accessible and returns valid OIDC configuration")
                else:
                    print(f"  ❌ URL validation failed: {message}")
    
    print(f"\n💡 Manual Gateway Benefits:")
    print(f"   • Gateway created successfully via AWS Management Console")
    print(f"   • Bypasses automatic creation validation issues")
    print(f"   • Enables advanced MCP (Model Context Protocol) integrations")
    
    print(f"\n🚀 Agent Status:")
    print(f"   The agent works with full functionality including gateway support!")

def main():
    """Main execution function."""
    import sys
    
    # Check for setup command
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_gateway_parameters()
        return
    
    agent = create_devops_agent()
    conversation_manager = ConversationManager(agent)
    conversation_manager.start_conversation()

if __name__ == "__main__":
    main()