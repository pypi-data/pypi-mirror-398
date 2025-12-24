"""
Agent Registry for CogniHive.

Manages agent registration, capabilities, and expertise profiles.
This is the central authority for "who is in the hive".
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from cognihive.core.memory_types import ExpertiseProfile


@dataclass
class Agent:
    """An agent in the CogniHive system.
    
    Agents are the entities that store and retrieve memories.
    Each agent has their own expertise profile that tracks what they know.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    
    # Role and description
    role: str = ""  # e.g., "researcher", "coder", "analyst"
    description: str = ""
    
    # Initial expertise declarations
    declared_expertise: List[str] = field(default_factory=list)
    
    # Computed expertise profile
    expertise_profile: ExpertiseProfile = field(default=None)
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    # Metrics
    memory_count: int = 0
    query_count: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize expertise profile if not provided."""
        if self.expertise_profile is None:
            self.expertise_profile = ExpertiseProfile(
                agent_id=self.id,
                agent_name=self.name
            )
            # Initialize declared expertise
            for domain in self.declared_expertise:
                self.expertise_profile.expertise_domains[domain.lower()] = 0.7
    
    def update_activity(self):
        """Mark the agent as active."""
        self.last_active = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "declared_expertise": self.declared_expertise,
            "is_active": self.is_active,
            "memory_count": self.memory_count,
            "query_count": self.query_count,
            "expertise_domains": self.expertise_profile.expertise_domains,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }


class AgentRegistry:
    """Central registry for all agents in a Hive.
    
    The AgentRegistry manages:
    - Agent registration and lifecycle
    - Expertise profiles
    - Agent lookups and queries
    """
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._name_to_id: Dict[str, str] = {}  # For fast name lookups
    
    def register(
        self,
        name: str,
        expertise: Optional[List[str]] = None,
        role: str = "",
        description: str = "",
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """Register a new agent in the hive.
        
        Args:
            name: Unique name for the agent
            expertise: List of expertise domains (e.g., ["python", "sql"])
            role: Agent's role (e.g., "coder", "analyst")
            description: Description of the agent
            agent_id: Optional explicit ID (auto-generated if not provided)
            metadata: Optional additional metadata
            
        Returns:
            The registered Agent
            
        Raises:
            ValueError: If an agent with this name already exists
        """
        if name in self._name_to_id:
            raise ValueError(f"Agent with name '{name}' already exists")
        
        agent = Agent(
            id=agent_id or str(uuid.uuid4()),
            name=name,
            role=role,
            description=description,
            declared_expertise=expertise or [],
            metadata=metadata or {}
        )
        
        self._agents[agent.id] = agent
        self._name_to_id[name] = agent.id
        
        return agent
    
    def unregister(self, identifier: str) -> bool:
        """Remove an agent from the registry.
        
        Args:
            identifier: Agent ID or name
            
        Returns:
            True if agent was removed, False if not found
        """
        agent_id = self._resolve_identifier(identifier)
        if agent_id and agent_id in self._agents:
            agent = self._agents[agent_id]
            del self._name_to_id[agent.name]
            del self._agents[agent_id]
            return True
        return False
    
    def get(self, identifier: str) -> Optional[Agent]:
        """Get an agent by ID or name.
        
        Args:
            identifier: Agent ID or name
            
        Returns:
            The Agent if found, None otherwise
        """
        agent_id = self._resolve_identifier(identifier)
        return self._agents.get(agent_id) if agent_id else None
    
    def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
    
    def get_by_name(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        agent_id = self._name_to_id.get(name)
        return self._agents.get(agent_id) if agent_id else None
    
    def list_agents(self, active_only: bool = True) -> List[Agent]:
        """List all registered agents.
        
        Args:
            active_only: If True, only return active agents
            
        Returns:
            List of agents
        """
        agents = list(self._agents.values())
        if active_only:
            agents = [a for a in agents if a.is_active]
        return agents
    
    def list_agent_names(self, active_only: bool = True) -> List[str]:
        """List all agent names."""
        return [a.name for a in self.list_agents(active_only)]
    
    def list_agent_ids(self, active_only: bool = True) -> List[str]:
        """List all agent IDs."""
        return [a.id for a in self.list_agents(active_only)]
    
    def update_expertise(
        self,
        identifier: str,
        domain: str,
        score_delta: float
    ) -> bool:
        """Update an agent's expertise score.
        
        Args:
            identifier: Agent ID or name
            domain: The expertise domain
            score_delta: Change in score (positive = increase, negative = decrease)
            
        Returns:
            True if update was successful
        """
        agent = self.get(identifier)
        if agent:
            agent.expertise_profile.update_expertise(domain, score_delta)
            return True
        return False
    
    def get_experts(self, domain: str, min_score: float = 0.3) -> List[tuple]:
        """Find agents with expertise in a domain.
        
        Args:
            domain: The expertise domain to search
            min_score: Minimum expertise score to include
            
        Returns:
            List of (agent, score) tuples, sorted by score descending
        """
        results = []
        domain = domain.lower()
        
        for agent in self.list_agents():
            score = agent.expertise_profile.get_domain_score(domain)
            if score >= min_score:
                results.append((agent, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def count(self, active_only: bool = True) -> int:
        """Get the number of registered agents."""
        return len(self.list_agents(active_only))
    
    def _resolve_identifier(self, identifier: str) -> Optional[str]:
        """Resolve an identifier to an agent ID."""
        # Check if it's already an ID
        if identifier in self._agents:
            return identifier
        # Check if it's a name
        return self._name_to_id.get(identifier)
    
    def __len__(self) -> int:
        return self.count()
    
    def __contains__(self, identifier: str) -> bool:
        return self.get(identifier) is not None
    
    def __iter__(self):
        return iter(self.list_agents())
