import logging
import os
import uuid

# Import boto libraries and AWS tools
import boto3
from boto3.session import Session
from utils import get_ssm_parameter, put_ssm_parameter

# Import DDGS
from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException

# Import Strands, BedrockModel
from strands.agent import Agent
from strands.tools import tool
from strands.hooks import AfterInvocationEvent, HookProvider, HookRegistry, MessageAddedEvent
from strands.models.bedrock import BedrockModel

# Import agentCore Memory
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType

class AgentConfig:
    """Configuration settings for the DevOps Agent."""
    
    def __init__(self):
        self.aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        os.environ['AWS_DEFAULT_REGION'] = self.aws_region
        
        self.boto_session = Session()
        self.region = self.boto_session.region_name
        
        # Model settings
        self.model_id = 'us.anthropic.claude-sonnet-4-20250514-v1:0'
        self.model_temperature = MODEL_TEMPERATURE
        
        # Memory settings
        self.memory_name = MEMORY_NAME
        self.ssm_memory_id_path = SSM_MEMORY_ID_PATH
        self.devops_user_id = DEVOPS_USER_ID
        self.memory_expiry_days = MEMORY_EXPIRY_DAYS
        
        # Search settings
        self.search_region = "us-en"
        self.max_search_results = MAX_SEARCH_RESULTS_DEFAULT

# Initialize configuration
config = AgentConfig()
REGION = config.region

# Configure logging
logging.getLogger("strands").setLevel(
    logging.INFO
)  # Set to DEBUG for more detailed logs

logger = logging.getLogger(__name__)


