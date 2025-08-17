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
    
    # AWS Settings
    DEFAULT_REGION = 'us-east-1'
    
    # Model Settings
    MODEL_ID = 'us.anthropic.claude-sonnet-4-20250514-v1:0'
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

# Initialize configuration
REGION = AgentConfig.setup_aws_region()

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


# Define a websearch tool
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
model = BedrockModel(
    model_id=AgentConfig.MODEL_ID, 
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
        tools=[websearch],
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

def main():
    """Main execution function."""
    agent = create_devops_agent()
    conversation_manager = ConversationManager(agent)
    conversation_manager.start_conversation()

if __name__ == "__main__":
    main()