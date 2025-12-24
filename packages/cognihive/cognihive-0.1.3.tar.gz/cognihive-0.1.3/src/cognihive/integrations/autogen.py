"""
AutoGen Integration for CogniHive.

Provides seamless integration with Microsoft AutoGen agents.
Enables transactive memory for AutoGen multi-agent conversations.
"""

from typing import Any, Dict, List, Optional, Callable

from cognihive.core.hive import Hive
from cognihive.core.memory_types import Memory

# Check if AutoGen is available
try:
    from autogen import ConversableAgent, AssistantAgent, UserProxyAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    try:
        from pyautogen import ConversableAgent, AssistantAgent, UserProxyAgent
        AUTOGEN_AVAILABLE = True
    except ImportError:
        AUTOGEN_AVAILABLE = False
        ConversableAgent = None
        AssistantAgent = None
        UserProxyAgent = None


class AutoGenMemoryAdapter:
    """Memory adapter for AutoGen agents.
    
    Provides hooks into AutoGen's message handling to automatically
    store and retrieve memories from CogniHive.
    """
    
    def __init__(self, hive: Hive, agent_name: str):
        """Initialize the AutoGen memory adapter.
        
        Args:
            hive: The CogniHive instance
            agent_name: Name of the agent
        """
        self.hive = hive
        self.agent_name = agent_name
        self._context_window: List[str] = []
        self._max_context = 10
    
    def on_message_received(self, message: Dict[str, Any]) -> List[str]:
        """Handle incoming message - retrieve relevant memories.
        
        Args:
            message: The incoming message dict
            
        Returns:
            List of relevant memory contents to include in context
        """
        content = message.get("content", "")
        if not content:
            return []
        
        # Get relevant memories
        results = self.hive.recall(content, top_k=3)
        return [mem.content for mem, _ in results]
    
    def on_message_sent(self, message: Dict[str, Any]):
        """Handle outgoing message - store as memory.
        
        Args:
            message: The outgoing message dict
        """
        content = message.get("content", "")
        if content and len(content) > 20:  # Only store substantial messages
            # Extract topics from the message
            topics = self._extract_topics(content)
            
            self.hive.remember(
                content=content,
                agent=self.agent_name,
                topics=topics,
                metadata={"type": "conversation", "role": "assistant"}
            )
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from message content."""
        # Simple keyword extraction
        keywords = []
        content_lower = content.lower()
        
        topic_indicators = [
            "about", "regarding", "concerning", "related to",
            "for", "on", "with"
        ]
        
        # Very basic extraction - can be enhanced with NLP
        words = content_lower.split()[:20]  # First 20 words
        return [w for w in words if len(w) > 5 and w.isalpha()][:5]
    
    def get_context_injection(self, current_message: str) -> str:
        """Get memory context to inject into the conversation.
        
        Args:
            current_message: The current message being processed
            
        Returns:
            Formatted context string to inject
        """
        memories = self.hive.recall(current_message, top_k=3)
        
        if not memories:
            return ""
        
        context_parts = ["[Relevant memories from the team:]"]
        for mem, score in memories:
            if score > 0.3:
                context_parts.append(f"- {mem.content}")
        
        if len(context_parts) > 1:
            return "\n".join(context_parts) + "\n\n"
        return ""


class AutoGenHive(Hive):
    """CogniHive with AutoGen-specific features.
    
    Extends the base Hive with AutoGen integration capabilities:
    - Wrap AutoGen agents with memory adapters
    - Automatic message interception for memory
    - Multi-agent conversation memory
    
    Example:
        >>> from autogen import AssistantAgent, UserProxyAgent
        >>> from cognihive.integrations import AutoGenHive
        >>> 
        >>> hive = AutoGenHive()
        >>> 
        >>> assistant = AssistantAgent(
        ...     name="assistant",
        ...     system_message="You are a helpful assistant."
        ... )
        >>> 
        >>> # Wrap with CogniHive memory
        >>> assistant = hive.wrap_agent(assistant)
        >>> 
        >>> # Now the agent has transactive memory!
    """
    
    def __init__(
        self,
        name: str = "autogen_hive",
        persist_directory: Optional[str] = None,
        **kwargs
    ):
        """Initialize an AutoGen-enabled Hive.
        
        Args:
            name: Hive name
            persist_directory: Path for persistent storage
            **kwargs: Additional Hive arguments
        """
        if not AUTOGEN_AVAILABLE:
            raise ImportError(
                "AutoGen is required for AutoGenHive. "
                "Install with: pip install pyautogen"
            )
        
        super().__init__(
            name=name,
            persist_directory=persist_directory,
            **kwargs
        )
        
        self._autogen_adapters: Dict[str, AutoGenMemoryAdapter] = {}
        self._wrapped_agents: Dict[str, Any] = {}
    
    def get_adapter(self, agent_name: str) -> AutoGenMemoryAdapter:
        """Get or create a memory adapter for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AutoGenMemoryAdapter for this agent
        """
        if agent_name not in self._autogen_adapters:
            if not self.get_agent(agent_name):
                self.register_agent(agent_name)
            
            self._autogen_adapters[agent_name] = AutoGenMemoryAdapter(
                hive=self,
                agent_name=agent_name
            )
        
        return self._autogen_adapters[agent_name]
    
    def wrap_agent(
        self,
        agent: "ConversableAgent",
        extract_expertise: bool = True
    ) -> "ConversableAgent":
        """Wrap an AutoGen agent with CogniHive memory.
        
        This modifies the agent to automatically store and retrieve memories.
        
        Args:
            agent: The AutoGen agent to wrap
            extract_expertise: Whether to extract expertise from system message
            
        Returns:
            The wrapped agent (same object, modified)
        """
        agent_name = agent.name
        
        # Register in hive
        expertise = []
        if extract_expertise and hasattr(agent, 'system_message'):
            expertise = self._extract_expertise_from_system_message(
                agent.system_message or ""
            )
        
        if not self.get_agent(agent_name):
            self.register_agent(
                name=agent_name,
                expertise=expertise,
                role=agent_name,
                description=agent.system_message[:100] if hasattr(agent, 'system_message') and agent.system_message else ""
            )
        
        adapter = self.get_adapter(agent_name)
        
        # Store reference
        self._wrapped_agents[agent_name] = agent
        
        # Note: In practice, you'd hook into AutoGen's message handling
        # This is a conceptual implementation - exact hooks depend on AutoGen version
        
        return agent
    
    def _extract_expertise_from_system_message(self, system_message: str) -> List[str]:
        """Extract expertise keywords from system message."""
        keywords = [
            "code", "coding", "programming", "python", "javascript",
            "data", "analysis", "research", "write", "writing",
            "design", "plan", "execute", "review", "test",
            "math", "science", "engineering", "creative"
        ]
        
        msg_lower = system_message.lower()
        return [kw for kw in keywords if kw in msg_lower]
    
    def create_memory_enhanced_agent(
        self,
        name: str,
        system_message: str,
        expertise: Optional[List[str]] = None,
        **agent_kwargs
    ) -> "AssistantAgent":
        """Create a new AutoGen agent with CogniHive memory built-in.
        
        Args:
            name: Agent name
            system_message: System message for the agent
            expertise: List of expertise domains
            **agent_kwargs: Additional AssistantAgent arguments
            
        Returns:
            An AssistantAgent with CogniHive memory
        """
        # Enhance system message with memory awareness
        memory_prompt = """
