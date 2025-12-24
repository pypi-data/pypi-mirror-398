"""
Core memory types and dataclasses for CogniHive.

This module defines the fundamental data structures used throughout the system:
- Memory: The basic unit of knowledge storage
- ExpertiseProfile: Tracks what each agent knows
- TopicExpertise: Detailed expertise on specific topics
- RoutingDecision: Results of query routing to experts
- AccessPolicy: Fine-grained access control
- Conflict/Resolution: Memory conflict handling
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from enum import Enum
import uuid


class MemoryVisibility(str, Enum):
    """Memory visibility levels."""
    PRIVATE = "private"      # Only the owner can see
    SHARED = "shared"        # Specific agents can see
    TEAM = "team"            # All agents in the hive can see
    PUBLIC = "public"        # Everyone can see


class ConflictType(str, Enum):
    """Types of memory conflicts."""
    CONTRADICTION = "contradiction"      # Direct factual contradiction
    OUTDATED = "outdated"               # One memory is stale
    PARTIAL = "partial"                 # Partial overlap with differences
    AMBIGUOUS = "ambiguous"             # Unclear if truly conflicting


class ResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts."""
    RECENCY = "recency"                 # Prefer newer information
    CONFIDENCE = "confidence"           # Prefer higher confidence
    SOURCE = "source"                   # Prefer authoritative sources
    CONSENSUS = "consensus"             # Majority vote among agents
    HUMAN = "human"                     # Escalate to human


@dataclass
class AccessPolicy:
    """Fine-grained access control for memories.
    
    Defines who can read, write, and share a memory.
    """
    visibility: MemoryVisibility = MemoryVisibility.TEAM
    
    # Specific agent permissions (agent_ids)
    can_read: List[str] = field(default_factory=list)
    can_write: List[str] = field(default_factory=list)
    can_share: List[str] = field(default_factory=list)
    
    # Conditional access
    expires_at: Optional[datetime] = None
    requires_audit: bool = False
    redact_fields: List[str] = field(default_factory=list)
    
    # Provenance
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def allows(self, agent_id: str, operation: Literal["read", "write", "share"]) -> bool:
        """Check if an agent can perform an operation."""
        # Check expiration
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        
        # Public visibility allows all reads
        if self.visibility == MemoryVisibility.PUBLIC and operation == "read":
            return True
        
        # Team visibility allows team reads
        if self.visibility == MemoryVisibility.TEAM and operation == "read":
            return True
        
        # Check specific permissions
        permission_list = getattr(self, f"can_{operation}", [])
        return agent_id in permission_list or "*" in permission_list


@dataclass
class MemoryProvenance:
    """Tracks the origin and history of a memory."""
    source_agent: str
    created_at: datetime = field(default_factory=datetime.now)
    last_modified_at: datetime = field(default_factory=datetime.now)
    last_modified_by: str = ""
    
    # Lineage tracking
    derived_from: List[str] = field(default_factory=list)  # Memory IDs
    confidence_source: str = ""  # How confidence was determined
    
    # Validation
    validated_by: List[str] = field(default_factory=list)  # Agent IDs
    validation_count: int = 0
    
    # Citation tracking
    cited_by: List[str] = field(default_factory=list)  # Memory IDs that reference this


@dataclass
class Memory:
    """The fundamental unit of knowledge in CogniHive.
    
    A Memory represents a piece of information stored by an agent,
    with full provenance, access control, and metadata.
    """
    # Core content
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    
    # Ownership
    owner_id: str = ""
    owner_name: str = ""
    
    # Semantic indexing
    embedding: Optional[List[float]] = None
    topics: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Confidence and scoring
    confidence: float = 1.0  # 0-1 self-assessed
    importance: float = 0.5  # 0-1 importance score
    
    # Access control
    access_policy: AccessPolicy = field(default_factory=AccessPolicy)
    
    # Provenance
    provenance: MemoryProvenance = field(default_factory=lambda: MemoryProvenance(source_agent=""))
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # State
    is_active: bool = True
    superseded_by: Optional[str] = None  # Memory ID if this was replaced
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for storage."""
        return {
            "id": self.id,
            "content": self.content,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "topics": self.topics,
            "keywords": self.keywords,
            "confidence": self.confidence,
            "importance": self.importance,
            "visibility": self.access_policy.visibility.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Create memory from dictionary."""
        memory = cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            owner_id=data.get("owner_id", ""),
            owner_name=data.get("owner_name", ""),
            topics=data.get("topics", []),
            keywords=data.get("keywords", []),
            confidence=data.get("confidence", 1.0),
            importance=data.get("importance", 0.5),
            is_active=data.get("is_active", True),
            metadata=data.get("metadata", {}),
        )
        
        if "created_at" in data and isinstance(data["created_at"], str):
            memory.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            memory.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "visibility" in data:
            memory.access_policy.visibility = MemoryVisibility(data["visibility"])
        
        return memory


