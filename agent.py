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

# Set AWS region
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
boto_session = Session()
REGION = boto_session.region_name

# Configure logging
logging.getLogger("strands").setLevel(
    logging.INFO
)  # Set to DEBUG for more detailed logs

logger = logging.getLogger(__name__)


# Define a websearch tool
@tool
def websearch(
    keywords: str, region: str = "us-en", max_results: int | None = None
) -> str:
    """Search the web to get updated information.
    Args:
        keywords (str): The search query keywords.
        region (str): The search region: wt-wt, us-en, uk-en, ru-ru, etc..
        max_results (int | None): The maximum number of results to return.
    Returns:
        List of dictionaries with search results.
    """
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        return results if results else "No results found."
    except RatelimitException:
        return "RatelimitException: Please try again after a short delay."
    except DDGSException as d:
        return f"DuckDuckGoSearchException: {d}"
    except Exception as e:
        return f"Exception: {e}"


# Create a Bedrock model instance with temperature control
# Temperature 0.3: Focused and consistent responses, ideal for technical accuracy
# Adjust temperature: 0.1-0.3 (very focused), 0.4-0.7 (balanced), 0.8-1.0 (creative)
model = BedrockModel(
    model_id='us.anthropic.claude-sonnet-4-20250514-v1:0', 
    temperature=0.3
)

# AgentCore Memory section
memory_client = MemoryClient(region_name=REGION)
memory_name = "DevOpsAgentMemory"

def create_or_get_memory_resource():
    print("Attempting to retrieve or create AgentCore Memory resource...")
    
    # Step 1: Try to get existing memory ID from SSM
    try:
        memory_id = get_ssm_parameter("/app/devopsagent/agentcore/memory_id")
        if memory_id:
            print(f"Found memory ID in SSM: {memory_id}")
            # Verify the memory exists
            try:
                memory_client.gmcp_client.get_memory(memoryId=memory_id)
                print("Memory verified successfully")
                return memory_id
            except Exception as verify_error:
                print(f"Memory ID from SSM is invalid: {verify_error}")
                # Continue to next step
    except Exception as e:
        print(f"Could not retrieve memory ID from SSM: {e}")
    
    # Step 2: Try to find existing memory by name or ID pattern
    try:
        print("Searching for existing memory...")
        memories = memory_client.gmcp_client.list_memories()
        print(f"Found {len(memories.get('memories', []))} total memories")
        
        for memory in memories.get('memories', []):
            memory_id = memory.get('id')
            memory_name_from_api = memory.get('name')
            memory_status = memory.get('status')
            
            print(f"  Memory ID: {memory_id}, Name: {memory_name_from_api}, Status: {memory_status}")
            
            # Skip memories that are being deleted
            if memory_status == 'DELETING':
                print(f"    Skipping memory {memory_id} - status is DELETING")
                continue
            
            # Check if this matches our target memory by name
            if memory_name_from_api == memory_name:
                print(f"Found existing memory by name: {memory_id}")
                # Save the ID to SSM for future use
                try:
                    put_ssm_parameter("/app/devopsagent/agentcore/memory_id", memory_id)
                    print("Saved memory ID to SSM")
                except Exception as ssm_error:
                    print(f"Warning: Could not save memory ID to SSM: {ssm_error}")
                return memory_id
            
            # Check if this matches by ID pattern (fallback for memories with None name)
            elif memory_name_from_api is None and memory_name in memory_id and memory_status == 'ACTIVE':
                print(f"Found existing memory by ID pattern: {memory_id}")
                print("  (Memory has None name, likely from previous creation)")
                # Save the ID to SSM for future use
                try:
                    put_ssm_parameter("/app/devopsagent/agentcore/memory_id", memory_id)
                    print("Saved memory ID to SSM")
                except Exception as ssm_error:
                    print(f"Warning: Could not save memory ID to SSM: {ssm_error}")
                return memory_id
        
        print("No existing memory found by name or pattern")
    except Exception as e:
        print(f"Could not list existing memories: {e}")
    
    # Step 3: Create new memory if none exists
    try:
        print("Creating new AgentCore Memory resource...")
        strategies = [
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
        print("Creating AgentCore Memory resources. This can take a couple of minutes...")
        # *** AGENTCORE MEMORY USAGE *** - Create memory resource with semantic strategy
        response = memory_client.create_memory_and_wait(
            name=memory_name,
            description="DevOps Agent memory",
            strategies=strategies,
            event_expiry_days=90,          # Memories expire after 90 days
        )
        memory_id = response["id"]
        print(f"Successfully created memory: {memory_id}")
        
        # Save to SSM
        try:
            put_ssm_parameter("/app/devopsagent/agentcore/memory_id", memory_id)
            print("Saved new memory ID to SSM")
        except Exception as ssm_error:
            print(f"Warning: Could not save memory ID to SSM: {ssm_error}")
        
        return memory_id
    except Exception as e:
        print(f"Failed to create memory: {e}")
        return None

memory_id = create_or_get_memory_resource()
if not memory_id:
    print("ERROR: Failed to create or retrieve memory resource")
    print("Possible causes:")
    print("1. AWS credentials not configured or insufficient permissions")
    print("2. AgentCore Memory service not available in your region")
    print("3. Network connectivity issues")
    print("4. SSM parameter store access issues")
    print("\nThe bot will continue without memory functionality...")
    memory_id = None
else:
    print(f"AgentCore Memory ready with ID: {memory_id}")

DEVOPS_USER_ID = "devops_001"

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
                        top_k=3,
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
    system_prompt="""You are AWS DevOps bot. Help with AWS infrastructure and operations.

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


if __name__ == "__main__":
    print("\n🚀 AWS-DevOps-bot: Ask me about DevOps on AWS! Type 'exit' to quit.\n")

    # Run the agent in a loop for interactive conversation
    while True:
        user_input = input("\nYou > ")
        if user_input.lower() == "exit":
            print("Happy DevOpsing!")
            break
        if not user_input.strip():
            print("\nAWS-DevOps-bot > Please ask me something about DevOps on AWS!")
            continue
        response = agent(user_input)
        print(f"\nAWS-DevOps-bot > {response}")