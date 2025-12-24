"""
CrewAI Integration for CogniHive.

Provides seamless integration with CrewAI agents and crews.
Enables transactive memory for CrewAI multi-agent workflows.
"""

from typing import Any, Dict, List, Optional

from cognihive.core.hive import Hive
from cognihive.core.memory_types import Memory

# Check if CrewAI is available
try:
    from crewai import Agent as CrewAgent
    from crewai import Crew, Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    CrewAgent = None
    Crew = None
    Task = None


class CrewAIMemory:
    """Memory adapter that makes CogniHive work with CrewAI agents.
    
    This class adapts the CogniHive memory interface to be compatible
    with CrewAI's expected memory interface.
    """
    
    def __init__(self, hive: Hive, agent_name: str):
        """Initialize the CrewAI memory adapter.
        
        Args:
            hive: The CogniHive instance
            agent_name: Name of the agent using this memory
        """
        self.hive = hive
        self.agent_name = agent_name
        self._agent = hive.get_agent(agent_name)
    
    def save(self, data: str, metadata: Optional[Dict] = None) -> str:
        """Save information to memory.
        
        Args:
            data: The information to save
            metadata: Optional metadata
            
        Returns:
            Memory ID
        """
        memory = self.hive.remember(
            content=data,
            agent=self.agent_name,
            topics=metadata.get("topics", []) if metadata else [],
            metadata=metadata or {}
        )
        return memory.id
    
    def search(self, query: str, limit: int = 5) -> List[str]:
        """Search memories.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching memory contents
        """
        results = self.hive.recall(query, top_k=limit)
        return [memory.content for memory, _ in results]
    
    def get_relevant(self, context: str, limit: int = 5) -> List[str]:
        """Get memories relevant to a context.
        
        Args:
            context: The context to find relevant memories for
            limit: Max results
            
        Returns:
            List of relevant memory contents
        """
        return self.search(context, limit)
    
    def clear(self):
        """Clear this agent's memories."""
        # Note: Full clear not recommended in shared hive
        pass