@dataclass
class TopicExpertise:
    """Detailed expertise on a specific topic."""
    topic: str
    confidence: float = 0.5           # 0-1 self-assessed confidence
    validated_confidence: float = 0.0  # 0-1 externally validated
    memory_count: int = 0             # How many memories on this topic
    
    # Temporal tracking
    first_learned: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Evidence
    sample_memory_ids: List[str] = field(default_factory=list)
    
    @property
    def effective_confidence(self) -> float:
        """Get the effective confidence, blending self and validated."""
        if self.validated_confidence > 0:
            # Weight validated confidence higher
            return 0.3 * self.confidence + 0.7 * self.validated_confidence
        return self.confidence


@dataclass
class ExpertiseProfile:
    """What an agent knows and how well they know it.
    
    This is the heart of Transactive Memory — tracking "who knows what".
    """
    agent_id: str
    agent_name: str
    
    # Domain expertise (learned automatically)
    # Maps domain name to confidence score (0-1)
    expertise_domains: Dict[str, float] = field(default_factory=dict)
    
    # Topic-level knowledge (more granular)
    topics: Dict[str, TopicExpertise] = field(default_factory=dict)
    
    # Learning trajectory
    expertise_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Reliability metrics
    accuracy_score: float = 0.5       # How often this agent's memories are correct
    citation_count: int = 0           # How often other agents reference this agent
    
    # Activity tracking
    last_active: datetime = field(default_factory=datetime.now)
    total_memories: int = 0
    
    def get_domain_score(self, domain: str) -> float:
        """Get expertise score for a domain."""
        return self.expertise_domains.get(domain.lower(), 0.0)
    
    def update_expertise(self, domain: str, score_delta: float):
        """Update expertise score for a domain."""
        domain = domain.lower()
        current = self.expertise_domains.get(domain, 0.0)
        # Clamp between 0 and 1
        new_score = max(0.0, min(1.0, current + score_delta))
        self.expertise_domains[domain] = new_score
        
        # Record in history
        self.expertise_history.append({
            "domain": domain,
            "from": current,
            "to": new_score,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_topic_expertise(self, topic: str, confidence: float = 0.5):
        """Add or update topic expertise."""
        topic = topic.lower()
        if topic in self.topics:
            self.topics[topic].confidence = confidence
            self.topics[topic].last_updated = datetime.now()
            self.topics[topic].memory_count += 1
        else:
            self.topics[topic] = TopicExpertise(
                topic=topic,
                confidence=confidence,
                memory_count=1
            )
    
    def get_top_domains(self, n: int = 5) -> List[tuple]:
        """Get the top N domains by expertise score."""
        sorted_domains = sorted(
            self.expertise_domains.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_domains[:n]


@dataclass
class RoutingDecision:
    """Result of routing a query to expert agents.
    
    Contains the routing decision with explanations.
    """
    # Primary routing
    primary_agent: str
    primary_confidence: float
    
    # Secondary experts (backup/collaboration)
    secondary_agents: List[str] = field(default_factory=list)
    secondary_confidences: List[float] = field(default_factory=list)
    
    # Explanation
    reasoning: str = ""
    matched_domains: List[str] = field(default_factory=list)
    matched_topics: List[str] = field(default_factory=list)
    
    # Metadata
    query: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "primary_agent": self.primary_agent,
            "primary_confidence": self.primary_confidence,
            "secondary_agents": self.secondary_agents,
            "reasoning": self.reasoning,
            "matched_domains": self.matched_domains,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Conflict:
    """A conflict between two memories."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    memory_a_id: str = ""
    memory_b_id: str = ""
    memory_a_content: str = ""
    memory_b_content: str = ""
    
    conflict_type: ConflictType = ConflictType.CONTRADICTION
    severity: float = 0.5  # 0-1, how severe the conflict is
    
    # Detection metadata
    detected_at: datetime = field(default_factory=datetime.now)
    detection_method: str = ""
    
    # Context
    topic: str = ""
    agents_involved: List[str] = field(default_factory=list)


@dataclass
class Resolution:
    """Resolution of a memory conflict."""
    conflict_id: str
    
    # Outcome
    winning_memory_id: Optional[str] = None
    losing_memory_id: Optional[str] = None
    
    # Strategy used
    strategy: ResolutionStrategy = ResolutionStrategy.RECENCY
    
    # Status
    is_resolved: bool = False
    needs_human_review: bool = False
    
    # Explanation
    reasoning: str = ""
    confidence: float = 0.5
    
    # Metadata
    resolved_at: datetime = field(default_factory=datetime.now)
    resolved_by: str = ""  # "system" or agent_id or "human"
