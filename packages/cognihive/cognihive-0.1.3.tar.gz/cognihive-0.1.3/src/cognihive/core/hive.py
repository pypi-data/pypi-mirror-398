"""
CogniHive: The Main Hive Orchestrator.

The Hive is the central coordinator for multi-agent transactive memory.
It brings together agents, memory storage, expertise tracking, and query routing.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import uuid

from cognihive.core.agent_registry import AgentRegistry, Agent
from cognihive.core.memory_types import (
    Memory,
    MemoryVisibility,
    AccessPolicy,
    ExpertiseProfile,
    RoutingDecision,
)
from cognihive.storage.base import BaseStorage
from cognihive.storage.chroma import ChromaStorage
from cognihive.transactive.expertise_index import ExpertiseIndex
from cognihive.transactive.expertise_router import ExpertiseRouter


class Hive:
    """The CogniHive Orchestrator - Collective Intelligence for Agent Teams.
    
    The Hive provides:
    - Agent registration and management
    - Memory storage with access control
    - "Who Knows What" queries (Transactive Memory)
    - Automatic query routing to experts
    - Conflict detection and resolution
    
    Basic Usage:
        >>> from cognihive import Hive
        >>> 
        >>> hive = Hive()
        >>> hive.register_agent("coder", expertise=["python", "javascript"])
        >>> hive.register_agent("analyst", expertise=["sql", "data"])
        >>> 
        >>> hive.remember("Use connection pooling for DB performance", agent="coder")
        >>> 
        >>> # Who knows about databases?
        >>> experts = hive.who_knows("database optimization")
        >>> # Returns: [("analyst", 0.87), ("coder", 0.45)]
        >>> 
        >>> # Auto-route query to best expert
        >>> result = hive.ask("How do I optimize my queries?")
    """
    
    def __init__(
        self,
        name: str = "default",
        storage: Optional[BaseStorage] = None,
        persist_directory: Optional[str] = None,
        embedding_model: Optional[Any] = None
    ):
        """Initialize a new Hive.
        
        Args:
            name: Name of this hive (used for storage namespace)
            storage: Optional custom storage backend (default: ChromaDB)
            persist_directory: Path for persistent storage (None = in-memory)
            embedding_model: Optional custom embedding model
        """
        self.name = name
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        
        # Initialize storage
        if storage:
            self._storage = storage
        else:
            self._storage = ChromaStorage(
                collection_name=f"cognihive_{name}",
                persist_directory=persist_directory
            )
        self._storage.initialize()
        
        # Initialize agent registry
        self._agent_registry = AgentRegistry()
        
        # Initialize transactive memory components
        self._expertise_index = ExpertiseIndex(embedding_model=embedding_model)
        self._expertise_router = ExpertiseRouter(
            expertise_index=self._expertise_index
        )
        
        # Metrics
        self._metrics = {
            "memories_created": 0,
            "queries_processed": 0,
            "routing_decisions": 0,
        }
    
    # =========================================================================
    # Agent Management
    # =========================================================================
    
    def register_agent(
        self,
        name: str,
        expertise: Optional[List[str]] = None,
        role: str = "",
        description: str = "",
        **kwargs
    ) -> Agent:
        """Register a new agent in the hive.
        
        Args:
            name: Unique name for the agent
            expertise: List of expertise domains (e.g., ["python", "sql"])
            role: Agent's role (e.g., "coder", "analyst")
            description: Description of the agent
            **kwargs: Additional metadata
            
        Returns:
            The registered Agent
            
        Example:
            >>> hive.register_agent(
            ...     "coder",
            ...     expertise=["python", "javascript", "testing"],
            ...     role="Software Engineer"
            ... )
        """
        agent = self._agent_registry.register(
            name=name,
            expertise=expertise,
            role=role,
            description=description,
            metadata=kwargs
        )
        
        # Register in expertise index with initial expertise
        initial_expertise = {d.lower(): 0.7 for d in (expertise or [])}
        self._expertise_index.register_agent(
            agent_id=agent.id,
            agent_name=name,
            initial_expertise=initial_expertise
        )
        
        return agent
    
    def get_agent(self, identifier: str) -> Optional[Agent]:
        """Get an agent by name or ID."""
        return self._agent_registry.get(identifier)
    
    def list_agents(self) -> List[Agent]:
        """List all registered agents."""
        return self._agent_registry.list_agents()
    
    @property
    def agents(self) -> List[str]:
        """Get list of agent names."""
        return self._agent_registry.list_agent_names()
    
    # =========================================================================
    # Memory Operations
    # =========================================================================
    
    def remember(
        self,
        content: str,
        agent: Optional[str] = None,
        topics: Optional[List[str]] = None,
        visibility: str = "team",
        confidence: float = 1.0,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """Store a new memory in the hive.
        
        Args:
            content: The memory content (text)
            agent: Name or ID of the agent creating this memory
            topics: List of topics this memory relates to
            visibility: "private", "shared", "team", or "public"
            confidence: 0-1 confidence score
            importance: 0-1 importance score
            metadata: Additional metadata
            
        Returns:
            The created Memory object
            
        Example:
            >>> hive.remember(
            ...     "The API rate limit is 1000 requests per minute",
            ...     agent="docs",
            ...     topics=["api", "limits"]
            ... )
        """
        agent_obj = None
        agent_id = ""
        agent_name = ""
        
        if agent:
            agent_obj = self._agent_registry.get(agent)
            if agent_obj:
                agent_id = agent_obj.id
                agent_name = agent_obj.name
                agent_obj.memory_count += 1
            else:
                agent_id = agent
                agent_name = agent
        
        # Create memory
        memory = Memory(
            content=content,
            owner_id=agent_id,
            owner_name=agent_name,
            topics=topics or [],
            confidence=confidence,
            importance=importance,
            metadata=metadata or {}
        )
        
        # Set visibility
        try:
            memory.access_policy.visibility = MemoryVisibility(visibility)
        except ValueError:
            memory.access_policy.visibility = MemoryVisibility.TEAM
        
        # Store in backend
        self._storage.store_memory(memory)
        
        # Index expertise
        if agent_id:
            self._expertise_index.index_expertise(
                agent_id=agent_id,
                memory_content=content,
                topics=topics or [],
                confidence=confidence
            )
        
        self._metrics["memories_created"] += 1
        
        return memory
    
    def recall(
        self,
        query: str,
        agent: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Tuple[Memory, float]]:
        """Recall memories similar to a query.
        
        Args:
            query: The query text
            agent: Optional agent name/ID to filter by
            top_k: Number of results to return
            min_similarity: Minimum similarity score to include
            
        Returns:
            List of (Memory, similarity_score) tuples
            
        Example:
            >>> results = hive.recall("database optimization")
            >>> for memory, score in results:
            ...     print(f"{memory.content} (score: {score:.2f})")
        """
        filters = {}
        if agent:
            agent_obj = self._agent_registry.get(agent)
            if agent_obj:
                filters["owner_id"] = agent_obj.id
            else:
                filters["owner_id"] = agent
        
        # Query by text (let ChromaDB handle embedding)
        results = self._storage.query_by_text(
            query_text=query,
            top_k=top_k,
            filters=filters if filters else None
        )
        
        # Filter by minimum similarity
        results = [(m, s) for m, s in results if s >= min_similarity]
        
        self._metrics["queries_processed"] += 1
        
        return results
    
    def recall_by_topic(
        self,
        topic: str,
        limit: int = 20
    ) -> List[Memory]:
        """Recall memories by topic.
        
        Args:
            topic: Topic to filter by
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        return self._storage.query_by_metadata(
            filters={"topics": {"$contains": topic.lower()}},
            limit=limit
        )
    
    # =========================================================================
    # Transactive Memory - "Who Knows What"
    # =========================================================================
    
    def who_knows(
        self,
        topic: str,
        min_score: float = 0.3
    ) -> List[Tuple[str, float]]:
        """Find agents who know about a topic.
        
        THE KEY INNOVATION: Transactive Memory queries.
        
        Args:
            topic: The topic to find experts for
            min_score: Minimum expertise score to include
            
        Returns:
            List of (agent_name, score) tuples, sorted by expertise
            
        Example:
            >>> experts = hive.who_knows("python optimization")
            >>> for name, score in experts:
            ...     print(f"{name}: {score:.2f}")
            # Output:
            # coder: 0.92
            # analyst: 0.34
        """
        return self._expertise_index.who_knows(topic)
    
    def get_expert(self, topic: str) -> Optional[str]:
        """Get the single best expert for a topic.
        
        Args:
            topic: The topic to find an expert for
            
        Returns:
            Agent name of the best expert, or None if no expert found
            
        Example:
            >>> expert = hive.get_expert("machine learning")
            >>> print(f"The ML expert is: {expert}")
        """
        experts = self.who_knows(topic)
        return experts[0][0] if experts else None
    
    def expertise_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get the full expertise matrix for all agents.
        
        Returns:
            Dict of {agent_name: {domain: score, ...}, ...}
        """
        raw_matrix = self._expertise_index.export_expertise_matrix()
        
        # Convert agent IDs to names
        result = {}
        for agent_id, domains in raw_matrix.items():
            agent = self._agent_registry.get_by_id(agent_id)
            name = agent.name if agent else agent_id
            result[name] = domains
        
        return result
    
    # =========================================================================
    # Query Routing
    # =========================================================================
    
    def ask(
        self,
        query: str,
        route_to_expert: bool = True
    ) -> Dict[str, Any]:
        """Ask a question and get routed to the best expert.
        
        This combines routing + memory recall.
        
        Args:
            query: The question to ask
            route_to_expert: Whether to route to an expert
            
        Returns:
            Dict with routing decision and relevant memories
            
        Example:
            >>> result = hive.ask("How do I optimize my SQL queries?")
            >>> print(f"Best expert: {result['expert']}")
            >>> for memory in result['memories']:
            ...     print(f"- {memory.content}")
        """
        self._metrics["routing_decisions"] += 1
        
        # Get routing decision
        if route_to_expert:
            decision = self._expertise_router.route(query)
        else:
            decision = RoutingDecision(
                primary_agent="",
                primary_confidence=0.0,
                query=query
            )
        
        # Get relevant memories
        memories = self.recall(query, agent=decision.primary_agent if decision.primary_agent else None)
        
        # Get expert name
        expert_name = ""
        if decision.primary_agent:
            agent = self._agent_registry.get_by_id(decision.primary_agent)
            expert_name = agent.name if agent else decision.primary_agent
        
        return {
            "query": query,
            "expert": expert_name,
            "confidence": decision.primary_confidence,
            "memories": [m for m, _ in memories],
            "scores": [s for _, s in memories],
            "routing": decision,
            "secondary_experts": [
                self._agent_registry.get_by_id(aid).name if self._agent_registry.get_by_id(aid) else aid
                for aid in decision.secondary_agents
            ],
            "reasoning": decision.reasoning
        }
    
    def route(self, query: str) -> RoutingDecision:
        """Get a routing decision for a query without executing it.
        
        Args:
            query: The query to route
            
        Returns:
            RoutingDecision with expert recommendations
        """
        return self._expertise_router.route(query)
    
    # =========================================================================
    # Expertise Management
    # =========================================================================
    
    def get_expertise_profile(self, agent: str) -> Optional[ExpertiseProfile]:
        """Get an agent's expertise profile.
        
        Args:
            agent: Agent name or ID
            
        Returns:
            ExpertiseProfile or None if not found
        """
        agent_obj = self._agent_registry.get(agent)
        if agent_obj:
            return self._expertise_index.get_profile(agent_obj.id)
        return None
    
    def update_expertise(
        self,
        agent: str,
        domain: str,
        score: float
    ) -> bool:
        """Manually update an agent's expertise score.
        
        Args:
            agent: Agent name or ID
            domain: Expertise domain
            score: New score (0-1)
            
        Returns:
            True if update was successful
        """
        agent_obj = self._agent_registry.get(agent)
        if not agent_obj:
            return False
        
        profile = self._expertise_index.get_profile(agent_obj.id)
        if profile:
            profile.expertise_domains[domain.lower()] = max(0.0, min(1.0, score))
            return True
        return False
    
    def reinforce_expertise(
        self,
        agent: str,
        topic: str,
        success: bool
    ):
        """Reinforce or diminish expertise based on outcome.
        
        Call this after an agent handles a query to improve future routing.
        
        Args:
            agent: Agent name or ID
            topic: Topic of the interaction
            success: Whether the interaction was successful
        """
        agent_obj = self._agent_registry.get(agent)
        if agent_obj:
            self._expertise_index.learn_from_outcome(
                agent_id=agent_obj.id,
                topic=topic,
                success=success
            )
    
    # =========================================================================
    # Statistics and Utilities
    # =========================================================================
    
    def stats(self) -> Dict[str, Any]:
        """Get hive statistics.
        
        Returns:
            Dictionary with hive metrics and stats
        """
        return {
            "name": self.name,
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "agent_count": len(self._agent_registry),
            "memory_count": self._storage.count(),
            "metrics": self._metrics,
            "routing_stats": self._expertise_router.get_routing_stats()
        }
    
    def summary(self) -> str:
        """Get a human-readable summary of the hive.
        
        Returns:
            Formatted string summary
        """
        stats = self.stats()
        agents = self.agents
        
        lines = [
            f"🐝 CogniHive: {self.name}",
            "━" * 40,
            f"Agents: {stats['agent_count']}",
            f"Memories: {stats['memory_count']}",
            f"Queries: {stats['metrics']['queries_processed']}",
            "",
            "Registered Agents:",
        ]
        
        for agent_name in agents:
            profile = self.get_expertise_profile(agent_name)
            if profile:
                top_domains = profile.get_top_domains(3)
                domains_str = ", ".join([f"{d}({s:.1f})" for d, s in top_domains])
                lines.append(f"  • {agent_name}: {domains_str}")
            else:
                lines.append(f"  • {agent_name}")
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear all memories from the hive."""
        self._storage.clear()
    
    def __repr__(self) -> str:
        return f"Hive(name='{self.name}', agents={len(self._agent_registry)}, memories={self._storage.count()})"