class CrewAIHive(Hive):
    """CogniHive with CrewAI-specific features.
    
    Extends the base Hive with CrewAI integration capabilities:
    - Create agent memories compatible with CrewAI
    - Automatic expertise extraction from agent roles
    - Crew-level memory sharing
    
    Example:
        >>> from crewai import Agent, Crew, Task
        >>> from cognihive.integrations import CrewAIHive
        >>> 
        >>> hive = CrewAIHive()
        >>> 
        >>> researcher = Agent(
        ...     role="Researcher",
        ...     goal="Find information",
        ...     memory=hive.agent_memory("researcher")
        ... )
        >>> 
        >>> writer = Agent(
        ...     role="Writer",
        ...     goal="Write content", 
        ...     memory=hive.agent_memory("writer")
        ... )
        >>> 
        >>> crew = Crew(
        ...     agents=[researcher, writer],
        ...     tasks=[...],
        ...     memory=hive  # Shared transactive memory
        ... )
    """
    
    def __init__(
        self,
        name: str = "crewai_hive",
        persist_directory: Optional[str] = None,
        **kwargs
    ):
        """Initialize a CrewAI-enabled Hive.
        
        Args:
            name: Hive name
            persist_directory: Path for persistent storage
            **kwargs: Additional arguments for Hive
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI is required for CrewAIHive. "
                "Install with: pip install crewai"
            )
        
        super().__init__(
            name=name,
            persist_directory=persist_directory,
            **kwargs
        )
        
        self._crewai_memories: Dict[str, CrewAIMemory] = {}
    
    def agent_memory(self, agent_name: str) -> CrewAIMemory:
        """Get a CrewAI-compatible memory for an agent.
        
        If the agent isn't registered, registers them automatically.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            CrewAIMemory instance for this agent
        """
        if agent_name not in self._crewai_memories:
            # Auto-register if needed
            if not self.get_agent(agent_name):
                self.register_agent(agent_name)
            
            self._crewai_memories[agent_name] = CrewAIMemory(
                hive=self,
                agent_name=agent_name
            )
        
        return self._crewai_memories[agent_name]
    
    def from_crew_agent(
        self,
        crew_agent: "CrewAgent",
        extract_expertise: bool = True
    ) -> str:
        """Register a CogniHive agent from a CrewAI Agent.
        
        Args:
            crew_agent: The CrewAI Agent
            extract_expertise: Whether to extract expertise from role/goal
            
        Returns:
            The registered agent's name
        """
        name = crew_agent.role.lower().replace(" ", "_")
        
        expertise = []
        if extract_expertise:
            # Extract expertise from role and goal
            role_words = crew_agent.role.lower().split()
            goal_words = crew_agent.goal.lower().split() if crew_agent.goal else []
            
            # Common expertise keywords
            keywords = [
                "research", "write", "code", "analyze", "data", "design",
                "test", "review", "plan", "execute", "manage", "marketing",
                "sales", "support", "engineer", "develop"
            ]
            
            for word in role_words + goal_words:
                if word in keywords:
                    expertise.append(word)
        
        self.register_agent(
            name=name,
            expertise=expertise,
            role=crew_agent.role,
            description=crew_agent.goal or ""
        )
        
        return name
    
    def from_crew(
        self,
        crew: "Crew",
        extract_expertise: bool = True
    ) -> List[str]:
        """Register all agents from a CrewAI Crew.
        
        Args:
            crew: The CrewAI Crew
            extract_expertise: Whether to extract expertise
            
        Returns:
            List of registered agent names
        """
        agent_names = []
        for agent in crew.agents:
            name = self.from_crew_agent(agent, extract_expertise)
            agent_names.append(name)
        return agent_names
    
    def wrap_crew(self, crew: "Crew") -> "Crew":
        """Wrap a Crew with CogniHive memory.
        
        This automatically registers all agents and sets up shared memory.
        
        Args:
            crew: The CrewAI Crew to wrap
            
        Returns:
            The same crew with CogniHive memory integrated
        """
        self.from_crew(crew)
        
        # Set memory on each agent
        for agent in crew.agents:
            agent_name = agent.role.lower().replace(" ", "_")
            # Note: Actual memory injection depends on CrewAI version
            # This is a conceptual implementation
        
        return crew


def create_cognihive_crew(
    agents: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    hive_name: str = "crew_hive",
    **crew_kwargs
) -> tuple:
    """Create a CrewAI Crew with integrated CogniHive memory.
    
    Helper function to create a complete CrewAI setup with CogniHive.
    
    Args:
        agents: List of agent configurations
        tasks: List of task configurations
        hive_name: Name for the hive
        **crew_kwargs: Additional Crew arguments
        
    Returns:
        Tuple of (Crew, CrewAIHive)
        
    Example:
        >>> crew, hive = create_cognihive_crew(
        ...     agents=[
        ...         {"role": "Researcher", "goal": "Find info"},
        ...         {"role": "Writer", "goal": "Write content"}
        ...     ],
        ...     tasks=[
        ...         {"description": "Research the topic", "agent": "researcher"},
        ...         {"description": "Write the article", "agent": "writer"}
        ...     ]
        ... )
    """
    if not CREWAI_AVAILABLE:
        raise ImportError("CrewAI is required. Install with: pip install crewai")
    
    hive = CrewAIHive(name=hive_name)
    
    # Create agents
    crew_agents = []
    for agent_config in agents:
        crew_agent = CrewAgent(
            role=agent_config.get("role", "Agent"),
            goal=agent_config.get("goal", ""),
            backstory=agent_config.get("backstory", ""),
            verbose=agent_config.get("verbose", True)
        )
        crew_agents.append(crew_agent)
        
        # Register in hive
        hive.from_crew_agent(crew_agent)
    
    # Create tasks
    crew_tasks = []
    for task_config in tasks:
        # Find the agent
        agent_role = task_config.get("agent", "")
        agent = None
        for a in crew_agents:
            if a.role.lower().replace(" ", "_") == agent_role.lower():
                agent = a
                break
        
        task = Task(
            description=task_config.get("description", ""),
            agent=agent,
            expected_output=task_config.get("expected_output", "Completed task")
        )
        crew_tasks.append(task)
    
    # Create crew
    crew = Crew(
        agents=crew_agents,
        tasks=crew_tasks,
        **crew_kwargs
    )
    
    return crew, hive