# Define a websearch tool
@tool
def websearch(
    keywords: str, region: str = "us-en", max_results: int | None = MAX_SEARCH_RESULTS_DEFAULT
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
        
        # Format results for better readability
        formatted_results = _format_search_results(results)
        logger.info(f"Found {len(results)} search results")
        return formatted_results
        
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


def create_bedrock_model(model_id: str = 'us.anthropic.claude-sonnet-4-20250514-v1:0', 
                        temperature: float = MODEL_TEMPERATURE) -> BedrockModel:
    """Create a Bedrock model instance with temperature control.
    
    Temperature guidelines:
    - 0.1-0.3: Very focused, ideal for technical accuracy
    - 0.4-0.7: Balanced creativity and accuracy
    - 0.8-1.0: Creative responses
    
    Args:
        model_id: The Bedrock model identifier
        temperature: Model temperature for response generation
        
    Returns:
        Configured BedrockModel instance
    """
    return BedrockModel(model_id=model_id, temperature=temperature)

# Create a Bedrock model instance
model = create_bedrock_model()

# Constants
MEMORY_NAME = "DevOpsAgentMemory"
SSM_MEMORY_ID_PATH = "/app/devopsagent/agentcore/memory_id"
DEVOPS_USER_ID = "devops_001"
MEMORY_EXPIRY_DAYS = 90
MODEL_TEMPERATURE = 0.3
MAX_SEARCH_RESULTS_DEFAULT = None
CONTEXT_RETRIEVAL_TOP_K = 3

# AgentCore Memory section
memory_client = MemoryClient(region_name=REGION)

def _get_memory_from_ssm() -> str | None:
    """Retrieve and verify memory ID from SSM Parameter Store."""
    try:
        memory_id = get_ssm_parameter(SSM_MEMORY_ID_PATH)
        if memory_id:
            logger.info(f"Found memory ID in SSM: {memory_id}")
            # Verify the memory exists
            try:
                memory_client.gmcp_client.get_memory(memoryId=memory_id)
                logger.info("Memory verified successfully")
                return memory_id
            except Exception as verify_error:
                logger.warning(f"Memory ID from SSM is invalid: {verify_error}")
        return None
    except Exception as e:
        logger.warning(f"Could not retrieve memory ID from SSM: {e}")
        return None

def _find_existing_memory() -> str | None:
    """Search for existing memory by name or pattern."""
    try:
        logger.info("Searching for existing memory...")
        memories = memory_client.gmcp_client.list_memories()
        logger.info(f"Found {len(memories.get('memories', []))} total memories")
        
        for memory in memories.get('memories', []):
            memory_id = memory.get('id')
            memory_name_from_api = memory.get('name')
            memory_status = memory.get('status')
            
            logger.debug(f"Memory ID: {memory_id}, Name: {memory_name_from_api}, Status: {memory_status}")
            
            # Skip memories that are being deleted
            if memory_status == 'DELETING':
                continue
            
            # Check if this matches our target memory by name
            if memory_name_from_api == MEMORY_NAME:
                logger.info(f"Found existing memory by name: {memory_id}")
                _save_memory_id_to_ssm(memory_id)
                return memory_id
            
            # Check if this matches by ID pattern (fallback for memories with None name)
            elif (memory_name_from_api is None and 
                  MEMORY_NAME in memory_id and 
                  memory_status == 'ACTIVE'):
                logger.info(f"Found existing memory by ID pattern: {memory_id}")
                _save_memory_id_to_ssm(memory_id)
                return memory_id
        
        logger.info("No existing memory found by name or pattern")
        return None
    except Exception as e:
        logger.error(f"Could not list existing memories: {e}")
        return None

def _save_memory_id_to_ssm(memory_id: str) -> None:
    """Save memory ID to SSM Parameter Store."""
    try:
        put_ssm_parameter(SSM_MEMORY_ID_PATH, memory_id)
        logger.info("Saved memory ID to SSM")
    except Exception as ssm_error:
        logger.warning(f"Could not save memory ID to SSM: {ssm_error}")

def _create_memory_strategies() -> list:
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

def _create_new_memory() -> str | None:
    """Create a new memory resource."""
    try:
        logger.info("Creating new AgentCore Memory resource...")
        strategies = _create_memory_strategies()
        
        logger.info("Creating AgentCore Memory resources. This can take a couple of minutes...")
        # *** AGENTCORE MEMORY USAGE *** - Create memory resource with semantic strategy
        response = memory_client.create_memory_and_wait(
            name=MEMORY_NAME,
            description="DevOps Agent memory",
            strategies=strategies,
            event_expiry_days=MEMORY_EXPIRY_DAYS,
        )
        memory_id = response["id"]
        logger.info(f"Successfully created memory: {memory_id}")
        
        _save_memory_id_to_ssm(memory_id)
        return memory_id
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        return None

def create_or_get_memory_resource() -> str | None:
    """Get existing memory or create new one."""
    logger.info("Attempting to retrieve or create AgentCore Memory resource...")
    
    # Step 1: Try to get existing memory ID from SSM
    memory_id = _get_memory_from_ssm()
    if memory_id:
        return memory_id
    
    # Step 2: Try to find existing memory by name or ID pattern
    memory_id = _find_existing_memory()
    if memory_id:
        return memory_id
    
    # Step 3: Create new memory if none exists
    return _create_new_memory()

def _handle_memory_initialization_error():
    """Handle memory initialization failure with helpful error messages."""
    error_messages = [
        "ERROR: Failed to create or retrieve memory resource",
        "Possible causes:",
        "1. AWS credentials not configured or insufficient permissions",
        "2. AgentCore Memory service not available in your region",
        "3. Network connectivity issues", 
        "4. SSM parameter store access issues",
        "\nThe agent will continue without memory functionality..."
    ]
    for msg in error_messages:
        logger.error(msg) if msg.startswith("ERROR") else logger.warning(msg)

# Initialize memory
memory_id = create_or_get_memory_resource()
if not memory_id:
    _handle_memory_initialization_error()
else:
    logger.info(f"AgentCore Memory ready with ID: {memory_id}")

class DevOpsAgentMemoryHooks(HookProvider):
    """Memory hooks for DevOps Agent with context retrieval and interaction persistence."""

    def __init__(self, memory_id: str, client: MemoryClient, actor_id: str, session_id: str):
        self.memory_id = memory_id
        self.client = client
        self.actor_id = actor_id
        self.session_id = session_id
        self._namespaces = None
    
    @property
    def namespaces(self) -> dict:
        """Lazy load namespaces to avoid initialization issues."""
        if self._namespaces is None:
            try:
                strategies = self.client.get_memory_strategies(self.memory_id)
                self._namespaces = {
                    strategy["type"]: strategy["namespaces"][0]
                    for strategy in strategies
                }
            except Exception as e:
                logger.error(f"Failed to load memory strategies: {e}")
                self._namespaces = {}
        return self._namespaces

    def _is_user_query(self, messages: list) -> bool:
        """Check if the last message is a user query (not a tool result)."""
        if not messages:
            return False
        last_message = messages[-1]
        return (last_message.get("role") == "user" and 
                "toolResult" not in last_message.get("content", [{}])[0])
    
    def _format_memory_context(self, memories: list, context_type: str) -> list:
        """Format memories into context strings."""
        context_items = []
        for memory in memories:
            if isinstance(memory, dict):
                content = memory.get("content", {})
                if isinstance(content, dict):
                    text = content.get("text", "").strip()
                    if text:
                        context_items.append(f"[{context_type.upper()}] {text}")
        return context_items
    
    def _inject_context_into_query(self, messages: list, context_items: list) -> None:
        """Inject context into the user query."""
        if context_items:
            context_text = "\n".join(context_items)
            original_text = messages[-1]["content"][0]["text"]
            messages[-1]["content"][0]["text"] = (
                f"DevOps Context:\n{context_text}\n\n{original_text}"
            )

    def retrieve_devops_context(self, event: MessageAddedEvent):
        """Retrieve DevOps context before processing query."""
        messages = event.agent.messages
        
        if not self._is_user_query(messages):
            return
            
        user_query = messages[-1]["content"][0]["text"]
        
        try:
            all_context = []
            
            for context_type, namespace in self.namespaces.items():
                # *** AGENTCORE MEMORY USAGE *** - Retrieve DevOps context from each namespace
                memories = self.client.retrieve_memories(
                    memory_id=self.memory_id,
                    namespace=namespace.format(actorId=self.actor_id),
                    query=user_query,
                    top_k=CONTEXT_RETRIEVAL_TOP_K,
                )
                context_items = self._format_memory_context(memories, context_type)
                all_context.extend(context_items)
            
            self._inject_context_into_query(messages, all_context)
            
            if all_context:
                logger.info(f"Retrieved {len(all_context)} DevOps context items")
                
        except Exception as e:
            logger.error(f"Failed to retrieve DevOps context: {e}")

    def _extract_interaction_pair(self, messages: list) -> tuple[str | None, str | None]:
        """Extract the last user query and agent response pair."""
        if len(messages) < 2 or messages[-1]["role"] != "agent":
            return None, None
            
        user_query = None
        agent_response = messages[-1]["content"][0]["text"]
        
        # Find the corresponding user query
        for msg in reversed(messages[:-1]):  # Skip the last agent message
            if (msg["role"] == "user" and 
                "toolResult" not in msg.get("content", [{}])[0]):
                user_query = msg["content"][0]["text"]
                break
        
        return user_query, agent_response

    def save_devops_interaction(self, event: AfterInvocationEvent):
        """Save DevOps Agent interaction after agent response."""
        try:
            messages = event.agent.messages
            user_query, agent_response = self._extract_interaction_pair(messages)
            
            if user_query and agent_response:
                # *** AGENTCORE MEMORY USAGE *** - Save the DevOps interaction
                self.client.create_event(
                    memory_id=self.memory_id,
                    actor_id=self.actor_id,
                    session_id=self.session_id,
                    messages=[
                        (user_query, "USER"),
                        (agent_response, "AGENT"),
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

# Only create memory hooks if memory_id is available
hooks = []
if memory_id:
    memory_hooks = DevOpsAgentMemoryHooks(memory_id, memory_client, DEVOPS_USER_ID, SESSION_ID)
    hooks = [memory_hooks]
    print("Memory hooks enabled")
else:
    print("Running without memory functionality")

# Create an example agent
agent = Agent(
    model=model,
    hooks=hooks, # Pass Memory Hooks only if available
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
    tools=[websearch],
)


class ConversationManager:
    """Manages the interactive conversation loop with the agent."""
    
    def __init__(self, agent, bot_name: str = "AWS-DevOps-Agent"):
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
                    
                    self._process_user_input(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\nGoodbye! Happy DevOpsing!")
                    break
                except Exception as e:
                    self._handle_input_error(e)
                    
        except Exception as e:
            logger.error(f"Fatal error in conversation loop: {e}")
            print(f"Fatal error: {e}")
    
    def _process_user_input(self, user_input: str):
        """Process a single user input."""
        logger.info(f"Processing user query: {user_input[:50]}...")
        response = self.agent(user_input)
        print(f"\n{self.bot_name} > {response}")
    
    def _handle_input_error(self, error: Exception):
        """Handle errors during input processing."""
        logger.error(f"Error processing user input: {error}")
        print(f"\n{self.bot_name} > Sorry, I encountered an error: {error}")


def main():
    """Main execution function."""
    conversation_manager = ConversationManager(agent)
    conversation_manager.start_conversation()

if __name__ == "__main__":
    main()