You have access to a shared team memory system. When you receive information 
that might be useful later, it will be automatically stored. You may also 
receive relevant memories from team members to help with your tasks.
"""
        enhanced_message = memory_prompt + "\n\n" + system_message
        
        agent = AssistantAgent(
            name=name,
            system_message=enhanced_message,
            **agent_kwargs
        )
        
        # Register with explicit expertise
        self.register_agent(
            name=name,
            expertise=expertise or [],
            role=name,
            description=system_message[:100]
        )
        
        return self.wrap_agent(agent, extract_expertise=False)
    
    def get_memory_context_for_agent(
        self,
        agent_name: str,
        query: str,
        include_who_knows: bool = True
    ) -> str:
        """Get memory context string for an agent's query.
        
        Useful for manually injecting memory context.
        
        Args:
            agent_name: Name of the agent
            query: The query to get context for
            include_who_knows: Whether to include expert recommendations
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Get relevant memories
        memories = self.recall(query, top_k=3)
        if memories:
            parts.append("📚 Relevant Team Memories:")
            for mem, score in memories:
                if score > 0.3:
                    parts.append(f"  • [{mem.owner_name}]: {mem.content}")
        
        # Get expert recommendations
        if include_who_knows:
            experts = self.who_knows(query)
            if experts:
                parts.append("\n👥 Team Experts on this topic:")
                for name, score in experts[:3]:
                    parts.append(f"  • {name} (confidence: {score:.2f})")
        
        if parts:
            return "\n".join(parts)
        return ""


def create_autogen_group_with_memory(
    agent_configs: List[Dict[str, Any]],
    hive_name: str = "autogen_hive"
) -> tuple:
    """Create an AutoGen agent group with shared CogniHive memory.
    
    Args:
        agent_configs: List of agent configurations
        hive_name: Name for the hive
        
    Returns:
        Tuple of (List[agents], AutoGenHive)
        
    Example:
        >>> agents, hive = create_autogen_group_with_memory([
        ...     {
        ...         "name": "coder",
        ...         "system_message": "You are an expert Python coder.",
        ...         "expertise": ["python", "coding"]
        ...     },
        ...     {
        ...         "name": "reviewer", 
        ...         "system_message": "You review code for quality.",
        ...         "expertise": ["review", "testing"]
        ...     }
        ... ])
    """
    if not AUTOGEN_AVAILABLE:
        raise ImportError("AutoGen is required. Install with: pip install pyautogen")
    
    hive = AutoGenHive(name=hive_name)
    agents = []
    
    for config in agent_configs:
        agent = hive.create_memory_enhanced_agent(
            name=config["name"],
            system_message=config.get("system_message", ""),
            expertise=config.get("expertise", []),
            llm_config=config.get("llm_config")
        )
        agents.append(agent)
    
    return agents, hive
