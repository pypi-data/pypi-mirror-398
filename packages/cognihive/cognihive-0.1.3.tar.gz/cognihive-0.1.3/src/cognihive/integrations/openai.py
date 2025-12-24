"""
OpenAI Assistants API integration for CogniHive.

Provides function tools for OpenAI Assistants to access 
transactive memory capabilities: who_knows, remember, recall.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from cognihive.core.hive import Hive
from cognihive.core.agent_registry import Agent


# OpenAI Function Tool Schemas
COGNIHIVE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "who_knows",
            "description": "Find which team member/agent is the expert on a specific topic. Returns a list of experts ranked by their expertise score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to find experts for, e.g., 'python optimization', 'database queries', 'react components'"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Store a piece of knowledge or information that should be remembered for future reference. Associates the memory with the current agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The knowledge or information to remember"
                    },
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of topics this memory relates to, e.g., ['python', 'performance']"
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Search for relevant memories and knowledge based on a query. Returns memories that semantically match the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant memories"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_expert",
            "description": "Route a question to the most appropriate expert and get relevant memories. Combines expert finding with memory retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to route to an expert"
                    }
                },
                "required": ["question"]
            }
        }
    }
]


class OpenAIHive:
    """CogniHive wrapper for OpenAI Assistants API integration.
    
    Provides function tools that OpenAI Assistants can use to access
    CogniHive's transactive memory capabilities.
    
    Example:
        ```python
        from openai import OpenAI
        from cognihive.integrations import OpenAIHive
        
        client = OpenAI()
        hive = OpenAIHive()
        
        # Create assistant with CogniHive tools
        assistant = client.beta.assistants.create(
            name="Team Assistant",
            instructions="You help coordinate a software team.",
            tools=hive.get_tools(),
            model="gpt-4-turbo-preview"
        )
        
        # When processing tool calls:
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            output = hive.process_tool_call(tool_call)
            # Submit output back to the run
        ```
    """
    
    def __init__(
        self,
        name: str = "openai_hive",
        persist_directory: Optional[str] = None,
        default_agent: str = "assistant",
        **kwargs
    ):
        """Initialize OpenAI-compatible Hive.
        
        Args:
            name: Name of the hive
            persist_directory: Path for persistent storage
            default_agent: Default agent name for memories
            **kwargs: Additional arguments passed to Hive
        """
        self.hive = Hive(
            name=name,
            persist_directory=persist_directory,
            **kwargs
        )
        self.default_agent = default_agent
        self._current_agent = default_agent
        
        # Register default agent
        self.hive.register_agent(
            name=default_agent,
            expertise=["general"],
            role="OpenAI Assistant"
        )
    
    def register_assistant(
        self,
        assistant_id: str,
        name: str,
        expertise: Optional[List[str]] = None,
        role: str = ""
    ) -> Agent:
        """Register an OpenAI Assistant as an agent.
        
        Args:
            assistant_id: OpenAI Assistant ID
            name: Friendly name for the agent
            expertise: List of expertise areas
            role: Agent's role description
            
        Returns:
            Registered Agent object
        """
        return self.hive.register_agent(
            name=name,
            expertise=expertise or [],
            role=role,
            metadata={"openai_assistant_id": assistant_id}
        )
    
    def set_current_agent(self, agent_name: str) -> None:
        """Set the current agent for memory operations.
        
        Args:
            agent_name: Name of the agent to use for remember/recall
        """
        self._current_agent = agent_name
    
    def get_tools(self) -> List[Dict]:
        """Get OpenAI function tool schemas.
        
        Returns:
            List of tool definitions for OpenAI Assistants API
        """
        return COGNIHIVE_TOOLS
    
    def process_tool_call(
        self,
        tool_call: Any,
        agent_name: Optional[str] = None
    ) -> str:
        """Process an OpenAI tool call and return the result.
        
        Args:
            tool_call: OpenAI tool call object (has .function.name and .function.arguments)
            agent_name: Override agent for this call
            
        Returns:
            JSON string result to send back to OpenAI
        """
        agent = agent_name or self._current_agent
        
        # Parse the function call
        func_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        # Route to appropriate handler
        if func_name == "who_knows":
            result = self._handle_who_knows(arguments)
        elif func_name == "remember":
            result = self._handle_remember(arguments, agent)
        elif func_name == "recall":
            result = self._handle_recall(arguments, agent)
        elif func_name == "ask_expert":
            result = self._handle_ask_expert(arguments)
        else:
            result = {"error": f"Unknown function: {func_name}"}
        
        return json.dumps(result)
    
    def _handle_who_knows(self, arguments: Dict) -> Dict:
        """Handle who_knows function call."""
        topic = arguments.get("topic", "")
        if not topic:
            return {"error": "Topic is required"}
        
        experts = self.hive.who_knows(topic)
        
        return {
            "topic": topic,
            "experts": [
                {"agent": name, "expertise_score": round(score, 2)}
                for name, score in experts
            ],
            "recommendation": experts[0][0] if experts else None
        }
    
    def _handle_remember(self, arguments: Dict, agent: str) -> Dict:
        """Handle remember function call."""
        content = arguments.get("content", "")
        if not content:
            return {"error": "Content is required"}
        
        topics = arguments.get("topics", [])
        
        memory = self.hive.remember(
            content=content,
            agent=agent,
            topics=topics
        )
        
        return {
            "success": True,
            "memory_id": memory.id,
            "agent": agent,
            "topics": topics
        }
    
    def _handle_recall(self, arguments: Dict, agent: str) -> Dict:
        """Handle recall function call."""
        query = arguments.get("query", "")
        if not query:
            return {"error": "Query is required"}
        
        top_k = arguments.get("top_k", 5)
        
        results = self.hive.recall(query, agent=None, top_k=top_k)  # Search all agents
        
        memories = []
        for memory, score in results:
            memories.append({
                "content": memory.content,
                "agent": memory.owner_name,
                "topics": memory.topics,
                "relevance_score": round(score, 2)
            })
        
        return {
            "query": query,
            "memories": memories,
            "count": len(memories)
        }
    
    def _handle_ask_expert(self, arguments: Dict) -> Dict:
        """Handle ask_expert function call."""
        question = arguments.get("question", "")
        if not question:
            return {"error": "Question is required"}
        
        result = self.hive.ask(question)
        
        memories = []
        for memory in result.get("memories", []):
            memories.append({
                "content": memory.content,
                "agent": memory.owner_name,
                "topics": memory.topics
            })
        
        return {
            "question": question,
            "expert": result.get("expert"),
            "confidence": round(result.get("confidence", 0), 2),
            "reasoning": result.get("reasoning"),
            "secondary_experts": result.get("secondary_experts", []),
            "relevant_memories": memories
        }
    
    # Convenience methods that mirror Hive API
    
    def who_knows(self, topic: str) -> List[tuple]:
        """Find experts on a topic."""
        return self.hive.who_knows(topic)
    
    def remember(
        self,
        content: str,
        topics: Optional[List[str]] = None,
        agent: Optional[str] = None
    ):
        """Store a memory."""
        return self.hive.remember(
            content=content,
            agent=agent or self._current_agent,
            topics=topics
        )
    
    def recall(self, query: str, top_k: int = 5):
        """Recall memories."""
        return self.hive.recall(query, top_k=top_k)
    
    def ask(self, question: str):
        """Ask the hive and route to expert."""
        return self.hive.ask(question)


# Helper function to create tool outputs for OpenAI API
def create_tool_outputs(
    hive: OpenAIHive,
    tool_calls: List[Any],
    agent_name: Optional[str] = None
) -> List[Dict]:
    """Process multiple tool calls and return outputs for OpenAI API.
    
    Args:
        hive: OpenAIHive instance
        tool_calls: List of tool call objects from OpenAI run
        agent_name: Optional agent name override
        
    Returns:
        List of tool outputs ready for submit_tool_outputs
        
    Example:
        ```python
        if run.required_action:
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            outputs = create_tool_outputs(hive, tool_calls)
            
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )
        ```
    """
    outputs = []
    for tool_call in tool_calls:
        output = hive.process_tool_call(tool_call, agent_name)
        outputs.append({
            "tool_call_id": tool_call.id,
            "output": output
        })
    return outputs
